# -*- coding:utf-8 -*-
from metagpt.actions.action import Action
from metagpt.roles.role import Role, RoleReactMode
from metagpt.schema import Message
from metagpt.logs import logger
from metagpt.const import MESSAGE_ROUTE_TO_ALL
from abc import abstractmethod
import json
import math
import numpy as np
from route import add_to_route
import random
import re


class MakeConsensus(Action):
    PROMPT_TEMPLATE: str = """
        All the members in the team have the same goal to {goal}.
        Your task is to create a consensus version that incorporates the best aspects of each
        Here are the results given by all members of the team:
        """
    name: str = "MakeConsensus"

    async def run(self, group_message: dict[Role, str], use_llm: bool = False) -> str:
        """给出每个Role的结果，返回共识"""
        if not group_message:
            logger.error(" no group message")
        if not use_llm:
            # 共识算法
            NCTs = {}
            N = sum(r.n for r in group_message.keys())
            for r in group_message.keys():
                NCTs[r] = MakeConsensus.calculate_nct(r.w, r.n, N)
            values = np.array(list(NCTs.values()))
            softmax_values = np.exp(values) / np.sum(np.exp(values))
            softmax_dict = {role: float(value) for role, value in zip(NCTs.keys(), softmax_values)}
            random_number = random.uniform(0, 1)
            selected_role = None
            cumulative_prob = 0
            for role, prob in softmax_dict.items():
                cumulative_prob += prob
                if random_number <= cumulative_prob:
                    selected_role = role
                    break
            if selected_role:
                add_to_route(selected_role)
                return group_message[selected_role]
            else:
                logger.warning("can't make consensus without llm")
                return random.choice(list(group_message.values()))

        else:
            for r in (group_message.keys()):
                add_to_route(r)
            goal = list(group_message.keys())[0].goal
            prompt = self.PROMPT_TEMPLATE.format(goal=goal)
            for role, content in group_message:
                prompt += f"{role.profile}:\n{content}\n"
            prompt += "\nReturn the consensus version with NO other texts,\nconsensus content:\n"

            consensus_content = await self._aask(prompt)
            return consensus_content

    @staticmethod
    def calculate_nct(w, n, N):
        if N == 0:
            return math.log(2)
        elif n == 0:
            return math.log(2) * (math.log(N)) ** 0.5
        else:
            return w / n + math.log(2) * (math.log(N) / n) ** 0.5


class CheckConsensus(Action):
    PROMPT_TEMPLATE: str = (
        "Your task is to check whether all answers given by different members are in agreement. "
        "All members have the same goal: {goal}.\n"
        "You need to give a dict to judge whether they make consensus, "
        "for example:{\"Role1\":true, \"Role2\":false, \"Role3\":true, \"Role4\":true} "
        "means Role1 ,Role3 and Role4 are in agreement while Role2 has different opinions.\n"
        "You need to find the roles that have the most agreements and set their attributes to true. "
        "For roles that do not reach consensus with others, set them to false.\n"
        "In other words, I hope to find the correct answer through this method.\n"
        "Here are the results given by all roles in the team:"
    )
    name: str = "CheckConsensus"

    @abstractmethod
    def check_no_llm(self, group_message: dict[Role, str]) -> str:
        pass

    async def run(self, group_message: dict[Role, str], use_llm: bool = True) -> str:
        """给出每个Role的结果，查看是否达成共识"""
        if not group_message:
            logger.error("no group message")
        if not use_llm:
            return self.check_no_llm(group_message)
        else:
            goal = list(group_message.keys())[0].goal
            prompt = self.PROMPT_TEMPLATE.format(goal=goal)
            for role, content in group_message:
                prompt += f"{role.profile}: {content}\n"
            prompt += "Return a dict with NO other texts:"

            consensus_ans = await self._aask(prompt)
            return consensus_ans

    # @staticmethod
    # def parse_dict(group_message, rsp) -> dict[Role, bool]:
    #     if not rsp.startswith("{"):
    #         logger.error(f"rsp:{rsp} can't be parsed")
    #     parsed_dict = json.loads(rsp)
    #     role_bool_dict = {}
    #     for role in group_message:
    #         if role.profile in parsed_dict:
    #             role_bool_dict[role] = parsed_dict[role.profile]
    #     for role, value in role_bool_dict.items():
    #         logger.debug(f"Role profile: {role.profile}, Value: {value}")
    #     return role_bool_dict


class ConsensusMaker(Role):
    """默认流程：
    1. 观察有无消息
    2. 初始化group_message
    3. CheckConsensus 返回dict[Role,bool]
    4. 从group_message中删除没有达成共识的角色消息
    5. 采用共识算法选出采用的角色消息，加入角色路径 (可选：利用llm生成共识信息，所有角色加入路径)
    6. 返回所选角色的消息
    注意： 默认返回的消息send_to:MESSAGE_ROUTE_TO_ALL
    """
    profile: str = "Consensus Maker"
    goal: str = "Receive output from other members of the group and help them to reach a consensus"
    constraints: str = ""
    group_message: dict[Role, str]
    next_group: str = MESSAGE_ROUTE_TO_ALL

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.set_actions([CheckConsensus, MakeConsensus])
        self._set_react_mode(react_mode="by_order")

    async def _act(self) -> Message:
        if self.group_message is None:
            logger.warning(f"group_message is none!")
        rsp = await self.todo.run(self.group_message)
        msg = None
        if isinstance(self.rc.todo, CheckConsensus):
            pattern = r'\{.*?\}'
            match = re.search(pattern, rsp)
            rsp = match.group(0) if match else None
            if not rsp:
                logger.error(f"rsp:{rsp} can't be parsed")
            roleprofile_dict = json.loads(rsp)
            role_dict = {}
            for role_profile, value in roleprofile_dict:
                role_dict[self.rc.env.roles[role_profile]] = value
            if all(value for value in role_dict.values()):
                msg = Message(
                        content=str(role_dict),
                        role=self.profile,
                        cause_by=self.rc.todo,
                        sent_from=self,
                    )
                self.rc.memory.add(msg)
            else:
                for role, value in role_dict.items():
                    if not value:
                        del self.group_message[role]
        elif isinstance(self.rc.todo, MakeConsensus):
            msg = Message(
                content=rsp,
                role=self.profile,
                cause_by=self.rc.to,
                sent_from=self,
                send_to={self.next_group}
            )
        assert not msg
        return msg

    async def react(self) -> Message:
        """Entry to one of three strategies by which Role reacts to the observed Message"""
        for m in self.rc.news:
            self.group_message[self.rc.env.roles[m.role]] = m.content
        if self.rc.react_mode == RoleReactMode.REACT:
            rsp = await self._react()
        elif self.rc.react_mode == RoleReactMode.BY_ORDER:
            rsp = await self._act_by_order()
        else:
            raise ValueError(f"Unsupported react mode: {self.rc.react_mode}")
        self._set_state(state=-1)  # current reaction is complete, reset state to -1 and todo back to None
        return rsp
