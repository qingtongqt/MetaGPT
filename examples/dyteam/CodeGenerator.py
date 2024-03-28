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
    Write a python function that can {instruction} and provide two runnnable test cases.
    Return ```python your_code_here ``` with NO other texts,
    your code:
    """
    name: str = "SimpleWriteCode"

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


class AlgorithmDeveloper(Role):
    name: str = "Bob"
    profile: str = "Algorithm Developer"
    goal: str = "write code"
    desc: str = ("You are an algorithm developer. "
                 "You are good at developing and utilizing algorithms to solve problems. "
                 "You must respond with python code, no free-flowing text (unless in a comment). "
                 "You will be given a function signature and its docstring by the user. "
                 "Write your full implementation following the format (restate the function signature).")


class ComputerScientist(Role):
    name: str = "Bob"
    profile: str = "Computer Scientist"
    goal: str = "write code"
    desc: str = ("You are a computer scientist. "
                 "You are good at writing high performance code and recognizing corner cases while solve real problems."
                 " You must respond with python code, no free-flowing text (unless in a comment). "
                 "You will be given a function signature and its docstring by the user. "
                 "Write your full implementation following the format (restate the function signature).")


class Programmer(Role):
    name: str = "Bob"
    profile: str = "Programmer"
    goal: str = "write code"
    desc: str = ("You are an intelligent programmer. "
                 "You must complete the python function given to you by the user. "
                 "And you must follow the format they present when giving your answer! "
                 "You can only respond with comments and actual code, no free-flowing text (unless in a comment).")


class SoftwareArchitect(Role):
    name: str = "Bob"
    profile: str = "Software Architect"
    goal: str = "write code"
    desc: str = ("You are a software architect, skilled in designing and structuring code for scalability, "
                 "maintainability, and robustness. Your responses should focus on best practices in software design."
                 " You will be given a function signature and its docstring by the user. "
                 "Write your full implementation following the format (restate the function signature).")


class CodeArtist(Role):
    name: str = "Bob"
    profile: str = "Code Artist"
    goal: str = "write code"
    desc: str = ("You are a coding artist. "
                 "You write Python code that is not only functional but also aesthetically pleasing and creative. "
                 "Your goal is to make the code an art form while maintaining its utility. "
                 "You will be given a function signature and its docstring by the user. "
                 "Write your full implementation following the format (restate the function signature).")


class CodeWriter(Role):
    name: str = "Bob"
    profile: str = "Architect"
    goal: str = "design a concise, usable, complete software system"
    constraints: str = (
        "make sure the architecture is simple enough and use  appropriate open source "
        "libraries. Use same language as user requirement"
    )

    async def run(self, with_message=None) -> None:
        if with_message:
            # 解析接收到的消息中的指令
            instruction = with_message.content
            # 执行写代码的动作
            code_action = WriteCode()
            code = await code_action.run(instruction)
            # 将生成的代码发送给 ConsensusMaker
            self.publish_message(
                Message(role=self.name, content=code, cause_by=WriteCode, send_to="ConsensusMaker"),
            )


