# Apollo

[English](README.md) | [中文](README.zh-CN.md)

Apollo 是一个面向 150 个工具的中文 Tool Router 复现项目。项目实现了工程化的两阶段路由流程：第一阶段使用 embedding 从大规模工具集合中召回 Top-K 候选工具，第二阶段让 LLM 只在候选集合中完成工具仲裁和参数抽取。

本项目关注可复现、可评测和可部署，不执行真实工具。

## 项目亮点

- 使用统一 YAML schema 管理 150 个工具。
- 构建 850 条中文自然语言评测样本。
- 实现 embedding 语义召回 + LLM 仲裁的两阶段路由。
- 提供 hash embedding + dry-run 仲裁器的本地离线 demo，无需 API key。
- 评测指标覆盖 Top-1 Accuracy、Top-K Recall、Slot Precision / Recall / F1、None Accuracy 和按类别统计。
- 对比 keyword、embedding only、LLM full prompt 和 Apollo two-stage 四类方案。
- 保留 CLI、FastAPI REST API、Docker demo 和 embedding 缓存能力。

## 架构

```text
用户 query
  -> BGE / hash embedding 语义召回
  -> Top-K 候选工具
  -> LLM / dry-run 仲裁器在候选中选择工具
  -> 结构化 JSON 路由结果
```

输出格式：

```json
{
  "is_instruction": true,
  "tool_code": "message.send",
  "intent": "发送消息",
  "arguments": {
    "recipient": "张三",
    "content": "我晚点到"
  },
  "missing_required_arguments": [],
  "confidence": 0.99,
  "reason": "dry-run 本地仲裁"
}
```

## 目录结构

```text
apollo/
  cache.py          # embedding 缓存读写
  cli.py            # 命令行入口
  config.py         # YAML 工具 schema 加载
  embedding.py      # BGE 和 hash embedding 模型
  evaluate.py       # 评测和 baseline 对比
  llm.py            # OpenAI-compatible client 与 dry-run 仲裁器
  prompt.py         # 仲裁 prompt 构建
  retrieval.py      # Top-K 工具召回
  router.py         # 端到端路由器
  server.py         # FastAPI REST API
configs/
  tools.yaml        # 150 个工具定义
data/
  generated_queries.jsonl
scripts/
  generate_assets.py
tests/
  test_router.py
```

## 快速开始

安装项目：

```bash
python -m pip install -e .
```

运行离线烟测。该模式不需要下载 BGE 模型，也不需要 API key：

```bash
python -m apollo.cli route --embedding hash --llm dry-run "请帮我发送消息，收件人：张三，内容：我晚点到"
```

示例输出：

```json
{
  "is_instruction": true,
  "tool_code": "message.send",
  "intent": "发送消息",
  "arguments": {
    "recipient": "张三",
    "content": "我晚点到"
  },
  "missing_required_arguments": [],
  "confidence": 0.99,
  "reason": "dry-run 本地仲裁"
}
```

查看召回候选：

```bash
python -m apollo.cli route --embedding hash --llm dry-run --show-candidates "请帮我查询天气，地点：上海，日期：明天"
```

## 生产模式

生产模式使用 BGE embedding 和 OpenAI-compatible Chat Completions API。

```bash
set APOLLO_LLM_API_KEY=your_api_key
set APOLLO_LLM_MODEL=your_model
set APOLLO_LLM_BASE_URL=https://api.openai.com/v1

router route "请帮我创建日程，标题：周会安排，日期：明天，时间：明天下午三点"
```

预计算工具 embedding 缓存以降低启动成本：

```bash
router precompute
```

缓存文件位于 `data/tool_embeddings.json`。当 `configs/tools.yaml` 内容变化时，缓存会自动失效。

## 工具 Schema

工具定义存放在 `configs/tools.yaml`。每个工具包含：

- `code`
- `name`
- `category`
- `description`
- `aliases`
- `examples`
- `arguments`

当前 schema 共包含 150 个工具，覆盖系统工具、办公工具、通讯工具、生活服务、多媒体、智能家居、开发工具、知识工具和 `none` 兜底类。

`none` 工具用于表示闲聊、知识问答、解释说明、感谢等不需要调用工具的输入。

## 评测数据集

评测集位于 `data/generated_queries.jsonl`。

当前规模：

- 850 条总样本
- 覆盖 149 个可执行工具
- 105 条 `none` 样本
- 每个可执行工具至少 5 条样本

样本类型覆盖标准完整指令、口语表达、可路由的模糊表达、缺参表达和非指令干扰输入。

重新生成工具 schema 和评测数据：

```bash
python scripts/generate_assets.py
```

## 评测

运行离线评测：

```bash
python -m apollo.evaluate --embedding hash --llm dry-run data/generated_queries.jsonl
```

评测脚本会输出 Top-1 Accuracy、Top-K Recall、Slot Precision / Recall / F1、None Accuracy、按类别 accuracy、baseline 对比，以及 full-prompt baseline 的 token 和成本估算。

## 当前离线测评结果

以下结果来自 `hash` embedding + `dry-run` 仲裁器，在 850 条生成样本上的离线评测：

```text
样本数:             850
工具数:             150
None 样本数:        105

Top-1 Accuracy:     99.65%
Top-3 Recall:       100.00%
Top-5 Recall:       100.00%
Top-8 Recall:       100.00%
Top-10 Recall:      100.00%

Slot Precision:     100.00%
Slot Recall:        100.00%
Slot F1:            100.00%

None Accuracy:      97.14%
```

按类别 accuracy：

```text
系统工具:           100.00%
办公工具:           100.00%
通讯工具:           100.00%
生活服务:           100.00%
多媒体:             100.00%
智能家居:           100.00%
开发工具:           100.00%
知识工具:           100.00%
None 兜底:           97.14%
```

Baseline 对比：

```text
Keyword baseline
  Top-1 Accuracy:   99.18%
  None Accuracy:    93.33%
  Slot F1:          100.00%

Embedding only
  Top-1 Accuracy:   87.65%
  None Accuracy:     0.00%
  Slot F1:            0.00%

LLM full prompt
  Top-1 Accuracy:   99.65%
  None Accuracy:    97.14%
  Slot F1:          100.00%
  估算 prompt tokens: 14801
  估算成本:          $1.887 / 850 samples

Apollo two-stage
  Top-1 Accuracy:   99.65%
  None Accuracy:    97.14%
  Slot F1:          100.00%
```

这些离线指标用于确定性的工程 smoke test 和 baseline 对比。真实 BGE + 真实 LLM 的效果可以通过同一条评测命令切换到 `--embedding bge --llm openai` 后重新测量。

## REST API

安装服务端依赖：

```bash
python -m pip install -e ".[serve]"
```

启动 demo API：

```bash
set APOLLO_EMBEDDING=hash
set APOLLO_LLM_MODE=dry-run
uvicorn apollo.server:app --reload
```

接口：

| 方法 | 路径 | 说明 |
| --- | --- | --- |
| GET | `/health` | 健康检查 |
| POST | `/route` | 路由 query 并返回结构化 JSON |

请求示例：

```bash
curl -s -X POST http://localhost:8000/route ^
  -H "Content-Type: application/json" ^
  -d "{\"query\":\"请帮我发送消息，收件人：张三，内容：我晚点到\"}"
```

## Docker Demo

运行无需 API key 的本地 demo：

```bash
docker-compose --profile demo up --build
```

运行生产模式：

```bash
copy .env.example .env
docker-compose --profile prod up --build
```

demo 模式使用 hash embedding 和 dry-run 仲裁；生产模式使用 BGE embedding 和 OpenAI-compatible LLM。

## 测试

```bash
python -m pytest tests/ -v
```

当前结果：

```text
5 passed
```

## 简历描述

Apollo 是一个 150 工具规模的中文 Tool Router 复现项目。项目实现 embedding Top-K 召回 + LLM 仲裁的两阶段工具路由流程，构建 YAML 管理的工具 schema 和 850 条中文评测集，评测 Top-K Recall、Tool Accuracy、Slot F1、None Accuracy 等指标，并对比 keyword、embedding only、LLM full prompt 和 two-stage 方案；同时封装 CLI、FastAPI、Docker demo、embedding 缓存和 dry-run 本地烟测，形成可运行、可评测、可部署的完整工程闭环。
