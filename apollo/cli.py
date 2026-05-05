from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from apollo.cache import DEFAULT_CACHE_PATH, compute_tools_hash, save_cache
from apollo.config import default_tools_path, load_tools
from apollo.embedding import BGEEmbeddingModel, HashEmbeddingModel
from apollo.router import Router


def main() -> None:
    argv = sys.argv[1:]
    if argv and argv[0] == "precompute":
        _precompute(argv[1:])
        return
    if argv and argv[0] == "route":
        argv = argv[1:]
    _route(argv)


def _route(argv: list[str]) -> None:
    parser = argparse.ArgumentParser(prog="router")
    parser.add_argument("query", help="user query")
    parser.add_argument("--tools", default=None, help="tool YAML config path")
    parser.add_argument("--embedding", choices=["bge", "hash"], default="bge")
    parser.add_argument("--llm", choices=["openai", "dry-run"], default="openai")
    parser.add_argument("--show-candidates", action="store_true", help="print retrieval candidates for debugging")
    args = parser.parse_args(argv)

    router = Router.for_modes(embedding=args.embedding, llm=args.llm, tools_path=args.tools)
    if args.show_candidates:
        candidates = [candidate.to_prompt_dict() for candidate in router.retrieve(args.query)]
        print(json.dumps({"candidates": candidates}, ensure_ascii=False, indent=2))
        return
    result = router.route(args.query)
    print(json.dumps(result.to_dict(), ensure_ascii=False, indent=2))


def _precompute(argv: list[str]) -> None:
    parser = argparse.ArgumentParser(prog="router precompute")
    parser.add_argument("--tools", default=None, help="tool YAML config path")
    parser.add_argument("--embedding", choices=["bge", "hash"], default="bge")
    args = parser.parse_args(argv)

    tools_path = Path(args.tools) if args.tools else default_tools_path()
    tools = load_tools(tools_path)
    if args.embedding == "bge":
        model = BGEEmbeddingModel()
    else:
        model = HashEmbeddingModel()
    vectors = model.encode([tool.embedding_text() for tool in tools])
    save_cache(vectors, [tool.code for tool in tools], compute_tools_hash(tools_path), embedding=args.embedding)
    print(f"Cached {len(tools)} tool embeddings -> {DEFAULT_CACHE_PATH}")


if __name__ == "__main__":
    main()
