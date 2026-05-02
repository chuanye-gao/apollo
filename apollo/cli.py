from __future__ import annotations

import argparse
import json

from apollo.router import Router


def main() -> None:
    parser = argparse.ArgumentParser(prog="router")
    parser.add_argument("query", help="用户 query")
    parser.add_argument("--tools", default=None, help="工具 YAML 配置路径")
    parser.add_argument("--embedding", choices=["bge", "hash"], default="bge")
    parser.add_argument("--llm", choices=["openai", "dry-run"], default="openai")
    parser.add_argument("--show-candidates", action="store_true", help="输出召回候选，便于调试")
    args = parser.parse_args()

    router = Router.for_modes(embedding=args.embedding, llm=args.llm, tools_path=args.tools)
    if args.show_candidates:
        candidates = [candidate.to_prompt_dict() for candidate in router.retrieve(args.query)]
        print(json.dumps({"candidates": candidates}, ensure_ascii=False, indent=2))
        return
    result = router.route(args.query)
    print(json.dumps(result.to_dict(), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
