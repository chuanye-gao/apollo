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


class DryRunClient:
    """Local deterministic arbiter for tests and smoke demos only."""

    def complete_with_context(self, query: str, candidates: list[Candidate]) -> str:
        selected = self._select(query, candidates)
        args = self._extract_args(query, selected.tool.code)
        if selected.tool.code == "none":
            is_instruction = False
            args = {}
        else:
            is_instruction = True
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

    def _select(self, query: str, candidates: list[Candidate]) -> Candidate:
        question_markers = ["为什么", "怎么学习", "解释", "是什么", "你是谁", "谢谢", "讲个笑话"]
        if any(marker in query for marker in question_markers):
            none = next((candidate for candidate in candidates if candidate.tool.code == "none"), None)
            if none:
                return none
        return max(
            (candidate for candidate in candidates if candidate.tool.code != "none"),
            key=lambda candidate: candidate.score,
            default=candidates[0],
        )

    def _extract_args(self, query: str, tool_code: str) -> dict[str, str]:
        if tool_code == "message.send":
            match = re.search(r"给(.+?)(?:发消息|发短信|发一句|说|通知|告诉)(?:说)?(.+)", query)
            if match:
                return {"recipient": match.group(1).strip(), "content": match.group(2).strip(" ：:，,")}
            match = re.search(r"告诉(.+?)(.+)", query)
            if match:
                return {"recipient": match.group(1).strip(), "content": match.group(2).strip(" ：:，,")}
            return {}
        if tool_code == "alarm.create":
            args: dict[str, str] = {}
            time = _first_match(query, [r"(半小时后)", r"((?:上午|下午|晚上|早上|明早)?[一二三四五六七八九十\d]{1,3}点(?:半|三十)?)"])
            date = _first_match(query, [r"(今天|明天|后天|周[一二三四五六日天]|下周[一二三四五六日天])"])
            if time:
                args["time"] = time
            if date:
                args["date"] = date
            return args
        if tool_code == "weather.query":
            location = _first_match(query, [r"查一下(.+?)(?:今天|明天|后天|周末)?的天气", r"(.+?)(?:今天|明天|现在|周末).*(?:天气|下雨|多少度)"])
            args = {}
            if location:
                args["location"] = location.strip("看看查一下")
            date = _first_match(query, [r"(今天|明天|后天|周末)"])
            if date:
                args["date"] = date
            return args
        if tool_code == "navigation.start":
            destination = _first_match(query, [r"(?:导航到|带我去|去)(.+)", r"规划去(.+?)最快"])
            return {"destination": destination.strip()} if destination else {}
        if tool_code == "music.play":
            music = _first_match(query, [r"(?:播放|放点|来一首|来点|我想听)(.+)"])
            return {"query": music.strip()} if music else {}
        if tool_code in {"note.create", "todo.create"}:
            content = _first_match(query, [r"(?:记一下|记录灵感：|记录|备忘：|加一个待办：|创建任务)(.+)"])
            return {"content": content.strip()} if content else {}
        if tool_code == "contact.search":
            name = _first_match(query, [r"查一下(.+?)的", r"找(.+?)的", r"搜索通讯录里的(.+)"])
            return {"name": name.strip()} if name else {}
        if tool_code == "calendar.create":
            time = _first_match(query, [r"((?:上午|下午|晚上|今晚)?[一二三四五六七八九十\d]{1,3}点)"])
            date = _first_match(query, [r"(今天|明天|下周[一二三四五六日天]|周[一二三四五六日天])"])
            title = query
            for word in ["安排", "创建", "加入日历", "加一个", "帮我"]:
                title = title.replace(word, "")
            args = {"title": title.strip(" ，,")}
            if time:
                args["time"] = time
            if date:
                args["date"] = date
            return args
        if tool_code == "email.send":
            recipient = _first_match(query, [r"给(.+?)发邮件", r"发邮件给(.+?)(?:询问|说明|反馈|通知|，|,|$)"])
            content = _first_match(query, [r"(?:说明|询问|反馈|通知)(.+)"])
            args = {}
            if recipient:
                args["recipient"] = recipient.strip()
            if content:
                args["content"] = content.strip()
            return args
        return {}


def _first_match(text: str, patterns: list[str]) -> str | None:
    for pattern in patterns:
        match = re.search(pattern, text)
        if match:
            return match.group(1)
    return None
