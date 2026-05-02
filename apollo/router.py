from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any

from apollo.config import Tool, load_tools
from apollo.embedding import BGEEmbeddingModel, EmbeddingModel, HashEmbeddingModel
from apollo.llm import DryRunClient, LLMClient, OpenAICompatibleClient
from apollo.prompt import build_prompt
from apollo.retrieval import Candidate, TOP_K, ToolRetriever


@dataclass(frozen=True)
class RouteResult:
    is_instruction: bool
    tool_code: str
    intent: str
    arguments: dict[str, Any]
    missing_required_arguments: list[str]
    confidence: float
    reason: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "is_instruction": self.is_instruction,
            "tool_code": self.tool_code,
            "intent": self.intent,
            "arguments": self.arguments,
            "missing_required_arguments": self.missing_required_arguments,
            "confidence": self.confidence,
            "reason": self.reason,
        }


class Router:
    def __init__(
        self,
        tools: list[Tool] | None = None,
        embedding_model: EmbeddingModel | None = None,
        llm_client: LLMClient | DryRunClient | None = None,
    ) -> None:
        self.tools = tools or load_tools()
        self.tools_by_code = {tool.code: tool for tool in self.tools}
        self.retriever = ToolRetriever(self.tools, embedding_model or BGEEmbeddingModel())
        self.llm_client = llm_client or OpenAICompatibleClient()

    @classmethod
    def for_modes(cls, embedding: str = "bge", llm: str = "openai", tools_path: str | None = None) -> "Router":
        tools = load_tools(tools_path)
        embedding_model: EmbeddingModel
        if embedding == "bge":
            embedding_model = BGEEmbeddingModel()
        elif embedding == "hash":
            embedding_model = HashEmbeddingModel()
        else:
            raise ValueError(f"unknown embedding mode: {embedding}")

        if llm == "openai":
            llm_client: LLMClient | DryRunClient = OpenAICompatibleClient()
        elif llm == "dry-run":
            llm_client = DryRunClient()
        else:
            raise ValueError(f"unknown llm mode: {llm}")
        return cls(tools=tools, embedding_model=embedding_model, llm_client=llm_client)

    def route(self, query: str) -> RouteResult:
        candidates = self.retriever.retrieve(query, k=TOP_K)
        prompt = build_prompt(query, candidates)
        if isinstance(self.llm_client, DryRunClient):
            raw = self.llm_client.complete_with_context(query, candidates)
        else:
            raw = self.llm_client.complete(prompt)
        data = _parse_json(raw)
        return self._validate(data, candidates)

    def retrieve(self, query: str) -> list[Candidate]:
        return self.retriever.retrieve(query, k=TOP_K)

    def build_prompt(self, query: str) -> str:
        return build_prompt(query, self.retrieve(query))

    def _validate(self, data: dict[str, Any], candidates: list[Candidate]) -> RouteResult:
        candidate_codes = {candidate.tool.code for candidate in candidates}
        tool_code = str(data.get("tool_code", "none"))
        if tool_code not in candidate_codes:
            tool_code = "none"
        tool = self.tools_by_code.get(tool_code) or self.tools_by_code["none"]
        arguments = data.get("arguments") if isinstance(data.get("arguments"), dict) else {}
        arguments = {key: value for key, value in arguments.items() if key in tool.arguments and value not in ("", None)}
        missing = [
            name
            for name, spec in tool.arguments.items()
            if spec.required and name not in arguments
        ]
        if tool.code == "none":
            arguments = {}
            missing = []
        confidence = data.get("confidence", 0.0)
        try:
            confidence_float = float(confidence)
        except (TypeError, ValueError):
            confidence_float = 0.0
        confidence_float = min(1.0, max(0.0, confidence_float))
        return RouteResult(
            is_instruction=bool(data.get("is_instruction", tool.code != "none")) and tool.code != "none",
            tool_code=tool.code,
            intent=str(data.get("intent") or tool.name),
            arguments=arguments,
            missing_required_arguments=missing,
            confidence=confidence_float,
            reason=str(data.get("reason") or "")[:50],
        )


def _parse_json(raw: str) -> dict[str, Any]:
    try:
        parsed = json.loads(raw)
        if isinstance(parsed, dict):
            return parsed
    except json.JSONDecodeError:
        pass
    start = raw.find("{")
    end = raw.rfind("}")
    if start >= 0 and end > start:
        parsed = json.loads(raw[start : end + 1])
        if isinstance(parsed, dict):
            return parsed
    raise ValueError("LLM output is not a JSON object")
