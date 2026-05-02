from __future__ import annotations

import json

from apollo.retrieval import Candidate


def build_prompt(query: str, candidates: list[Candidate]) -> str:
    candidate_json = json.dumps(
        [candidate.to_prompt_dict() for candidate in candidates],
        ensure_ascii=False,
        indent=2,
    )
    return f"""你是一个工具路由器。

你的任务：
根据用户 query，从候选工具中选择最合适的工具，并抽取参数。

你不能回答问题。
你不能执行工具。
你只能输出 JSON。

用户 query：
{query}

候选工具（仅限以下）：
{candidate_json}

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

{{
  "is_instruction": true,
  "tool_code": "...",
  "intent": "...",
  "arguments": {{}},
  "missing_required_arguments": [],
  "confidence": 0.0,
  "reason": "不超过50字"
}}
"""
