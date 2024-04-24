# -*- coding:utf-8 -*-
from metagpt.actions.action import Action
from metagpt.actions import UserRequirement
from metagpt.roles.role import Role
from metagpt.schema import Message
from metagpt.logs import logger
import re
from ConsensusMaker import CheckConsensus, MakeConsensus, ConsensusMaker
from TaskAssigner import Assign, TaskAssigner
from utils import add_api_call
import json


class WriteSolution(Action):
    PROMPT_TEMPLATE: str = """
    {question}
    Put your answer in the form (X) at the end of your response. (X) represents choice (A), (B), (C), or (D).
    """
    name: str = "WriteSolution"

    async def run(self, question: str):
        prompt = self.PROMPT_TEMPLATE.format(question=question)
        add_api_call()
        rsp = await self._aask(prompt)
        return rsp


class Iterate(Action):
    PROMPT_TEMPLATE: str = "Here is the question: {question}\n\n" \
                           "These are the solutions to the problem from other agents: {responses}\n\n" \
                           "Using the reasoning from other agents as additional advice with critical thinking, " \
                           "can you give an updated answer? Examine your solution and that other agents step by step." \
                           " Notice that their answers might be all wrong. " \
                           "Put your answer in the form (X) at the end of your response. " \
                           "(X) represents choice (A), (B), (C), or (D)."
    name: str = "Iterate"

    async def run(self, question: str, responses: str):
        prompt = self.PROMPT_TEMPLATE.format(question=question, responses=responses)
        add_api_call()
        rsp = await self._aask(prompt)
        return rsp


class SolutionGeneratorTaskAssigner(TaskAssigner):
    name: str = "Tom"
    profile: str = "Solution Generator Task Assigner"
    multi_assign: bool = True

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.set_actions([Assign])
        self._watch([UserRequirement])
        self.group_name = "Solution Generator"


class SolutionGeneratorConsensusMaker(ConsensusMaker):
    name: str = "Sam"
    profile: str = "Solution Generator Consensus Maker"
    goal: str = "Receive solution from other members of the group and help them to reach a consensus"
    group_name: str = "Solution Generator"
    next_group: str = "Human"

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.set_actions([CheckConsensus, MakeConsensus])
        self._watch([WriteSolution, Iterate])


class SolutionGenerator(Role):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.set_actions([WriteSolution, Iterate])
        self._watch([Assign, CheckConsensus])
        self._set_react_mode(react_mode="react")

    async def _react(self) -> Message:
        if self.latest_observed_msg.role == "Solution Generator Task Assigner":
            self._set_state(0)
        elif self.latest_observed_msg.role == "Solution Generator Consensus Maker":
            self._set_state(1)
        else:
            logger.error("bug")
        rsp = await self._act()
        return rsp

    async def _act(self) -> Message:
        todo = self.rc.todo

        if isinstance(todo, WriteSolution):
            question = self.latest_observed_msg.content
            # 执行生成解决方案的动作
            solution = await todo.run(question=question)
            msg = Message(role=self.profile, content=solution,
                          cause_by=todo, send_to="Solution Generator Consensus Maker")
            self.rc.memory.add(msg)
            return msg
        elif isinstance(todo, Iterate):
            group_message = self.get_memories(k=1)[0].content
            rsp = await todo.run(question=self.rc.env.UserPrompt, responses=group_message)
            msg = Message(role=self.profile, content=rsp,
                          cause_by=todo, send_to="Solution Generator Consensus Maker")
            self.rc.memory.add(msg)
            return msg


class Lawyer(SolutionGenerator):
    name: str = "James"
    profile: str = "Lawyer"
    desc: str = "You are a lawyer. You are good at law, politics, and history."



class Historian(SolutionGenerator):
    name: str = "Andy"
    profile: str = "Historian"
    desc: str = "You are a historian. You research and analyze cultural, economic, political, and social events " \
                "in the past, collect data from primary sources and use it to develop theories about " \
                "what happened during various periods of history."


class Mathematician(SolutionGenerator):
    name: str = "Mike"
    profile: str = "Mathematician"
    desc: str = "You are a mathematician. You are good at math games, arithmetic calculation, and long-term planning."


class Psychologist(SolutionGenerator):
    name: str = "Kevin"
    profile: str = "Psychologist"
    desc: str = "You are a psychologist. You are good at psychology, sociology, and philosophy. " \
                "You give people scientific suggestions that will make them feel better."


class Biologist(SolutionGenerator):
    name: str = "Susan"
    profile: str = "Biologist"
    desc: str = "You are a biologist with expertise in marine ecosystems. " \
                "You are adept at explaining biological concepts, analyzing ecological data, and providing insights " \
                "into marine biodiversity and conservation strategies"


class Engineer(SolutionGenerator):
    name: str = "Nick"
    profile: str = "Engineer"
    desc: str = "You are a engineer. You try to apply the scientific method and outlook " \
                "to the analysis and solution of engineering problems."
