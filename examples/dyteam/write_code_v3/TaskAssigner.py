# -*- coding:utf-8 -*-
from typing import Tuple

from metagpt.actions.action import Action
from metagpt.actions import UserRequirement
from metagpt.roles.role import Role
from metagpt.schema import Message
from metagpt.logs import logger
from utils import calculate_nct
import numpy as np


class Assign(Action):
    name: str = "Assign"

    def run(self, code_group: list[Role]) -> str:
        NCTs = {}
        N = sum(r.n for r in code_group)
        for role in code_group:
            NCTs[role] = calculate_nct(role.w, role.n, N)
        values = np.array(list(NCTs.values()))
        softmax_values = np.exp(values) / np.sum(np.exp(values))
        softmax_dict = {role: float(value) for role, value in zip(NCTs.keys(), softmax_values)}
        # softmax归一化后依概率选择role
        selected_role = np.random.choice(list(softmax_dict.keys()), p=list(softmax_dict.values()))
        return selected_role.profile


class TaskAssigner(Role):
    profile: str = "Task Assigner"
    constraints: str = ""
    group_name: str = ""
    multi_assign: bool = False

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.set_actions([Assign])
        # 继承自该类需要自行重写init函数，修改_watch和group_name
        self._watch([UserRequirement])

    async def _act(self) -> Message:
        # 解析接收到的UserRequirement
        instruction = self.get_memories(k=1)[0].content
        if self.multi_assign:
            msg = Message(role=self.profile, content=instruction, cause_by=self.rc.todo,
                          sent_from=self, send_to=self.group_name)
        else:
            code_group = []
            for role, addrs in self.rc.env.member_addrs.items():
                if self.group_name in addrs and role.is_activate:
                    code_group.append(role)

            selected_role = self.todo.run(code_group)

            logger.info(f"select role:{selected_role}")
            msg = Message(role=self.profile, content=instruction, cause_by=self.rc.todo,
                          sent_from=self, send_to=selected_role)
        return msg
