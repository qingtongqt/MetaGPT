# -*- coding:utf-8 -*-
from metagpt.roles.role import Role
from typing import List
from metagpt.utils.common import role_raise_decorator
from metagpt.logs import logger
from utils import calculate_nct


class Administrator:
    profile: str = "Administrator"
    group_list: list[list[Role]]

    def __init__(self, group_list: list[list[Role]]):
        self.group_list = group_list

    def run(self, deactivate_cnt: int = 1):
        for role_list in self.group_list:
            NCTs = {}
            N = sum(r.n for r in role_list)
            if N < 5:
                break
            for r in role_list:
                r.is_activate = True
                NCTs[r] = calculate_nct(r.w, r.n, N)
            sorted_role = sorted(NCTs, key=NCTs.get)
            for i in range(deactivate_cnt):
                sorted_role[i].is_activate = False
                logger.info(f"deactivate:{sorted_role[i].profile}")
        return
