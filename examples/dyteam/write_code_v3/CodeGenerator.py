# -*- coding:utf-8 -*-
from metagpt.actions.action import Action
from metagpt.actions import UserRequirement
from metagpt.roles.role import Role
from metagpt.schema import Message
from metagpt.logs import logger
import re
from ConsensusMaker import CheckConsensus, MakeConsensus, ConsensusMaker
from TaskAssigner import Assign, TaskAssigner
from Debugger import Debug
from utils import add_api_call
import json


class WriteCode(Action):
    PROMPT_TEMPLATE: str = """
    Here is a function signature and its docstring:
    =========
    {instruction}
    =========
    please give the full completion.
    Use ```python to put the completed Python code, including the necessary imports, in markdown quotes
    your code:
    """
    name: str = "WriteCode"

    async def run(self, instruction: str):
        prompt = self.PROMPT_TEMPLATE.format(instruction=instruction)
        add_api_call()
        rsp = await self._aask(prompt)
        code_text = WriteCode.parse_code(rsp)
        return code_text

    @staticmethod
    def parse_code(rsp):
        pattern = r"```python(.*)```"
        match = re.search(pattern, rsp, re.DOTALL)
        code_text = match.group(1) if match else rsp
        return code_text


class ReWriteCode(Action):
    PROMPT_TEMPLATE: str = """
    Here is a function signature:
    {instruction}
    ==========
    And your previews implementation:
    {prevcode}
    ==========
    This implementation fails the test.
    the Debugger gives you some feedback:
    {debug}
    Based on your previews implementation and the debug message, rewrite the function.
    Please follow the template by repeating the function signature and complete the new implementation
    Use ```python to put the completed Python code, including the necessary imports, in markdown quotes
    your code:
    """
    name: str = "ReWriteCode"

    async def run(self, instruction: str, prevcode: str, debug: str):
        prompt = self.PROMPT_TEMPLATE.format(instruction=instruction, prevcode=prevcode, debug=debug)
        add_api_call()
        rsp = await self._aask(prompt)
        code_text = WriteCode.parse_code(rsp)
        return code_text

    @staticmethod
    def parse_code(rsp):
        pattern = r"```python(.*)```"
        match = re.search(pattern, rsp, re.DOTALL)
        code_text = match.group(1) if match else rsp
        return code_text


class Iterate(Action):
    PROMPT_TEMPLATE: str = """
    Here is a function signature:
    {instruction}
    ==========
    And here are other agents' implementation:
    {group_message}
    ==========
    Please follow the template by repeating the function signature and complete the new implementation
    If no changes are needed, simply rewrite the implementation in the Python code block.
    Use ```python to put the completed Python code, including the necessary imports, in markdown quotes
    your code:
    """
    name: str = "Iterate"

    async def run(self, instruction: str, group_message: str):
        prompt = self.PROMPT_TEMPLATE.format(instruction=instruction, group_message=group_message)
        add_api_call()
        rsp = await self._aask(prompt)
        code_text = WriteCode.parse_code(rsp)
        return code_text

    @staticmethod
    def parse_code(rsp):
        pattern = r"```python(.*)```"
        match = re.search(pattern, rsp, re.DOTALL)
        code_text = match.group(1) if match else rsp
        return code_text


class CodeGeneratorTaskAssigner(TaskAssigner):
    name: str = "Tom"
    profile: str = "Code Generator Task Assigner"

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.set_actions([Assign])
        self._watch([UserRequirement])
        self.group_name = "Code Generator"


class CodeGeneratorConsensusMaker(ConsensusMaker):
    name: str = "Sam"
    profile: str = "Code Generator Consensus Maker"
    goal: str = "Receive code from other members of the Code Generator group and help them to reach a consensus"
    group_name: str = "Code Generator"
    next_group: str = "Debugger"

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.set_actions([CheckConsensus, MakeConsensus])
        self._watch([WriteCode, ReWriteCode, Iterate])


class CodeGenerator(Role):
    goal: str = "write code"
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.set_actions([WriteCode, ReWriteCode, Iterate])
        self._watch([Assign, Debug, CheckConsensus])
        self._set_react_mode(react_mode="react")

    async def _react(self) -> Message:
        if self.latest_observed_msg.role == "Code Generator Task Assigner":
            self._set_state(0)
        elif self.latest_observed_msg.role == "Debugger":
            self._set_state(1)
        elif self.latest_observed_msg.role == "Code Generator Consensus Maker":
            self._set_state(2)
        else:
            logger.error("bug")
        rsp = await self._act()
        return rsp

    async def _act(self) -> Message:
        todo = self.rc.todo

        if isinstance(todo, WriteCode):
            instruction = self.latest_observed_msg.content
            # 执行写代码的动作
            code = await todo.run(instruction=instruction)
            msg = Message(role=self.profile, content=code, cause_by=todo, send_to="Code Generator Consensus Maker")
            self.rc.memory.add(msg)
            return msg
        elif isinstance(todo, ReWriteCode):
            content = json.loads(self.latest_observed_msg.content)
            debug = content["result"]
            prevcode = content["code"]
            code = await todo.run(instruction=self.rc.env.UserPrompt, prevcode=prevcode, debug=debug)
            self.rc.env.FinalResult = code
            msg = Message(role=self.profile, content=code, cause_by=todo, send_to="Code Generator Consensus Maker")
            return msg
        elif isinstance(todo, Iterate):
            group_message = self.get_memories(k=1)[0].content
            code = await todo.run(instruction=self.rc.env.UserPrompt, group_message=group_message)
            msg = Message(role=self.profile, content=code, cause_by=todo, send_to="Code Generator Consensus Maker")
            self.rc.memory.add(msg)
            return msg


class AlgorithmDeveloper(CodeGenerator):
    name: str = "James"
    profile: str = "Algorithm Developer"
    desc: str = ("You are an algorithm developer. "
                 "You are good at developing and utilizing algorithms to solve problems.")



class ComputerScientist(CodeGenerator):
    name: str = "Andy"
    profile: str = "Computer Scientist"
    desc: str = ("You are a computer scientist. "
                 "You are good at writing high performance code and recognizing corner cases while solve real problems.")


class Programmer(CodeGenerator):
    name: str = "Mike"
    profile: str = "Programmer"
    desc: str = ("You are an intelligent programmer. "
                 "You must complete the python function given to you by the user. ")


class SoftwareArchitect(CodeGenerator):
    name: str = "Kevin"
    profile: str = "Software Architect"
    desc: str = ("You are a software architect, skilled in designing and structuring code for scalability, "
                 "maintainability, and robustness. Your responses should focus on best practices in software design.")


class CodeArtist(CodeGenerator):
    name: str = "Susan"
    profile: str = "Code Artist"
    desc: str = ("You are a coding artist. "
                 "You write Python code that is not only functional but also aesthetically pleasing and creative. "
                 "Your goal is to make the code an art form while maintaining its utility.")

class Mathematician(CodeGenerator):
    name: str = "Nick"
    profile: str = "Mathematician"
    desc: str = "You are a mathematician. You are good at math games, arithmetic calculation, and long-term planning."
