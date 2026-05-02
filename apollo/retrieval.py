from __future__ import annotations

from dataclasses import dataclass

from apollo.config import Tool
from apollo.embedding import EmbeddingModel, cosine


TOP_K = 8


@dataclass(frozen=True)
class Candidate:
    tool: Tool
    score: float

    def to_prompt_dict(self) -> dict[str, object]:
        data = self.tool.to_prompt_dict()
        data["retrieval_score"] = round(self.score, 4)
        return data


class ToolRetriever:
    def __init__(self, tools: list[Tool], embedding_model: EmbeddingModel) -> None:
        self.tools = tools
        self.embedding_model = embedding_model
        self.tool_vectors = embedding_model.encode([tool.embedding_text() for tool in tools])

    def retrieve(self, query: str, k: int = TOP_K) -> list[Candidate]:
        query_vector = self.embedding_model.encode([query])[0]
        ranked = sorted(
            [
                Candidate(tool=tool, score=cosine(query_vector, vector))
                for tool, vector in zip(self.tools, self.tool_vectors)
            ],
            key=lambda item: item.score,
            reverse=True,
        )
        selected = ranked[:k]
        if not any(candidate.tool.code == "none" for candidate in selected):
            none_candidate = next(candidate for candidate in ranked if candidate.tool.code == "none")
            selected = selected[: max(0, k - 1)] + [none_candidate]
        return selected
