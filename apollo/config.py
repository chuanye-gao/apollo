from __future__ import annotations

import ast
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class ArgumentSpec:
    type: str
    required: bool = False


@dataclass(frozen=True)
class Tool:
    code: str
    name: str
    description: str
    category: str
    aliases: list[str]
    examples: list[str]
    arguments: dict[str, ArgumentSpec]

    def embedding_text(self) -> str:
        return (
            f"name: {self.name}\n"
            f"category: {self.category}\n"
            f"description: {self.description}\n"
            f"aliases: {self.aliases}\n"
            f"examples: {self.examples}"
        )

    def to_prompt_dict(self) -> dict[str, Any]:
        return {
            "code": self.code,
            "name": self.name,
            "category": self.category,
            "description": self.description,
            "aliases": self.aliases,
            "examples": self.examples,
            "arguments": {
                name: {"type": spec.type, "required": spec.required}
                for name, spec in self.arguments.items()
            },
        }


def default_tools_path() -> Path:
    return Path(__file__).resolve().parent.parent / "configs" / "tools.yaml"


def load_tools(path: str | Path | None = None) -> list[Tool]:
    source = Path(path) if path else default_tools_path()
    raw = source.read_text(encoding="utf-8")
    data = _load_yaml(raw)
    tools = [_parse_tool(item) for item in data.get("tools", [])]
    codes = [tool.code for tool in tools]
    duplicated = sorted({code for code in codes if codes.count(code) > 1})
    if duplicated:
        raise ValueError(f"duplicate tool codes in tools config: {duplicated}")
    if "none" not in set(codes):
        raise ValueError('tools config must include tool_code = "none"')
    return tools


def _parse_tool(item: dict[str, Any]) -> Tool:
    args: dict[str, ArgumentSpec] = {}
    for name, spec in (item.get("arguments") or {}).items():
        args[name] = ArgumentSpec(
            type=str(spec.get("type", "string")),
            required=bool(spec.get("required", False)),
        )
    return Tool(
        code=str(item["code"]),
        name=str(item["name"]),
        description=str(item["description"]),
        category=str(item.get("category", "uncategorized")),
        aliases=list(item.get("aliases") or []),
        examples=list(item.get("examples") or []),
        arguments=args,
    )


def _load_yaml(raw: str) -> dict[str, Any]:
    try:
        import yaml  # type: ignore

        loaded = yaml.safe_load(raw)
        return loaded or {}
    except ModuleNotFoundError:
        return _load_simple_tools_yaml(raw)


def _load_simple_tools_yaml(raw: str) -> dict[str, Any]:
    """Tiny fallback parser for this repository's tools.yaml shape.

    PyYAML is the recommended parser. This keeps local smoke tests runnable in a
    bare Python environment and intentionally supports only the config shape
    used by configs/tools.yaml.
    """

    tools: list[dict[str, Any]] = []
    current: dict[str, Any] | None = None
    current_examples: list[str] | None = None
    current_args: dict[str, Any] | None = None
    current_arg_name: str | None = None

    for raw_line in raw.splitlines():
        if not raw_line.strip() or raw_line.lstrip().startswith("#"):
            continue
        indent = len(raw_line) - len(raw_line.lstrip(" "))
        line = raw_line.strip()
        if line == "tools:":
            continue
        if indent == 2 and line.startswith("- code:"):
            current = {"code": _scalar(line.split(":", 1)[1].strip())}
            tools.append(current)
            current_examples = None
            current_args = None
            current_arg_name = None
            continue
        if current is None:
            continue
        if indent == 4 and line.endswith(":") and line[:-1] == "examples":
            current_examples = []
            current["examples"] = current_examples
            current_args = None
            continue
        if indent == 4 and line.endswith(":") and line[:-1] == "arguments":
            current_args = {}
            current["arguments"] = current_args
            current_examples = None
            continue
        if indent == 4 and ":" in line:
            key, value = line.split(":", 1)
            current[key] = _scalar(value.strip())
            current_examples = None
            current_arg_name = None
            continue
        if indent == 6 and current_examples is not None and line.startswith("- "):
            current_examples.append(_scalar(line[2:].strip()))
            continue
        if indent == 6 and current_args is not None and line.endswith(":"):
            current_arg_name = line[:-1]
            current_args[current_arg_name] = {}
            continue
        if indent == 8 and current_args is not None and current_arg_name and ":" in line:
            key, value = line.split(":", 1)
            current_args[current_arg_name][key] = _scalar(value.strip())

    return {"tools": tools}


def _scalar(value: str) -> Any:
    if value in {"true", "True"}:
        return True
    if value in {"false", "False"}:
        return False
    if value == "{}":
        return {}
    if value.startswith("[") or value.startswith('"') or value.startswith("'"):
        return ast.literal_eval(value)
    return value
