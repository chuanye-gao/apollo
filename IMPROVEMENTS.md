# Apollo 改进规格文档

> 本文档供 AI 执行者阅读。请严格按照规格实现，不要自行增加额外抽象、框架或依赖。

---

## 背景

Apollo 是一个两阶段工具路由系统：embedding 语义召回（Top-K）→ LLM 仲裁 → 结构化输出。核心逻辑已完成，本次改进补全四个缺失部分：

1. 样例数据扩充
2. Embedding 预计算缓存
3. REST API 服务端
4. Docker 一键演示

**禁止引入 LangChain、LangGraph 或任何重量级框架。** 保持项目风格：标准库优先，依赖最小化。

---

## 当前文件树

```
apollo/
├── apollo/
│   ├── __init__.py
│   ├── cli.py          # CLI 入口，router "query"
│   ├── config.py       # Tool dataclass + load_tools()
│   ├── embedding.py    # BGEEmbeddingModel, HashEmbeddingModel
│   ├── evaluate.py     # 评测脚本
│   ├── llm.py          # OpenAICompatibleClient, DryRunClient
│   ├── prompt.py       # build_prompt()
│   ├── retrieval.py    # ToolRetriever, Candidate, TOP_K=8
│   └── router.py       # Router, RouteResult
├── configs/
│   └── tools.yaml      # 11 个工具定义（含 none）
├── data/
│   └── generated_queries.jsonl   # 目前 22 条，需扩充
├── tests/
│   ├── __init__.py
│   └── test_router.py
├── pyproject.toml
└── README.md
```

---

## 改动一：扩充样例数据

### 目标文件

`data/generated_queries.jsonl`

### 格式

每行一个 JSON 对象，字段如下：

```json
{"query": "用户自然语言输入", "tool_code": "对应工具code", "arguments": {"参数名": "参数值"}}
```

- `arguments` 只包含能从 query 中提取到的参数，**不要编造**
- 缺失必填参数时，`arguments` 中不写该字段（不写 `null`）

### 数量要求

| tool_code | 目标条数 |
|-----------|---------|
| alarm.create | 20 |
| message.send | 20 |
| calendar.create | 20 |
| weather.query | 20 |
| music.play | 20 |
| navigation.start | 20 |
| note.create | 20 |
| email.send | 20 |
| todo.create | 20 |
| contact.search | 20 |
| none | 20 |

总计约 **220 条**（现有 22 条可保留，补齐差额即可，去重）。

### 各工具参数定义（参照 configs/tools.yaml）

```
alarm.create:     time(required), date(optional)
message.send:     recipient(required), content(required)
calendar.create:  title(required), time(required), date(optional)
weather.query:    location(required), date(optional)
music.play:       query(required)
navigation.start: destination(required), origin(optional)
note.create:      content(required)
email.send:       recipient(required), subject(optional), content(required)
todo.create:      content(required), due_date(optional)
contact.search:   name(required)
none:             无参数（arguments 写 {}）
```

### 表达风格要求（每工具 20 条需覆盖）

- **正常表达**（5 条）：清晰完整，所有必填参数均在 query 中
- **口语/简短表达**（5 条）：如"帮我导航"、"放歌"、"记一下"
- **参数缺失**（5 条）：必填参数不在 query 中，`arguments` 不含该字段
- **模糊/间接表达**（5 条）：语义需推断，如"我要出门了"→ navigation.start

---

## 改动二：Embedding 预计算缓存

### 新增文件：`apollo/cache.py`

```python
"""离线预计算并缓存工具 embedding，避免每次启动重算。"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

# 缓存文件默认路径（与 tools.yaml 同目录）
DEFAULT_CACHE_PATH = Path(__file__).resolve().parent.parent / "data" / "tool_embeddings.json"


def compute_tools_hash(tools_path: Path) -> str:
    """根据 tools.yaml 内容生成哈希，用于判断缓存是否失效。"""
    content = tools_path.read_bytes()
    return hashlib.sha256(content).hexdigest()[:16]


def save_cache(
    vectors: list[list[float]],
    tool_codes: list[str],
    tools_hash: str,
    cache_path: Path = DEFAULT_CACHE_PATH,
) -> None:
    """将工具向量写入 JSON 缓存文件。"""
    data: dict[str, Any] = {
        "tools_hash": tools_hash,
        "tool_codes": tool_codes,
        "vectors": vectors,
    }
    cache_path.parent.mkdir(parents=True, exist_ok=True)
    cache_path.write_text(json.dumps(data), encoding="utf-8")


def load_cache(
    tools_hash: str,
    cache_path: Path = DEFAULT_CACHE_PATH,
) -> tuple[list[str], list[list[float]]] | None:
    """
    尝试加载缓存。

    返回 (tool_codes, vectors)，若缓存不存在或哈希不匹配则返回 None。
    """
    if not cache_path.exists():
        return None
    try:
        data = json.loads(cache_path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return None
    if data.get("tools_hash") != tools_hash:
        return None
    return data["tool_codes"], data["vectors"]
```

### 修改 `apollo/router.py`

在 `ToolRetriever.__init__` 调用之前，Router 尝试加载缓存。具体改法：

在 `Router.__init__` 中，当 `embedding_model` 是 `BGEEmbeddingModel` 时，尝试从缓存加载工具向量；若缓存命中，直接传给 `ToolRetriever` 跳过重算。

**接口约定**：`ToolRetriever` 需新增一个可选参数 `precomputed_vectors`：

```python
# retrieval.py
class ToolRetriever:
    def __init__(
        self,
        tools: list[Tool],
        embedding_model: EmbeddingModel,
        precomputed_vectors: list[list[float]] | None = None,  # 新增
    ) -> None:
        self.tools = tools
        self.embedding_model = embedding_model
        if precomputed_vectors is not None:
            self.tool_vectors = precomputed_vectors
        else:
            self.tool_vectors = embedding_model.encode([tool.embedding_text() for tool in tools])
```

`Router.__init__` 中加载缓存逻辑（仅对 BGEEmbeddingModel 生效）：

```python
# router.py，在构造 ToolRetriever 之前
from apollo.cache import compute_tools_hash, load_cache, DEFAULT_CACHE_PATH
from apollo.config import default_tools_path
from apollo.embedding import BGEEmbeddingModel

precomputed: list[list[float]] | None = None
if isinstance(embedding_model or BGEEmbeddingModel(), BGEEmbeddingModel):
    tools_path = default_tools_path()
    h = compute_tools_hash(tools_path)
    cached = load_cache(h)
    if cached is not None:
        cached_codes, cached_vectors = cached
        if cached_codes == [t.code for t in self.tools]:
            precomputed = cached_vectors

self.retriever = ToolRetriever(self.tools, embedding_model or BGEEmbeddingModel(), precomputed)
```

### 修改 `apollo/cli.py`

新增 `precompute` 子命令（与现有 `router` 入口并列）：

```
用法：router precompute [--tools PATH] [--embedding bge|hash]
```

逻辑：
1. `load_tools(args.tools)`
2. 初始化 embedding model
3. `model.encode([tool.embedding_text() for tool in tools])`
4. `save_cache(vectors, [t.code for t in tools], compute_tools_hash(tools_path))`
5. 打印 `Cached {n} tool embeddings → {cache_path}`

实现方式：将 `cli.py` 的 `main()` 改为用 `subparsers`，原有 `router "query"` 逻辑挂在 `subparsers.add_parser("route")`（同时保持无子命令时的默认行为向后兼容，即若第一个参数不是子命令则走原逻辑）。

---

## 改动三：REST API

### 新增文件：`apollo/server.py`

```python
"""FastAPI REST 服务。启动：uvicorn apollo.server:app"""
from __future__ import annotations

import os
from typing import Any

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from apollo.router import Router

app = FastAPI(title="Apollo Tool Router", version="0.1.0")

# 全局单例 Router，启动时初始化
_router: Router | None = None


def _get_router() -> Router:
    global _router
    if _router is None:
        embedding = os.getenv("APOLLO_EMBEDDING", "bge")
        llm = os.getenv("APOLLO_LLM_MODE", "openai")
        _router = Router.for_modes(embedding=embedding, llm=llm)
    return _router


class RouteRequest(BaseModel):
    query: str


class RouteResponse(BaseModel):
    is_instruction: bool
    tool_code: str
    intent: str
    arguments: dict[str, Any]
    missing_required_arguments: list[str]
    confidence: float
    reason: str


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/route", response_model=RouteResponse)
def route(request: RouteRequest) -> RouteResponse:
    if not request.query.strip():
        raise HTTPException(status_code=400, detail="query must not be empty")
    result = _get_router().route(request.query)
    return RouteResponse(**result.to_dict())
```

**环境变量**：

| 变量 | 默认值 | 说明 |
|------|--------|------|
| `APOLLO_EMBEDDING` | `bge` | `bge` 或 `hash` |
| `APOLLO_LLM_MODE` | `openai` | `openai` 或 `dry-run` |
| `APOLLO_LLM_API_KEY` | — | LLM API key（openai 模式必填） |
| `APOLLO_LLM_MODEL` | — | 模型名（openai 模式必填） |
| `APOLLO_LLM_BASE_URL` | `https://api.openai.com/v1` | API 基础 URL |

### 修改 `pyproject.toml`

在 `[project]` 下增加可选依赖：

```toml
[project.optional-dependencies]
serve = [
  "fastapi>=0.110",
  "uvicorn[standard]>=0.29",
]
```

安装命令：`pip install -e ".[serve]"`

---

## 改动四：Docker 一键演示

### 新增文件：`Dockerfile`

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# 先复制依赖声明，利用 layer cache
COPY pyproject.toml ./
COPY apollo/__init__.py apollo/

# 安装基础依赖 + serve 组
RUN pip install --no-cache-dir -e ".[serve]"

# 复制全部源码
COPY . .

# 默认环境：dry-run 演示，无需 API key
ENV APOLLO_EMBEDDING=hash
ENV APOLLO_LLM_MODE=dry-run

EXPOSE 8000

# 默认启动 REST API
CMD ["uvicorn", "apollo.server:app", "--host", "0.0.0.0", "--port", "8000"]
```

### 新增文件：`docker-compose.yml`

```yaml
version: "3.9"

services:
  # ── demo 模式：hash embedding + dry-run LLM，无需任何配置 ──
  demo:
    build: .
    profiles: ["demo"]
    ports:
      - "8000:8000"
    environment:
      APOLLO_EMBEDDING: hash
      APOLLO_LLM_MODE: dry-run

  # ── prod 模式：BGE embedding + 真实 LLM，读取 .env 文件 ──
  prod:
    build: .
    profiles: ["prod"]
    ports:
      - "8000:8000"
    env_file:
      - .env
    environment:
      APOLLO_EMBEDDING: bge
      APOLLO_LLM_MODE: openai
```

启动方式：
- `docker-compose --profile demo up` — 零配置演示
- `docker-compose --profile prod up` — 生产模式（需要 `.env`）

### 新增文件：`.env.example`

```dotenv
# 复制为 .env 并填写真实值

# LLM 配置（prod 模式必填）
APOLLO_LLM_API_KEY=your_api_key_here
APOLLO_LLM_MODEL=gpt-4o-mini
APOLLO_LLM_BASE_URL=https://api.openai.com/v1

# Embedding 模式：bge（需下载模型）或 hash（本地烟测）
APOLLO_EMBEDDING=bge

# LLM 模式：openai 或 dry-run
APOLLO_LLM_MODE=openai
```

### 新增文件：`Makefile`

```makefile
.PHONY: demo prod precompute eval test

# 一键启动演示（无需 API key）
demo:
	docker-compose --profile demo up --build

# 一键启动生产服务（需要 .env）
prod:
	docker-compose --profile prod up --build

# 预计算工具 embedding（本地 BGE 模式）
precompute:
	python -m apollo.cli precompute --embedding bge

# 评测（dry-run 模式，无需 API key）
eval:
	python -m apollo.evaluate --embedding hash --llm dry-run data/generated_queries.jsonl

# 单元测试
test:
	python -m pytest tests/ -v
```

---

## 修改 README.md

在现有 README 末尾追加以下章节（不要删除原有内容）：

```markdown
## Docker 一键演示

无需 API key，使用本地 hash embedding + dry-run 仲裁：

​```bash
docker-compose --profile demo up --build
​```

然后：

​```bash
curl -s -X POST http://localhost:8000/route \
  -H "Content-Type: application/json" \
  -d '{"query": "给张三发消息说我晚点到"}' | python -m json.tool
​```

生产模式（BGE embedding + 真实 LLM）：

​```bash
cp .env.example .env   # 填入 API key
docker-compose --profile prod up --build
​```

## REST API

启动本地服务端（需先 `pip install -e ".[serve]"`）：

​```bash
uvicorn apollo.server:app --reload
​```

端点：

| 方法 | 路径 | 说明 |
|------|------|------|
| GET  | /health | 健康检查 |
| POST | /route  | 工具路由，body: `{"query": "..."}` |

## Embedding 预计算

首次使用 BGE embedding 建议预计算并缓存工具向量（约 1-2 秒），之后每次启动无需重算：

​```bash
router precompute
# 或
make precompute
​```

缓存存储在 `data/tool_embeddings.json`，`tools.yaml` 变更后自动失效。
```

---

## 执行顺序建议

1. **先扩充数据**（改动一）— 纯数据，无代码风险
2. **实现缓存**（改动二）— 修改 `retrieval.py` 和 `router.py`，改完跑 `python -m pytest tests/ -v` 确认无回归
3. **实现 REST API**（改动三）— 新增 `server.py`，改完用 `curl` 手动验证
4. **加 Docker**（改动四）— 最后，确保 demo 模式能跑通

---

## 验收标准

### 数据

```bash
wc -l data/generated_queries.jsonl
# 输出应 >= 200
```

### 缓存

```bash
python -m apollo.cli precompute --embedding hash
# 输出：Cached 11 tool embeddings → data/tool_embeddings.json
```

### REST API

```bash
pip install -e ".[serve]"
uvicorn apollo.server:app &
curl -s -X POST http://localhost:8000/route \
  -H "Content-Type: application/json" \
  -d '{"query": "明天下午三点提醒我开会"}' | python -m json.tool
# tool_code 应为 alarm.create
curl -s http://localhost:8000/health
# {"status": "ok"}
```

### Docker demo

```bash
docker-compose --profile demo up --build -d
curl -s -X POST http://localhost:8000/route \
  -H "Content-Type: application/json" \
  -d '{"query": "导航到上海虹桥火车站"}' | python -m json.tool
# tool_code 应为 navigation.start
docker-compose --profile demo down
```

### 单测不回归

```bash
python -m pytest tests/ -v
# 4 个测试全部 PASSED
```
