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

    async def run(self, instruction: str):
        prompt = self.PROMPT_TEMPLATE.format(instruction=instruction)
        rsp = await self._aask(prompt)
        code_text = WriteCode.parse_code(rsp)
        return code_text

    @staticmethod
    def parse_code(rsp):
        pattern = r"```python(.*)```"
        match = re.search(pattern, rsp, re.DOTALL)
        code_text = match.group(1) if match else rsp
        return code_text


class CodeWriter(Role):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.set_actions([WriteCode])
        # TODO self._watch()

    async def _act(self) -> Message:
        # 解析接收到的消息中的指令
        instruction = self.get_memories(k=1)
        # 执行写代码的动作
        code = await self.todo.run(instruction)
        msg = Message(role=self.name, content=code, cause_by=WriteCode, send_to="ConsensusMaker")
        return msg


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
