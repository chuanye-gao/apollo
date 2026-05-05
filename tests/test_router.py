from __future__ import annotations

import unittest

from apollo.config import load_tools
from apollo.embedding import HashEmbeddingModel
from apollo.llm import DryRunClient
from apollo.router import Router


class RouterTest(unittest.TestCase):
    def setUp(self) -> None:
        self.tools = load_tools()
        self.router = Router(
            tools=self.tools,
            embedding_model=HashEmbeddingModel(),
            llm_client=DryRunClient(),
        )

    def test_tool_config_has_150_unique_codes(self) -> None:
        codes = [tool.code for tool in self.tools]
        self.assertEqual(len(codes), 150)
        self.assertEqual(len(set(codes)), 150)
        self.assertIn("none", codes)

    def test_retrieval_always_includes_none(self) -> None:
        candidates = self.router.retrieve("请帮我创建提醒，内容：开会，时间：明天下午三点")
        self.assertLessEqual(len(candidates), 8)
        self.assertIn("none", {candidate.tool.code for candidate in candidates})

    def test_message_route(self) -> None:
        result = self.router.route("请帮我发送消息，收件人：张三，内容：我晚点到")
        self.assertEqual(result.tool_code, "message.send")
        self.assertEqual(result.arguments["recipient"], "张三")
        self.assertEqual(result.arguments["content"], "我晚点到")

    def test_none_route(self) -> None:
        result = self.router.route("解释一下余弦相似度是什么")
        self.assertEqual(result.tool_code, "none")
        self.assertFalse(result.is_instruction)
        self.assertEqual(result.arguments, {})

    def test_missing_required_arguments_are_computed(self) -> None:
        result = self.router.route("请帮我发送消息，收件人：张三")
        self.assertEqual(result.tool_code, "message.send")
        self.assertIn("content", result.missing_required_arguments)


if __name__ == "__main__":
    unittest.main()
