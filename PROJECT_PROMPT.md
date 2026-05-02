## 项目目标

实现一个基于 **embedding 语义召回 + LLM 仲裁** 的意图识别系统。

输入：

- 用户 query

输出：

- tool_code
- arguments
- is_instruction
- missing_required_arguments
- confidence

系统核心：

> 用 embedding 做工具语义召回（Top-K），再用 LLM 做最终决策与参数抽取。

------

## 核心设计（必须遵守）

必须采用“两阶段架构”：

```text
query
  ↓
embedding 语义召回（Top-K tools）
  ↓
LLM 仲裁（只在 Top-K 中选择）
  ↓
结构化输出
```

禁止：

- 不允许把所有工具塞进 prompt
- 不允许用 LLM 做粗选
- 不允许跳过召回阶段

------

## embedding 选型

使用：

- bge-small-zh-v1.5

原因：

- 小模型（~30M 参数级别）
- 向量维度约 384
- 支持语义检索、聚类、匹配
- 中文表现稳定
- CPU 可跑

------

## 工具 embedding 构建（离线）

对每个 tool，拼接文本：

```text
tool_text = f"""
name: {name}
description: {description}
aliases: {aliases}
examples: {examples}
"""
```

对 tool_text 生成 embedding：

```python
tool_embedding = model.encode(tool_text)
```

存储：

```python
{
  "code": "...",
  "embedding": vector
}
```

------

## query embedding

```python
query_embedding = model.encode(query)
```

------

## 相似度计算

使用 cosine similarity：

```python
score = cosine(query_embedding, tool_embedding)
```

------

## Top-K 召回

```python
top_k_tools = sorted(tools, key=score, reverse=True)[:8]
```

强制规则：

- K = 8
- 必须加入 tool_code = "none"

------

## 工具配置格式

```yaml
tools:
  - code: "alarm.create"
    name: "创建闹钟"
    description: "设置闹钟或提醒"
    aliases: ["闹钟", "提醒我", "叫我"]
    examples:
      - "明早八点叫我起床"
      - "设置一个下午三点的闹钟"
    arguments:
      time:
        type: "string"
        required: true
      date:
        type: "string"
        required: false

  - code: "message.send"
    name: "发送消息"
    description: "发送短信或消息"
    aliases: ["发消息", "发短信", "告诉某人"]
    examples:
      - "给张三发消息说我晚点到"
    arguments:
      recipient:
        type: "string"
        required: true
      content:
        type: "string"
        required: true

  - code: "none"
    name: "非指令"
    description: "闲聊或问问题"
    aliases: []
    examples: []
    arguments: {}
```

------

## Prompt（只使用 Top-K tools）

```text
你是一个工具路由器。

你的任务：
根据用户 query，从候选工具中选择最合适的工具，并抽取参数。

你不能回答问题。
你不能执行工具。
你只能输出 JSON。

用户 query：
{query}

候选工具（仅限以下）：
{top_k_tools}

规则：

1. 如果用户不是在发指令，而是聊天或提问，则：
   tool_code = "none"
   is_instruction = false

2. 如果用户在发指令：
   is_instruction = true
   只能从候选工具中选 tool_code

3. arguments 只能来自 query，不允许编造

4. 缺少参数：
   填入 missing_required_arguments

5. 多工具冲突：
   选最直接的

输出：

{
  "is_instruction": true,
  "tool_code": "...",
  "intent": "...",
  "arguments": {},
  "missing_required_arguments": [],
  "confidence": 0.0,
  "reason": "不超过50字"
}
```

------

## Router 流程

```python
def route(query):
    # 1. encode query
    q_emb = embed(query)

    # 2. 计算与所有 tool embedding 相似度
    scores = cosine(q_emb, tool_embeddings)

    # 3. 取 Top-K
    candidates = top_k(scores, k=8)

    # 4. 构造 prompt（只包含 candidates）
    prompt = build_prompt(query, candidates)

    # 5. 调用 LLM
    result = llm(prompt)

    # 6. 解析 JSON + 校验
    return result
```

------

## CLI

```bash
router "明天下午三点提醒我开会"
```

输出：

```json
{
  "is_instruction": true,
  "tool_code": "alarm.create",
  "intent": "创建闹钟",
  "arguments": {
    "time": "15:00"
  },
  "missing_required_arguments": [],
  "confidence": 0.92,
  "reason": "用户要求设置提醒"
}
```

------

## 数据（你没有数据的解决方案）

必须自己生成：

### Step 1（手写）

每个工具写 5 条 example

### Step 2（自动生成）

让 LLM 扩写：

```text
给定工具 schema，生成20条用户 query：
- 正常表达
- 口语表达
- 参数缺失
- 模糊表达
```

### Step 3（评测）

指标：

```text
Accuracy(tool_code)
Slot F1
```

------

## 项目定位（写在 README）

```text
一个基于 embedding 语义召回 + LLM 仲裁的工具路由系统，
用于 Function Calling / MCP 场景下的意图识别与参数抽取。
```

------

## 简历写法

```text
实现两阶段工具路由系统：
第一阶段基于 BGE embedding 做语义召回（Top-K tools），
第二阶段由 LLM 完成工具仲裁与槽位抽取，
在百级工具规模下保持低延迟与稳定识别精度。
```

------

## 强制约束（非常重要）

- 不要引入 LangChain
- 不要引入 LangGraph
- 不要过度抽象
- 不要设计复杂架构
- 不要做多轮 Agent
- 不要做真实工具执行
- 只做：router

## 项目名称是：apollo