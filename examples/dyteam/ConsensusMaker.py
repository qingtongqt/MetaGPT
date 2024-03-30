# -*- coding:utf-8 -*-
from metagpt.actions.action import Action
from metagpt.roles.role import Role
from metagpt.schema import Message
from metagpt.logs import logger
from abc import abstractmethod
import json
import math
import numpy as np
from route import add_to_route
import random


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
        "for example:{\"Role1\":True, \"Role2\":False, \"Role3\":True, \"Role4\":True} "
        "means Role1 ,Role3 and Role4 are in agreement while Role2 has different opinions.\n"
        "You need to find the role that reaches the most consensus and set the corresponding item to True, "
        "and the role that does not reach consensus set it to False.\n"
        "Here are the results given by all members of the team:"
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
            prompt += "\nReturn a dict with NO other texts:"

            consensus_ans = await self._aask(prompt)
            return consensus_ans

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
        self.set_actions([CheckConsensus, MakeConsensus])
        self._set_react_mode(react_mode="by_order")

    async def _act(self, group_message=None):
        if group_message is None:
            logger.warning(f"group_message is none!")
        rsp = await self.todo.run(group_message)
        if isinstance(self.rc.todo, CheckConsensus):
            if not rsp.startwith("{"):
                logger.error(f"rsp:{rsp} can't be parsed")
            role_dict = json.loads(rsp)
            rsp = {}
            for role_profile, value in role_dict:
                rsp[self.rc.env.roles[role_profile]] = value
        return rsp

    async def _act_by_order(self) -> Message:
        start_idx = self.rc.state if self.rc.state >= 0 else 0  # action to run from recovered state
        rsp = Message(content="No actions taken yet")  # return default message if actions=[]
        group_message = {}
        for m in self.rc.news:
            group_message[self.rc.env.roles[m.role]] = m.content
        for i in range(start_idx, len(self.states)):
            self._set_state(i)
            rsp = await self._act(group_message=group_message)
            # CheckConsensus时
            if i == 0:
                # 达成共识，字典全为True
                assert isinstance(rsp, dict)
                if all(value for value in rsp.values()):
                    add_to_route(self.rc.env.roles[self.rc.news[-1].role])
                    return Message(
                        content=self.latest_observed_msg.content,
                        role=self._setting,
                        cause_by=self.rc.todo,
                        sent_from=self,
                    )
                else:
                    # 删除未达成共识的角色
                    for role, value in rsp.items():
                        if not value:
                            del group_message[role]
        # MakeConsensus需返回Message
        assert isinstance(rsp, Message)
        return rsp  # return output from the last action
