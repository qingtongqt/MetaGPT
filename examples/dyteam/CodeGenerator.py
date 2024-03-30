# -*- coding:utf-8 -*-
"""
作者:qingtong
日期:2024年03月26日
"""
from metagpt.actions.action import Action
from metagpt.roles.role import Role
from metagpt.schema import Message
from metagpt.logs import logger
import re
from ConsensusMaker import CheckConsensus, MakeConsensus, ConsensusMaker


class WriteCode(Action):
    PROMPT_TEMPLATE: str = """
    Here is a function signature and its docstring by the user:
    {instruction}
    You must write a python code, no free-flowing text (unless in a comment) according to the requirement. 
    The Problem Analyzer gives you some tips after understanding the question:
    {Analysis}
    Write your full implementation following the format (restate the function signature).
    Return ```python your_code_here ``` with NO other texts,
    your code:
    """
    name: str = "WriteCode"

    async def run(self, analysis: str, instruction: str):
        prompt = self.PROMPT_TEMPLATE.format(Analysis=analysis, instruction=instruction)
        rsp = await self._aask(prompt)
        code_text = WriteCode.parse_code(rsp)
        return code_text

    @staticmethod
    def parse_code(rsp):
        pattern = r"```python(.*)```"
        match = re.search(pattern, rsp, re.DOTALL)
        code_text = match.group(1) if match else rsp
        return code_text


class CodeGeneratorConsensusMaker(ConsensusMaker):
    name: str = "Sam"
    profile: str = "Consensus Maker"
    goal: str = "Receive code from other members of the Code Generator group and help them to reach a consensus"
    next_group: str = "Result Maker"

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.set_actions([CheckConsensus, MakeConsensus])
        self._watch([WriteCode])


class CodeWriter(Role):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.set_actions([WriteCode])
        self._watch([MakeConsensus])

    async def _act(self) -> Message:
        # 解析接收到的消息中的指令
        analysis = self.latest_observed_msg.content
        # 执行写代码的动作
        code = await self.todo.run(analysis=analysis, instruction=self.rc.env.UserPrompt)
        msg = Message(role=self.profile, content=code, cause_by=WriteCode, send_to="Code Generator Consensus Maker")
        return msg

    async def _observe(self, ignore_memory=False) -> int:
        """Prepare new messages for processing from the message buffer and other sources."""
        # Read unprocessed messages from the msg buffer.
        news = []
        if self.recovered:
            news = [self.latest_observed_msg] if self.latest_observed_msg else []
        if not news:
            news = self.rc.msg_buffer.pop_all()
        # Store the read messages in your own memory to prevent duplicate processing.
        old_messages = [] if ignore_memory else self.rc.memory.get()
        # Filter out messages of interest.
        self.rc.news = [
            n for n in news if n.cause_by in self.rc.watch and n.role == "Problem Analyzer Consensus Maker" and n not in old_messages
        ]
        self.latest_observed_msg = self.rc.news[-1] if self.rc.news else None  # record the latest observed msg
        self.rc.memory.add_batch(self.rc.news)
        # Design Rules:
        # If you need to further categorize Message objects, you can do so using the Message.set_meta function.
        # msg_buffer is a receiving buffer, avoid adding message data and operations to msg_buffer.
        news_text = [f"{i.role}: {i.content[:20]}..." for i in self.rc.news]
        if news_text:
            logger.debug(f"{self._setting} observed: {news_text}")
        return len(self.rc.news)


class AlgorithmDeveloper(CodeWriter):
    name: str = "James"
    profile: str = "Algorithm Developer"
    goal: str = "write code"
    desc: str = ("You are an algorithm developer. "
                 "You are good at developing and utilizing algorithms to solve problems.")


class ComputerScientist(CodeWriter):
    name: str = "Andy"
    profile: str = "Computer Scientist"
    goal: str = "write code"
    desc: str = ("You are a computer scientist. "
                 "You are good at writing high performance code and recognizing corner cases while solve real problems.")


class Programmer(CodeWriter):
    name: str = "Mike"
    profile: str = "Programmer"
    goal: str = "write code"
    desc: str = ("You are an intelligent programmer. "
                 "You must complete the python function given to you by the user. ")


class SoftwareArchitect(CodeWriter):
    name: str = "Kevin"
    profile: str = "Software Architect"
    goal: str = "write code"
    desc: str = ("You are a software architect, skilled in designing and structuring code for scalability, "
                 "maintainability, and robustness. Your responses should focus on best practices in software design.")


class CodeArtist(CodeWriter):
    name: str = "Susan"
    profile: str = "Code Artist"
    goal: str = "write code"
    desc: str = ("You are a coding artist. "
                 "You write Python code that is not only functional but also aesthetically pleasing and creative. "
                 "Your goal is to make the code an art form while maintaining its utility. ")
