from __future__ import annotations

import argparse
import json
import time
from pathlib import Path
from typing import Any

from apollo.config import Tool, load_tools
from apollo.llm import DryRunClient
from apollo.retrieval import Candidate
from apollo.router import Router


DEFAULT_KS = [3, 5, 8, 10]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("dataset", help="JSONL dataset path")
    parser.add_argument("--tools", default=None)
    parser.add_argument("--embedding", choices=["bge", "hash"], default="bge")
    parser.add_argument("--llm", choices=["openai", "dry-run"], default="openai")
    parser.add_argument("--ks", default="3,5,8,10", help="comma separated top-k recall values")
    args = parser.parse_args()

    rows = _load_jsonl(Path(args.dataset))
    tools = load_tools(args.tools)
    ks = [int(item) for item in args.ks.split(",") if item.strip()]
    report = evaluate(rows, tools, args.tools, args.embedding, args.llm, ks)
    print(json.dumps(report, ensure_ascii=False, indent=2))


def evaluate(
    rows: list[dict[str, Any]],
    tools: list[Tool],
    tools_path: str | None,
    embedding: str,
    llm: str,
    ks: list[int] | None = None,
) -> dict[str, Any]:
    ks = ks or DEFAULT_KS
    router = Router.for_modes(embedding=embedding, llm=llm, tools_path=tools_path)
    tool_by_code = {tool.code: tool for tool in tools}

    started = time.perf_counter()
    predictions = [router.route(row["query"]).to_dict() for row in rows]
    elapsed_ms = (time.perf_counter() - started) * 1000

    topk_recall = {
        f"top_{k}_recall": _topk_recall(router, rows, k)
        for k in ks
    }
    category_stats = _category_stats(rows, predictions, tool_by_code)
    baselines = {
        "keyword": _keyword_baseline(rows, tools, router),
        "embedding_only": _embedding_only_baseline(rows, router),
        "llm_full_prompt": _llm_full_prompt_baseline(rows, tools, router),
        "apollo_two_stage": _summarize_predictions(rows, predictions, elapsed_ms),
    }

    summary = _summarize_predictions(rows, predictions, elapsed_ms)
    return {
        "dataset": {
            "rows": len(rows),
            "tools": len(tools),
            "none_rows": sum(1 for row in rows if row["tool_code"] == "none"),
        },
        "metrics": {
            "top_1_accuracy": summary["top_1_accuracy"],
            **topk_recall,
            "slot_precision": summary["slot_precision"],
            "slot_recall": summary["slot_recall"],
            "slot_f1": summary["slot_f1"],
            "none_accuracy": summary["none_accuracy"],
        },
        "by_category": category_stats,
        "baselines": baselines,
    }


def _load_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def _topk_recall(router: Router, rows: list[dict[str, Any]], k: int) -> float:
    hits = 0
    for row in rows:
        candidates = router.retriever.retrieve(row["query"], k=k)
        if row["tool_code"] in {candidate.tool.code for candidate in candidates}:
            hits += 1
    return hits / len(rows) if rows else 0.0


def _summarize_predictions(
    rows: list[dict[str, Any]],
    predictions: list[dict[str, Any]],
    elapsed_ms: float,
) -> dict[str, float]:
    correct = sum(1 for row, result in zip(rows, predictions) if result["tool_code"] == row["tool_code"])
    none_rows = [(row, result) for row, result in zip(rows, predictions) if row["tool_code"] == "none"]
    none_correct = sum(1 for row, result in none_rows if result["tool_code"] == "none")
    tp = fp = fn = 0
    for row, result in zip(rows, predictions):
        row_tp, row_fp, row_fn = _slot_counts(row.get("arguments") or {}, result.get("arguments") or {})
        tp += row_tp
        fp += row_fp
        fn += row_fn
    precision = tp / (tp + fp) if tp + fp else 0.0
    recall = tp / (tp + fn) if tp + fn else 0.0
    return {
        "top_1_accuracy": correct / len(rows) if rows else 0.0,
        "slot_precision": precision,
        "slot_recall": recall,
        "slot_f1": 2 * precision * recall / (precision + recall) if precision + recall else 0.0,
        "none_accuracy": none_correct / len(none_rows) if none_rows else 0.0,
        "avg_latency_ms": elapsed_ms / len(rows) if rows else 0.0,
    }


def _category_stats(
    rows: list[dict[str, Any]],
    predictions: list[dict[str, Any]],
    tool_by_code: dict[str, Tool],
) -> dict[str, dict[str, float]]:
    buckets: dict[str, dict[str, float]] = {}
    for row, result in zip(rows, predictions):
        tool = tool_by_code.get(row["tool_code"])
        category = tool.category if tool else "unknown"
        bucket = buckets.setdefault(category, {"total": 0, "correct": 0, "accuracy": 0.0})
        bucket["total"] += 1
        if result["tool_code"] == row["tool_code"]:
            bucket["correct"] += 1
    for bucket in buckets.values():
        bucket["accuracy"] = bucket["correct"] / bucket["total"] if bucket["total"] else 0.0
    return buckets


def _keyword_baseline(rows: list[dict[str, Any]], tools: list[Tool], router: Router) -> dict[str, float]:
    started = time.perf_counter()
    predictions = []
    all_candidates = [Candidate(tool=tool, score=0.0) for tool in tools]
    dry_run = DryRunClient()
    keyword_index = _build_keyword_index(tools)
    for row in rows:
        query = row["query"]
        tool = _keyword_select(query, tools, keyword_index)
        selected = Candidate(tool=tool, score=1.0)
        data = {
            "is_instruction": tool.code != "none",
            "tool_code": tool.code,
            "intent": tool.name,
            "arguments": dry_run.extract_args(query, selected),
            "missing_required_arguments": [],
            "confidence": 0.5,
            "reason": "keyword baseline",
        }
        predictions.append(router._validate(data, all_candidates))
    elapsed_ms = (time.perf_counter() - started) * 1000
    summary = _summarize_predictions(rows, [item.to_dict() for item in predictions], elapsed_ms)
    summary["prompt_tokens_estimate"] = 0.0
    summary["cost_estimate_usd"] = 0.0
    return summary


def _embedding_only_baseline(rows: list[dict[str, Any]], router: Router) -> dict[str, float]:
    started = time.perf_counter()
    predictions = []
    for row in rows:
        candidates = router.retriever.retrieve(row["query"], k=10)
        selected = next((candidate for candidate in candidates if candidate.tool.code != "none"), candidates[0])
        data = {
            "is_instruction": selected.tool.code != "none",
            "tool_code": selected.tool.code,
            "intent": selected.tool.name,
            "arguments": {},
            "missing_required_arguments": [],
            "confidence": selected.score,
            "reason": "embedding only baseline",
        }
        predictions.append(router._validate(data, candidates).to_dict())
    elapsed_ms = (time.perf_counter() - started) * 1000
    summary = _summarize_predictions(rows, predictions, elapsed_ms)
    summary["prompt_tokens_estimate"] = 0.0
    summary["cost_estimate_usd"] = 0.0
    return summary


def _llm_full_prompt_baseline(rows: list[dict[str, Any]], tools: list[Tool], router: Router) -> dict[str, float]:
    started = time.perf_counter()
    predictions = []
    candidates = [Candidate(tool=tool, score=0.0) for tool in tools]
    dry_run = DryRunClient()
    for row in rows:
        raw = dry_run.complete_with_context(row["query"], candidates)
        predictions.append(router._validate(json.loads(raw), candidates).to_dict())
    elapsed_ms = (time.perf_counter() - started) * 1000
    summary = _summarize_predictions(rows, predictions, elapsed_ms)
    prompt_size = len(json.dumps([tool.to_prompt_dict() for tool in tools], ensure_ascii=False))
    summary["prompt_tokens_estimate"] = float(prompt_size // 4)
    summary["cost_estimate_usd"] = summary["prompt_tokens_estimate"] * len(rows) / 1_000_000 * 0.15
    return summary


def _build_keyword_index(tools: list[Tool]) -> dict[str, list[str]]:
    return {
        tool.code: [tool.name, tool.code, *tool.aliases]
        for tool in tools
    }


def _keyword_select(query: str, tools: list[Tool], keyword_index: dict[str, list[str]]) -> Tool:
    query_lower = query.lower()
    best_score = float("-inf")
    best = next(tool for tool in tools if tool.code == "none")
    for tool in tools:
        score = 0.0
        for term in keyword_index[tool.code]:
            if str(term).lower() in query_lower:
                score += 3.0 if term == tool.name else 1.0
        if tool.code == "none" and any(marker in query for marker in ["为什么", "是什么", "解释", "谢谢"]):
            score += 3.0
        if score > best_score:
            best_score = score
            best = tool
    return best


def _slot_counts(expected: dict[str, Any], actual: dict[str, Any]) -> tuple[int, int, int]:
    expected_items = {(key, str(value)) for key, value in expected.items()}
    actual_items = {(key, str(value)) for key, value in actual.items()}
    return (
        len(expected_items & actual_items),
        len(actual_items - expected_items),
        len(expected_items - actual_items),
    )


if __name__ == "__main__":
    main()
