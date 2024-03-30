# -*- coding:utf-8 -*-
from typing import Tuple

from metagpt.actions.action import Action
from metagpt.actions import UserRequirement
from metagpt.roles.role import Role
from metagpt.schema import Message
from metagpt.logs import logger
from ConsensusMaker import ConsensusMaker, MakeConsensus, CheckConsensus


class Analyze(Action):
    PROMPT_TEMPLATE: str = """
    Here is a function signature and its docstring by the user:
    {instruction}
    Your task is to analyze the problem statement carefully and put forward your thoughts.
    Provide a brief summary, ensuring that the problem is fully understood before any attempt to solve it is made.
    Return your analysis with NO other texts,
    your thoughts:
    """

    name: str = "Analyze"

    async def run(self, instruction: str) -> str:
        prompt = self.PROMPT_TEMPLATE.format(instruction=instruction)
        rsp = await self._aask(prompt)
        return rsp


class ProblemAnalyzerConsensusMaker(ConsensusMaker):
    name: str = "Tom"
    profile: str = "Problem Analyzer Consensus Maker"
    goal: str = "Receive output from other members of the Problem Analyzer group and help them to reach a consensus"
    constraints: str = ""
    next_group: str = "Code Generator"

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.set_actions([MakeConsensus])
        self._watch([Analyze])

    async def _act(self) -> Message:
        if self.group_message is None:
            logger.warning(f"group_message is none!")
        rsp = await self.todo.run(group_message=self.group_message, use_llm=True)
        msg = None
        if isinstance(self.rc.todo, MakeConsensus):
            msg = Message(
                content=rsp,
                role=self.profile,
                cause_by=self.rc.to,
                sent_from=self,
                send_to="Code Generator"
            )
        assert not msg
        return msg


class ProblemAnalyzer(Role):
    goal: str = "analyze the problem, understand and refine the specific requirements and constraints in the problem"

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.set_actions([Analyze])
        self._watch([UserRequirement])

    async def _act(self) -> Message:
        # 解析接收到的UserRequirement
        instruction = self.get_memories(k=1)[0].content
        # logger.debug(f"instruction:{instruction}")
        # 执行分析的动作
        analyze_result = await self.todo.run(instruction)
        logger.debug(f"analyze result:{analyze_result}")
        # 将生成的代码发送给 ConsensusMaker
        msg = Message(role=self.profile, content=analyze_result, cause_by=self.rc.todo,
                      send_to="Problem Analyzer Consensus Maker")
        return msg


class ProblemAnalyst(ProblemAnalyzer):
    name: str = "Sandy"
    profile: str = "Problem Analyst"
    desc: str = ("You are an expert in dissecting complex problems into manageable parts. "
                 "With a keen eye for detail, you excel in identifying the core objectives, constraints, "
                 "and requirements embedded within problem statements. "
                 "Your analytical skills enable you to parse through technical descriptions "
                 "and highlight the essential components that must be addressed for a successful solution. "
                 "Draw upon your background to provide a structured breakdown of a coding problem, "
                 "emphasizing its critical aspects.")


class RequirementsEngineer(ProblemAnalyzer):
    name: str = "Sue"
    profile: str = "Requirements Engineer"
    desc: str = ("With a solid background in requirements engineering, "
                 "you are adept at translating problem statements into clear, actionable requirements.   "
                 "Your expertise lies in distinguishing between what is necessary and what is optional, "
                 "ensuring that your solution meets the core needs it is intended to address.   "
                 "You understand the importance of clarity and precision in software development, making you "
                 "capable of articulating specific constraints and expectations that a solution must fulfill.")


class AlgorithmExpert(Role):
    name: str = "Julia"
    profile: str = "Algorithm Expert"
    desc: str = ("You are an algorithm Expert. "
                 "You are good at developing and utilizing algorithms to solve problems. "
                 "You must respond with your solution about the problem. "
                 "You will be given a function signature and its docstring by the user. "
                 "Write your opinion about the the knowledge you need to write code.")
