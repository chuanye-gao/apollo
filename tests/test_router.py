from __future__ import annotations

import unittest

from apollo.config import load_tools
from apollo.embedding import HashEmbeddingModel
from apollo.llm import DryRunClient
from apollo.router import Router


class RouterTest(unittest.TestCase):
    def setUp(self) -> None:
        self.router = Router(
            tools=load_tools(),
            embedding_model=HashEmbeddingModel(),
            llm_client=DryRunClient(),
        )

    def test_retrieval_always_includes_none(self) -> None:
        candidates = self.router.retrieve("明天下午三点提醒我开会")
        self.assertLessEqual(len(candidates), 8)
        self.assertIn("none", {candidate.tool.code for candidate in candidates})

    def test_message_route(self) -> None:
        result = self.router.route("给张三发消息说我晚点到")
        self.assertEqual(result.tool_code, "message.send")
        self.assertEqual(result.arguments["recipient"], "张三")
        self.assertEqual(result.arguments["content"], "我晚点到")

    def test_none_route(self) -> None:
        result = self.router.route("给我解释一下余弦相似度")
        self.assertEqual(result.tool_code, "none")
        self.assertFalse(result.is_instruction)
        self.assertEqual(result.arguments, {})

    def test_missing_required_arguments_are_computed(self) -> None:
        result = self.router.route("提醒我")
        self.assertEqual(result.tool_code, "alarm.create")
        self.assertIn("time", result.missing_required_arguments)


if __name__ == "__main__":
    unittest.main()
