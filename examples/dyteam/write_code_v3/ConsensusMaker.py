# -*- coding:utf-8 -*-
from typing import Union

from metagpt.actions.action import Action
from metagpt.roles.role import Role, RoleReactMode
from metagpt.schema import Message
from metagpt.logs import logger
from metagpt.const import MESSAGE_ROUTE_TO_ALL
from sacrebleu import sentence_bleu
from route import add_to_route
import random
from utils import py_is_syntax_valid, calculate_nct


class MakeConsensus(Action):
    PROMPT_TEMPLATE: str = """
        All the members in the team have the same goal to {goal}.
        Your task is to create a consensus version that incorporates the best aspects of each
        Here are the results given by all members of the team:
        """
    PAIR_WISE_TEMPLATE: str = """
        Given a a function signature and its docstring:
        {query}
        Which of the following code is correct and more relevant to the requirement?
        {role1}: {content1}
        {role2}: {content2}
        Output {role1} or {role2} with NO other text.
        """
    name: str = "MakeConsensus"

    async def run(self, group_message: dict[Role, str], query: str = None, use_algorithm: bool = True) -> str:
        """给出每个Role的结果，返回共识"""
        if not group_message:
            logger.error(" no group message")
        selected_role = None
        if use_algorithm:
            try:
                # 共识算法
                NCTs = {}
                N = sum(r.n for r in group_message.keys())
                for r in group_message.keys():
                    NCTs[r] = calculate_nct(r.w, r.n, N)
                sorted_role = sorted(NCTs, key=NCTs.get)
                selected_role = sorted_role[0]
                for i in range(1, len(sorted_role)):
                    # 比较i和i+1
                    role1 = selected_role
                    role2 = sorted_role[i]
                    prompt = self.PAIR_WISE_TEMPLATE.format(query=query, role1=role1.profile, role2=role2.profile,
                                                            content1=group_message[role1],
                                                            content2=group_message[role2])
                    result = await self._aask(prompt)
                    if role2.profile == result or role2.profile in result:
                        selected_role = role2
                    elif role1.profile == result or role1.profile in result:
                        selected_role = role1
                    else:
                        logger.warning(f"{result} not in {role1.profile} and {role2.profile}")
                        selected_role = role2

                add_to_route(selected_role)
                return group_message[selected_role]
            except Exception as e:
                logger.warning(f"can't make consensus without llm because of {e}")
                logger.info(f"{selected_role.profile}")
                return random.choice(list(group_message.values()))

        else:
            for r in (group_message.keys()):
                add_to_route(r)
            goal = list(group_message.keys())[0].goal
            prompt = self.PROMPT_TEMPLATE.format(goal=goal)
            for role, content in group_message.items():
                prompt += f"{role.profile}:\n{content}\n"
            prompt += "\nReturn the consensus version with NO other texts,\nconsensus content:\n"

            consensus_content = await self._aask(prompt)
            return consensus_content


class CheckConsensus(Action):
    PROMPT_TEMPLATE: str = (
        "Your task is to check whether all answers given by different members are in agreement. "
        "All members have the same goal: {goal}.\n"
        "You need to give a dict to judge whether they make consensus, "
        "for example:{{\"Role1\":true, \"Role2\":false, \"Role3\":true, \"Role4\":true}} "
        "means Role1 ,Role3 and Role4 are in agreement while Role2 has different opinions.\n"
        "You need to find the roles that have the most agreements and set their attributes to true. "
        "For roles that do not reach consensus with others, set them to false.\n"
        "In other words, I hope to find the correct answer through this method.\n"
        "Here are the results given by all roles in the team:"
    )
    name: str = "CheckConsensus"

    async def run(self, group_message: dict[Role, str], use_llm: bool = False) -> Union[str, dict]:
        """给出每个Role的结果，查看是否达成共识"""
        if not group_message:
            logger.error("no group message")
        if not use_llm:
            consensus_ans = {}
            cmp_res = lambda x, y: sentence_bleu(x, [y], lowercase=True).score >= 0.9 * 100
            for role, python_code in group_message.items():
                # 检查语法错误
                execution_result = py_is_syntax_valid(code=python_code)
                if execution_result:
                    consensus_ans[role.profile] = True
                else:
                    consensus_ans[role.profile] = False
            logger.info(f"Checkconsensus:{consensus_ans}")
            return consensus_ans
        else:
            goal = list(group_message.keys())[0].goal
            prompt = self.PROMPT_TEMPLATE.format(goal=goal)
            for role, content in group_message.items():
                prompt += f"\n{role.profile}: {content}"
            prompt += "\nReturn a dict with NO other texts:"

            consensus_ans = await self._aask(prompt)
            return consensus_ans


class ConsensusMaker(Role):
    """默认流程：
    1. 观察有无消息
    2. 初始化group_message
    3. CheckConsensus (实际运行函数); 返回dict[Role,bool]
    4. 从group_message中删除没有达成共识的角色消息
    5. 采用共识算法选出采用的角色消息，加入角色路径 (可选：利用llm生成共识信息，所有角色加入路径)
    6. 返回所选角色的消息
    注意： 默认返回的消息send_to:MESSAGE_ROUTE_TO_ALL
    """
    profile: str = "Consensus Maker"
    goal: str = "Receive output from other members of the group and help them to reach a consensus"
    constraints: str = ""
    group_message: dict[str, str] = {}
    next_group: str = MESSAGE_ROUTE_TO_ALL

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.set_actions([CheckConsensus, MakeConsensus])
        self._set_react_mode(react_mode="by_order")

    async def _act(self) -> Message:
        if self.group_message is None:
            logger.warning(f"group_message is none!")
        role_message: dict[Role, str] = {}
        for role_profile, m in self.group_message.items():
            role_message[self.rc.env.roles[role_profile]] = m
        msg = None
        if isinstance(self.rc.todo, CheckConsensus):
            roleprofile_dict = await self.todo.run(role_message)
            for role, value in roleprofile_dict.items():
                if not value:
                    del self.group_message[role]
            msg = Message(
                content=str(roleprofile_dict),
                role=self.profile,
                cause_by=self.rc.todo,
                sent_from=self,
            )
        elif isinstance(self.rc.todo, MakeConsensus):
            rsp = await self.todo.run(role_message, query=self.rc.env.UserPrompt)
            if self.next_group == "Human":
                self.rc.env.FinalResult = rsp
                return msg
            msg = Message(
                content=rsp,
                role=self.profile,
                cause_by=self.rc.todo,
                sent_from=self,
                send_to={self.next_group}
            )
        assert msg
        return msg

    async def react(self) -> Message:
        """Entry to one of three strategies by which Role reacts to the observed Message"""
        for m in self.rc.news:
            self.group_message[m.role] = m.content
        if self.rc.react_mode == RoleReactMode.REACT:
            rsp = await self._react()
        elif self.rc.react_mode == RoleReactMode.BY_ORDER:
            rsp = await self._act_by_order()
        else:
            raise ValueError(f"Unsupported react mode: {self.rc.react_mode}")
        self._set_state(state=-1)  # current reaction is complete, reset state to -1 and todo back to None
        return rsp
