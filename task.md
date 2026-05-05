# Apollo 150 Tools Router 复现计划

## 项目定位

复现并工程化实现一个面向 150 个工具的两阶段 Tool Router：给定用户自然语言输入，从大规模工具集合中选择最合适的工具，并抽取所需参数。

本项目不强调算法创新，重点是完整复现、工程化落地和可评测验证。

## 核心目标

- 将当前 11 个工具扩展到 150 个工具。
- 使用 YAML schema 统一管理工具定义，包括工具名称、描述、别名、示例和参数约束。
- 基于 embedding 语义召回 + LLM 仲裁的两阶段架构完成工具选择。
- 构建中文自然语言评测集，覆盖标准表达、口语表达、模糊表达、缺参表达和非指令输入。
- 使用 Tool Accuracy、Top-K Recall、Slot F1 等指标评估路由效果。
- 保留 CLI、FastAPI、Docker、embedding 缓存和 dry-run 本地烟测能力。

## 技术路线

```text
用户 query
  -> BGE embedding 语义召回 Top-K tools
  -> LLM 仅在 Top-K 候选工具中仲裁
  -> 输出结构化 JSON
```

输出字段：

```json
{
  "is_instruction": true,
  "tool_code": "...",
  "intent": "...",
  "arguments": {},
  "missing_required_arguments": [],
  "confidence": 0.0,
  "reason": "..."
}
```

## 工具集扩展

将 `configs/tools.yaml` 扩展到 150 个工具，建议按领域组织：

- 系统工具：文件、剪贴板、搜索、窗口、通知、设置等。
- 办公工具：邮件、日历、会议、文档、表格、幻灯片、审批、待办等。
- 通讯工具：短信、联系人、电话、群聊、消息搜索等。
- 生活服务：天气、导航、打车、外卖、酒店、机票、火车票、快递等。
- 多媒体：音乐、视频、相册、录音、播客、有声书等。
- 智能家居：灯、空调、窗帘、电视、扫地机、摄像头、门锁等。
- 开发工具：代码搜索、运行测试、创建 issue、查询 PR、部署、日志检索等。
- 知识工具：翻译、摘要、问答、百科、计算、单位换算等。

每个工具至少包含：

- `code`
- `name`
- `description`
- `aliases`
- `examples`
- `arguments`

每个工具建议提供 3-5 条 examples。

## 数据集构建

构建 `data/generated_queries.jsonl`，每行一个样本：

```json
{"query": "用户自然语言输入", "tool_code": "目标工具 code", "arguments": {}}
```

每个工具建议至少 5 条样本：

- 标准表达：清晰完整，必填参数齐全。
- 口语表达：更短、更自然、更像真实用户。
- 模糊表达：需要根据语义判断目标工具。
- 缺参表达：缺少必填参数，用于测试 `missing_required_arguments`。
- 干扰表达：相近工具、非指令或问答类输入。

目标规模：

- 150 个工具。
- 每个工具至少 5 条 query。
- 总样本数不少于 750 条。
- 额外加入 100 条 `none` 非指令样本。

## 评测指标

实现或完善评测脚本，至少输出：

- `Top-1 Accuracy`：最终工具选择准确率。
- `Top-K Recall`：正确工具是否进入 embedding 召回候选。
- `Slot Precision`：抽取参数准确率。
- `Slot Recall`：应抽参数召回率。
- `Slot F1`：参数抽取综合指标。
- `None Accuracy`：非指令输入识别准确率。

建议评测不同 K 值：

- Top-3
- Top-5
- Top-8
- Top-10

## Baseline 对比

至少实现以下 baseline：

- 关键词匹配：基于工具名称、别名、示例做简单匹配。
- Embedding only：直接选择 embedding 分数最高的工具。
- LLM full prompt：将全部工具放入 prompt，让 LLM 直接选择。
- Apollo two-stage：embedding Top-K + LLM 仲裁。

对比维度：

- 工具选择准确率。
- Top-K Recall。
- Slot F1。
- Prompt token 数量。
- 平均延迟。
- 估算调用成本。

## 工程化要求

保留并完善现有能力：

- CLI：
  - `router route "query"`
  - `router precompute`
  - `router --show-candidates`
- REST API：
  - `GET /health`
  - `POST /route`
- Docker demo：
  - demo 模式使用 hash embedding + dry-run LLM。
  - prod 模式使用 BGE embedding + OpenAI-compatible LLM。
- Embedding 缓存：
  - 根据 `tools.yaml` 内容 hash 自动失效。
  - 支持预计算工具向量，避免重复启动成本。
- 测试：
  - 单元测试覆盖路由、召回、缺参、none 兜底和缓存逻辑。

## 阶段任务

### 阶段一：工具集扩展

- 扩展 `configs/tools.yaml` 到 150 个工具。
- 确保每个工具有清晰描述、别名、示例和参数定义。
- 避免工具 code 冲突。
- 保持工具命名风格一致。

### 阶段二：数据集扩展

- 扩展 `data/generated_queries.jsonl` 到不少于 850 条。
- 覆盖 150 个工具和 `none` 类别。
- 保证 arguments 只包含 query 中可抽取的信息。
- 缺参样本不要填充不存在的参数。

### 阶段三：评测能力增强

- 增加 Top-K Recall 评测。
- 增加 None Accuracy 评测。
- 增加按工具类别统计结果。
- 输出 JSON 格式评测报告，便于后续对比。

### 阶段四：Baseline 实现

- 实现关键词 baseline。
- 实现 embedding only baseline。
- 实现 LLM full prompt baseline。
- 对比 Apollo two-stage 的效果、成本和延迟。

### 阶段五：文档与简历材料

- 更新 README，说明项目定位为 150 tools router 复现。
- 补充架构图、运行方式、评测方式和实验结果。
- 整理简历描述，强调复现、工程化、评测闭环和大工具集路由能力。

## 验收标准

- `configs/tools.yaml` 中工具数量达到 150 个。
- `data/generated_queries.jsonl` 样本数不少于 850 条。
- `python -m pytest tests/ -v` 通过。
- `python -m apollo.evaluate --embedding hash --llm dry-run data/generated_queries.jsonl` 能正常输出指标。
- REST API 能通过 `/route` 返回合法结构化 JSON。
- Docker demo 能在无 API key 情况下启动并完成一次路由请求。
- README 包含项目定位、架构、运行方式、评测方式和实验结果。

## 简历表述方向

项目名称：

Apollo：150 工具规模中文 Tool Router 复现项目

简历描述：

- 复现并工程化实现面向 150 个工具的两阶段工具路由系统，基于 BGE embedding 进行语义召回，并由 LLM 在 Top-K 候选工具中完成最终仲裁和参数抽取。
- 构建配置化工具 schema 和中文自然语言评测集，覆盖标准表达、口语表达、模糊表达、缺参表达和非指令输入。
- 设计 Tool Accuracy、Top-K Recall、Slot F1、None Accuracy 等评测指标，并对比关键词匹配、embedding only、LLM full prompt 和 two-stage router 等方案。
- 封装 CLI、FastAPI、Docker demo、embedding 预计算缓存和 dry-run 本地烟测能力，形成可运行、可评测、可部署的完整工程闭环。
