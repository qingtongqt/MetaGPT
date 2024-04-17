# -*- coding:utf-8 -*-
from typing import Tuple

from metagpt.actions.action import Action
from metagpt.actions import UserRequirement
from metagpt.roles.role import Role
from metagpt.schema import Message
from metagpt.logs import logger
from utils import calculate_nct
import random


class Assign(Action):
    name: str = "Assign"

    async def run(self, instruction: str) -> str:
        return instruction


class TaskAssigner(Role):
    name: str = "Tom"
    profile: str = "Task Assigner"
    constraints: str = ""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.set_actions([Assign])
        self._watch([UserRequirement])

    async def _act(self) -> Message:
        # 解析接收到的UserRequirement
        instruction = self.get_memories(k=1)[0].content
        code_group = []
        for role, addrs in self.rc.env.member_addrs.items():
            if "Code Generator" in addrs:
                if role.is_activate:
                    code_group.append(role)
        NCTs = {}
        N = sum(r.n for r in code_group)
        for role in code_group:
            NCTs[role] = calculate_nct(role.w, role.n, N)

        sorted_role = sorted(NCTs, key=NCTs.get)
        logger.info(f"sorted role:{sorted_role}")
        selected_role = sorted_role[-1]
        msg = Message(role=self.profile, content=instruction, cause_by=self.rc.todo,
                      sent_from=self, send_to=selected_role.profile)
        return msg
