# -*- coding:utf-8 -*-
from metagpt.actions.action import Action
from metagpt.roles.role import Role
from metagpt.schema import Message
from metagpt.logs import logger
import json


class MakeConsensus(Action):
    PROMPT_TEMPLATE: str = """
        Your task is to create a consensus version that incorporates the best aspects of each
        Here are the results given by all members of the team with the common goal of {goal}:
        """
    name: str = "MakeConsensus"

    async def run(self, group_message: dict[Role, str], use_llm: bool = False) -> str:
        """给出每个Role的结果，返回共识"""
        if not group_message:
            logger.error(" no group message")
        if not use_llm:
            # TODO
            for i in group_message.items():
                pass
        else:
            goal = list(group_message.keys())[0].goal
            prompt = self.PROMPT_TEMPLATE.format(goal=goal)
            for role, content in group_message:
                prompt += f"{role.profile}:\n{content}\n"
            prompt += "\nReturn the consensus version with NO other texts,\nconsensus content:\n"

            consensus_content = await self._aask(prompt)
            return consensus_content


class CheckConsensus(Action):
    PROMPT_TEMPLATE: str = (
        "Your task is to check whether all answers given by different members are in agreement. "
        "All members have the same goal: {goal}.\n"
        "You need to give a dict to judge whether they make consensus, "
        "for example:{\"Role1\":True, \"Role2\":False, \"Role3\":True} means Role1 and Role3 are in agreement "
        "while Role2 has different opinions.\n"
        "You need to find the role that reaches the most consensus and set the corresponding item to True, "
        "and the role that does not reach consensus set it to False.\n"
        "Here are the results given by all members of the team:"
    )
    name: str = "CheckConsensus"

    async def run(self, group_message: dict[Role, str], use_llm: bool = True) -> dict[Role, bool]:
        """给出每个Role的结果，查看是否达成共识"""
        if not group_message:
            logger.error(" no group message")
        if not use_llm:
            logger.warning("you should implement not_use_llm method in the subclass")
            return
        else:
            goal = list(group_message.keys())[0].goal
            prompt = self.PROMPT_TEMPLATE.format(goal=goal)
            for role, content in group_message:
                prompt += f"{role.profile}: {content}\n"
            prompt += "\nReturn a dict with NO other texts:"

            consensus_ans = await self._aask(prompt)
            consensus_dict = CheckConsensus.parse_dict(group_message, consensus_ans)
            return consensus_dict

    @staticmethod
    def parse_dict(group_message, rsp) -> dict[Role, bool]:
        if not rsp.startswith("{"):
            logger.error(f"rsp:{rsp} can't be parsed")
        parsed_dict = json.loads(rsp)
        role_bool_dict = {}
        for role in group_message:
            if role.profile in parsed_dict:
                role_bool_dict[role] = parsed_dict[role.profile]
        for role, value in role_bool_dict.items():
            logger.debug(f"Role profile: {role.profile}, Value: {value}")
        return role_bool_dict

class ConsensusMaker(Role):
    name: str = "Sam"
    profile: str = "Consensus Maker"
    goal: str = "Receive output from other members of the group and help they to reach a consensus"
    constraints: str = ""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.set_actions([MakeConsensus])

    async def run(self, with_message=None) -> None:

        codes = [msg.content for msg in self.get_memories() if isinstance(msg.cause_by, WriteCode)]

        if codes:
            # 如果收到了代码，调用 MakeConsensus 动作来生成共识代码
            consensus_action = MakeConsensus()
            final_code = await consensus_action.run(codes)
            # 输出最终代码，或进行其他处理
            print(f"Consensus code: {final_code}")
            # 发布共识代码结果，可以选择发送给特定角色或处理其他逻辑
            # self.publish_message(Message(content=final_code, ...))

    async def _act(self) -> Message:
        group_message = {}
        for i in self.rc.news:
            group_message[self.rc.env.roles[i.role]] = i.content
        rsp = await self.todo.run(group_message)
        return rsp
