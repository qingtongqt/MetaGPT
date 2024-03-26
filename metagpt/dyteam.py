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
from team import Team
from metagpt.utils.common import (
    NoMoneyException,
    read_json_file,
    serialize_decorator,
    write_json_file,
)


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
    # idea: str = Field(default="")
    dynamic_group: dict[str, set[Role]] = None

    def __init__(self, context: Context = None, **data: Any):
        super(DyTeam, self).__init__(context=context, **data)

    def serialize(self, stg_path: Path = None):
        stg_path = SERDESER_PATH.joinpath("dyteam") if stg_path is None else stg_path

        dyteam_info_path = stg_path.joinpath("dyteam_info.json")
        write_json_file(dyteam_info_path, self.model_dump(exclude={"env": True}))

        self.env.serialize(stg_path.joinpath("environment"))  # save environment alone

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

    def run_project(self, idea, send_to: str = ""):
        """Run a project from publishing user requirement."""
        self.idea = idea

        # Human requirement.
        self.env.publish_message(
            Message(role="Human", content=idea, cause_by=UserRequirement, send_to=send_to or MESSAGE_ROUTE_TO_ALL),
            peekable=False,
        )

    def _save(self):
        logger.info(self.model_dump_json())

    def check_consensus(self) -> dict[str, bool]:
        if not self.dynamic_group:
            return
        new_dict = {key: False for key in self.dynamic_group.keys()}
        for group_name, roles in self.dynamic_group.items():
            # 判断在dynamic_group中的每个role，最近一条消息是不是自己产生的
            # 如果是其他role发过来的则不需check_consensus
            if not all(role.rc.memory.get(1)[0].sent_from == role for role in roles):
                continue

            pred_solutions = [role.rc.memory.get(1)[0].content for role in roles]
            pred_answers = []
            for pred_solution in pred_solutions:
                # pred_answer = extract_math_answer(pred_solution)
                pred_answer = 'test'
                if pred_answer:
                    pred_answers.append(pred_answer)

            if len(pred_answers) == 0:
                logger.warning("extract_math_answer fail")
                continue

            def most_frequent(List):
                counter = 0
                num = List[0]

                for i in List:
                    # current_frequency = sum(is_equiv(i, item) for item in List)
                    current_frequency = sum(item for item in List)
                    if current_frequency > counter:
                        counter = current_frequency
                        num = i

                return num, counter

            consensus_answer, counter = most_frequent(pred_answers)
            if counter > math.floor(2 / 3 * len(roles)):
                print("Consensus answer: {}".format(consensus_answer))
                new_dict[group_name] = True

        return new_dict

    @serialize_decorator
    async def run(self, n_round=3, idea="", send_to="", dynamic_group: dict[str, set[Role]] = None, auto_archive=True):
        """Run company until target round or no money or reach consensus

        Args:
            n_round: number of iterations
            idea: start message
            dynamic_group: a set of roles having the same purpose with the dynamic structure

            dynamic_group = {
                "group1": {"Role1", "Role2"},
                "group2": {"Role3", "Role4"},
                "group3": {"Role5", "Role6"}
            }

            send_to: the message sent to during initialization
            auto_archive: related to git_repo
        """

        if dynamic_group:
            self.dynamic_group = dynamic_group
            # 判断不同动态组中是否有重叠
            all_dynamic_roles = set()
            for roles in self.dynamic_group.values():
                if roles & all_dynamic_roles:
                    raise Exception(f"Intersection found in multi dynamic_group")
                all_dynamic_roles.update(roles)

            # 在环境中member_addrs变量添加group_name
            for group_name, roles in self.dynamic_group.items():
                logger.info(f"{group_name}:" + ",".join(role.name for role in roles))
                for role in roles:
                    role.is_dynamic = True
                    self.env.set_addresses(role, group_name)
                    # TODO 加入是否是consensus role的判断

        if idea:
            self.run_project(idea=idea, send_to=send_to)

        while n_round > 0:
            # self._save()
            n_round -= 1
            logger.debug(f"max {n_round=} left.")
            self._check_balance()
            if dynamic_group:
                consensus_dict = self.check_consensus()
                if all(consensus_dict.values()):
                    break

            await self.env.run()
        self.env.archive(auto_archive)
        return self.env.history
