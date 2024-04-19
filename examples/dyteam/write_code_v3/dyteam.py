#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time    : 2023/12/12 00:30
@Author  : leoqing
@File    : team.py
"""

import warnings
from pathlib import Path
from typing import Any
import math

from pydantic import BaseModel, ConfigDict, Field

from metagpt.actions import UserRequirement
from metagpt.context import Context
from metagpt.const import MESSAGE_ROUTE_TO_ALL, SERDESER_PATH
from metagpt.environment import Environment
from metagpt.logs import logger
from metagpt.roles import Role
from metagpt.schema import Message
from metagpt.team import Team
from metagpt.utils.common import (
    NoMoneyException,
    read_json_file,
    serialize_decorator,
    write_json_file,
)
from Administrator import Administrator

from Administrator import Administrator

# from metagpt.utils.dynamic_common import (
#     extract_math_answer,
#     is_equiv,
# )


class DyTeam(Team):
    """
    DyTeam: Possesses one or more roles (agents), dynamic communication, and an env for instant messaging,
    dedicated to env any dynamic multi-agent activity, such as agent optimization based on specific task.
    """

    # model_config = ConfigDict(arbitrary_types_allowed=True)
    #
    # env: Environment = Field(default_factory=Environment)
    # investment: float = Field(default=10.0)
    administrator: Administrator

    def __init__(self, context: Context = None, **data: Any):
        super(DyTeam, self).__init__(context=context, **data)

    def serialize(self, stg_path: Path = None):
        stg_path = SERDESER_PATH.joinpath("dyteam") if stg_path is None else stg_path

        dyteam_info_path = stg_path.joinpath("dyteam.json")
        write_json_file(dyteam_info_path, self.model_dump())

    @classmethod
    def deserialize(cls, stg_path: Path, context: Context = None) -> "dyTeam":
        """stg_path = ./storage/dyteam"""
        # recover team_info
        team_info_path = stg_path.joinpath("dyteam.json")
        if not team_info_path.exists():
            raise FileNotFoundError(
                "recover storage meta file `dyteam.json` not exist, " "not to recover and please start a new project."
            )

        team_info: dict = read_json_file(team_info_path)
        ctx = context or Context()
        dyteam = DyTeam(**team_info, context=ctx)
        return dyteam

    @serialize_decorator
    async def run(self, n_round=5, idea="", send_to="", auto_archive=True):
        """Run company until target round or no money"""
        if idea:
            self.run_project(idea=idea, send_to=send_to)

        if self.administrator:
            self.administrator.run()

        while n_round > 0:
            # self._save()
            n_round -= 1
            logger.debug(f"max {n_round=} left.")
            self._check_balance()

            await self.env.run()
            if self.env.is_idle:
                break
            if n_round == 0:
                for r in self.env.roles.values():
                    r.rc.msg_buffer.pop_all()
        self.env.archive(auto_archive)
        return self.env.FinalResult

    # @serialize_decorator
    # async def run(self, n_round=3, idea="", send_to="", dynamic_group: dict[str, set[Role]] = None, auto_archive=True):
    #     """Run company until target round or no money or reach consensus
    #
    #     Args:
    #         n_round: number of iterations
    #         idea: start message
    #         dynamic_group: a set of roles having the same purpose with the dynamic structure
    #
    #         dynamic_group = {
    #             "group1": {"Role1", "Role2"},
    #             "group2": {"Role3", "Role4"},
    #             "group3": {"Role5", "Role6"}
    #         }
    #
    #         send_to: the message sent to during initialization
    #         auto_archive: related to git_repo
    #     """
    #
    #     if dynamic_group:
    #         self.dynamic_group = dynamic_group
    #         # 判断不同动态组中是否有重叠
    #         all_dynamic_roles = set()
    #         for roles in self.dynamic_group.values():
    #             if roles & all_dynamic_roles:
    #                 raise Exception(f"Intersection found in multi dynamic_group")
    #             all_dynamic_roles.update(roles)
    #
    #         # 在环境中member_addrs变量添加group_name
    #         for group_name, roles in self.dynamic_group.items():
    #             logger.info(f"{group_name}:" + ",".join(role.name for role in roles))
    #             for role in roles:
    #                 role.is_dynamic = True
    #                 self.env.set_addresses(role, group_name)
    #                 # TODO 加入是否是consensus role的判断
    #
    #     if idea:
    #         self.run_project(idea=idea, send_to=send_to)
    #
    #     while n_round > 0:
    #         # self._save()
    #         n_round -= 1
    #         logger.debug(f"max {n_round=} left.")
    #         self._check_balance()
    #         if dynamic_group:
    #             consensus_dict = self.check_consensus()
    #             if all(consensus_dict.values()):
    #                 break
    #
    #         await self.env.run()
    #     self.env.archive(auto_archive)
    #     return self.env.history
