from __future__ import annotations

import json
import os
import re
import urllib.request
from typing import Protocol

from apollo.retrieval import Candidate


class LLMClient(Protocol):
    def complete(self, prompt: str) -> str:
        ...


class OpenAICompatibleClient:
    def __init__(
        self,
        api_key: str | None = None,
        model: str | None = None,
        base_url: str | None = None,
        timeout_seconds: int = 60,
    ) -> None:
        self.api_key = api_key or os.getenv("APOLLO_LLM_API_KEY")
        self.model = model or os.getenv("APOLLO_LLM_MODEL")
        self.base_url = (base_url or os.getenv("APOLLO_LLM_BASE_URL") or "https://api.openai.com/v1").rstrip("/")
        self.timeout_seconds = timeout_seconds
        if not self.api_key:
            raise RuntimeError("APOLLO_LLM_API_KEY is required for LLM arbitration")
        if not self.model:
            raise RuntimeError("APOLLO_LLM_MODEL is required for LLM arbitration")

    def complete(self, prompt: str) -> str:
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": "你只输出合法 JSON，不输出解释。"},
                {"role": "user", "content": prompt},
            ],
            "temperature": 0,
            "response_format": {"type": "json_object"},
        }
        request = urllib.request.Request(
            f"{self.base_url}/chat/completions",
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            },
            method="POST",
        )
        with urllib.request.urlopen(request, timeout=self.timeout_seconds) as response:
            data = json.loads(response.read().decode("utf-8"))
        return data["choices"][0]["message"]["content"]


ARGUMENT_LABELS: dict[str, list[str]] = {
    "recipient": ["收件人", "联系人", "发送给", "recipient"],
    "content": ["内容", "正文", "消息", "备注", "content"],
    "subject": ["主题", "subject"],
    "title": ["标题", "事项", "会议", "title"],
    "time": ["时间", "时刻", "time"],
    "date": ["日期", "哪天", "date"],
    "location": ["地点", "城市", "位置", "location"],
    "destination": ["目的地", "终点", "destination"],
    "origin": ["起点", "出发地", "origin"],
    "query": ["查询", "关键词", "名称", "query"],
    "name": ["姓名", "名称", "name"],
    "file": ["文件", "文件名", "file"],
    "folder": ["文件夹", "目录", "folder"],
    "url": ["链接", "网址", "url"],
    "amount": ["金额", "数量", "数值", "amount"],
    "unit": ["单位", "unit"],
    "source": ["来源", "源", "source"],
    "target": ["目标", "目标语言", "target"],
    "language": ["语言", "language"],
    "priority": ["优先级", "priority"],
    "status": ["状态", "status"],
    "assignee": ["负责人", "assignee"],
    "device": ["设备", "device"],
    "mode": ["模式", "mode"],
    "temperature": ["温度", "temperature"],
    "duration": ["时长", "duration"],
}

NON_INSTRUCTION_MARKERS = [
    "为什么",
    "怎么学习",
    "解释一下",
    "是什么",
    "你是谁",
    "谢谢",
    "讲个笑话",
    "原理",
    "区别",
]


class DryRunClient:
    """Local deterministic arbiter for tests, baselines, and smoke demos.

    It intentionally avoids network calls. Selection is lexical over the already
    recalled candidates, while argument extraction only accepts values that are
    explicitly present in the query after known labels.
    """

    def complete_with_context(self, query: str, candidates: list[Candidate]) -> str:
        selected = self.select(query, candidates)
        args = self.extract_args(query, selected)
        is_instruction = selected.tool.code != "none"
        if not is_instruction:
            args = {}
        result = {
            "is_instruction": is_instruction,
            "tool_code": selected.tool.code,
            "intent": selected.tool.name,
            "arguments": args,
            "missing_required_arguments": [],
            "confidence": min(0.99, max(0.1, selected.score)),
            "reason": "dry-run 本地仲裁",
        }
        return json.dumps(result, ensure_ascii=False)

    def complete(self, prompt: str) -> str:
        raise RuntimeError("DryRunClient requires complete_with_context(query, candidates)")

    def select(self, query: str, candidates: list[Candidate]) -> Candidate:
        none = next((candidate for candidate in candidates if candidate.tool.code == "none"), None)
        if any(marker in query for marker in NON_INSTRUCTION_MARKERS) and none is not None:
            return none

        scored: list[tuple[float, Candidate]] = []
        compact_query = re.sub(r"\s+", "", query).lower()
        for candidate in candidates:
            if candidate.tool.code == "none":
                scored.append((candidate.score - 0.25, candidate))
                continue
            boost = 0.0
            terms = [candidate.tool.name, candidate.tool.code, *candidate.tool.aliases]
            for term in terms:
                normalized = re.sub(r"\s+", "", str(term)).lower()
                if normalized and normalized in compact_query:
                    boost += 1.0 if term == candidate.tool.name else 0.55
            scored.append((candidate.score + boost, candidate))
        return max(scored, key=lambda item: item[0])[1]

    def extract_args(self, query: str, selected: Candidate) -> dict[str, str]:
        args: dict[str, str] = {}
        for name in selected.tool.arguments:
            value = _extract_labeled_value(query, name)
            if value:
                args[name] = value
        return args


def _extract_labeled_value(query: str, argument_name: str) -> str | None:
    labels = ARGUMENT_LABELS.get(argument_name, [argument_name])
    labels = [*labels, argument_name]
    for label in labels:
        pattern = rf"(?:{re.escape(label)})\s*[:：]\s*([^，。,；;\n]+)"
        match = re.search(pattern, query, flags=re.IGNORECASE)
        if match:
            return match.group(1).strip()
    return None
