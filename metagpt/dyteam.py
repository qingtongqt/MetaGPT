#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time    : 2023/5/12 00:30
@Author  : leoqing
@File    : team.py
"""

import warnings
from pathlib import Path
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from metagpt.actions import UserRequirement
from metagpt.config import CONFIG
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

    def __init__(self, **data: Any):
        super(DyTeam, self).__init__(**data)

    def serialize(self, stg_path: Path = None):
        stg_path = SERDESER_PATH.joinpath("dyteam") if stg_path is None else stg_path

        team_info_path = stg_path.joinpath("dyteam_info.json")
        write_json_file(team_info_path, self.model_dump(exclude={"env": True}))

        self.env.serialize(stg_path.joinpath("environment"))  # save environment alone

    @classmethod
    def deserialize(cls, stg_path: Path) -> "DyTeam":
        """stg_path = ./storage/dyteam"""
        # recover team_info
        team_info_path = stg_path.joinpath("dyteam_info.json")
        if not team_info_path.exists():
            raise FileNotFoundError(
                "recover storage meta file `dyteam_info.json` not exist, "
                "not to recover and please start a new project."
            )

        dyteam_info: dict = read_json_file(team_info_path)

        # recover environment
        environment = Environment.deserialize(stg_path=stg_path.joinpath("environment"))
        dyteam_info.update({"env": environment})
        dyteam = DyTeam(**dyteam_info)
        return dyteam

    # def run_project(self, idea, send_to: set[str] = None):
    #     """Run a project from publishing user requirement."""
    #     if send_to is None:
    #         send_to = {MESSAGE_ROUTE_TO_ALL}
    #     self.idea = idea
    #
    #     # Human requirement.
    #     self.env.publish_message(
    #         Message(role="Human", content=idea, cause_by=UserRequirement, send_to=send_to),
    #         peekable=False,
    #     )

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

    @serialize_decorator
    async def run(self, n_round=3, idea="", send_to="", auto_archive=True):
        """Run company until target round or no money"""
        if idea:
            self.run_project(idea=idea, send_to=send_to)

        while n_round > 0:
            # self._save()
            n_round -= 1
            logger.debug(f"max {n_round=} left.")
            self._check_balance()

            await self.env.run()
        self.env.archive(auto_archive)
        return self.env.history
