# -*- coding:utf-8 -*-
from metagpt.actions.action import Action
from metagpt.roles.role import Role
from metagpt.schema import Message
from metagpt.logs import logger
import re


class MakeConsensus(Action):
    name: str = "MakeConsensus"

    async def run(self, codes: list[str]) -> str:
        if not codes:
            return "No codes to process."

        # 组装提示信息，将收到的代码作为参考
        prompt = "Given the following Python code snippets, create a consensus version that incorporates the best aspects of each:\n\n"
        for i, code in enumerate(codes, 1):
            prompt += f"Code snippet {i}:\n```python\n{code}\n```\n\n"
        prompt += "Your consensus code:\n"

        # 调用 LLM 来处理提示信息并生成最终代码
        final_code = await self._aask(prompt)
        return final_code


class ConsensusMaker(Role):
    name: str = "Sam"
    profile: str = "Consensus Maker"
    goal: str = "Receive output from other members of the group and determine if they reach a consensus"
    constraints: str = ""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    async def run(self, with_message=None) -> None:
        if not await self._observe():
            # If there is no new information, suspend and wait
            logger.debug(f"{self._setting}: no news. waiting.")
            return
        # 从内存中检索所有相关的代码消息
        codes = [msg.content for msg in self.get_memories() if isinstance(msg.cause_by, WriteCode)]

        if codes:
            # 如果收到了代码，调用 MakeConsensus 动作来生成共识代码
            consensus_action = MakeConsensus()
            final_code = await consensus_action.run(codes)
            # 输出最终代码，或进行其他处理
            print(f"Consensus code: {final_code}")
            # 发布共识代码结果，可以选择发送给特定角色或处理其他逻辑
            # self.publish_message(Message(content=final_code, ...))
