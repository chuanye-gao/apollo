# apollo

一个基于 embedding 语义召回 + LLM 仲裁的工具路由系统，用于 Function Calling / MCP 场景下的意图识别与参数抽取。

## 架构

```text
query
  -> embedding 语义召回（Top-K tools, K=8）
  -> LLM 仲裁（只在 Top-K 中选择）
  -> JSON 结构化输出
```

本项目只做 router，不执行真实工具，不引入 LangChain / LangGraph。

## 快速开始

安装依赖：

```bash
python -m pip install -e .
```

使用真实 BGE embedding 和 OpenAI-compatible LLM：

```bash
set APOLLO_LLM_API_KEY=你的_api_key
set APOLLO_LLM_MODEL=你的模型名
router "明天下午三点提醒我开会"
```

本地烟测模式（不需要下载 BGE、不需要 API key，仅用于验证流程）：

```bash
python -m apollo.cli --embedding hash --llm dry-run "给张三发消息说我晚点到"
```

输出示例：

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
  "confidence": 0.73,
  "reason": "dry-run 本地仲裁"
}
```

## 配置

工具定义在 `configs/tools.yaml`。每个工具包含：

- `code`
- `name`
- `description`
- `aliases`
- `examples`（每个工具 5 条手写样例）
- `arguments`

召回阶段会使用以下文本构建工具 embedding：

```text
name: {name}
description: {description}
aliases: {aliases}
examples: {examples}
```

## LLM 配置

默认使用 OpenAI-compatible Chat Completions API：

- `APOLLO_LLM_API_KEY`
- `APOLLO_LLM_MODEL`
- `APOLLO_LLM_BASE_URL`，默认 `https://api.openai.com/v1`

LLM prompt 只会包含召回得到的 Top-K 候选工具，且强制包含 `tool_code = "none"`。

## 评测

```bash
python -m apollo.evaluate --embedding hash --llm dry-run data/generated_queries.jsonl
```

评测指标：

- `Accuracy(tool_code)`
- `Slot F1`

## 简历写法

实现两阶段工具路由系统：第一阶段基于 BGE embedding 做语义召回（Top-K tools），第二阶段由 LLM 完成工具仲裁与槽位抽取，在百级工具规模下保持低延迟与稳定识别精度。
