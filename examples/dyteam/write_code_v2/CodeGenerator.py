# -*- coding:utf-8 -*-
from metagpt.actions.action import Action
from metagpt.roles.role import Role
from metagpt.schema import Message
from metagpt.logs import logger
import re
from ConsensusMaker import CheckConsensus, MakeConsensus, ConsensusMaker
from ProblemAnalyzer import Analyze
from Debugger import Debug
import ast
from typing import Any


def get_return_type(source: str) -> Any:
    # 解析源代码为抽象语法树
    tree = ast.parse(source)

    # 遍历树中的所有节点
    for node in ast.walk(tree):
        # 检查节点是否为函数定义
        if isinstance(node, ast.FunctionDef):
            # 获取并返回函数的返回类型注解
            if node.returns:
                # 返回类型信息（如果存在）
                return ast.unparse(node.returns)


class WriteCode(Action):
    PROMPT_TEMPLATE: str = """
    Here is a function signature and its docstring:
    =========
    {instruction}
    =========
    You must write a python code, no free-flowing text (unless in a comment) according to the requirement. 
    The Problem Analyzer gives you some tips after understanding the question:
    =========
    {Analysis}
    =========
    When the function signature does not specify the input range, please do not throw an error for empty input or other unreasonable input, and please also provide a return value.
    Please follow the template by repeating the original function, then writing the completion..
    Use ```python to put the completed Python code, including the necessary imports, in markdown quotes
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

class ReWriteCode(Action):
    PROMPT_TEMPLATE: str = """
    Here is a function signature and your previews completion:
    {instruction}
    {prevcode}
    the Debugger gives you some feedback:
    {debug}
    Based on your previes completion and the debug message, rewrite the function.
    When the function signature does not specify the input range, please do not throw an error for empty input or other unreasonable input, and please also provide a return value.
    Use ```python to put the completed Python code, including the necessary imports, in markdown quotes
    your code:
    """
    name: str = "ReWriteCode"

    async def run(self, instruction: str, prevcode: str, debug: str):
        prompt = self.PROMPT_TEMPLATE.format(instruction=instruction, prevcode=prevcode, debug=debug)
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
    profile: str = "Code Generator Consensus Maker"
    goal: str = "Receive code from other members of the Code Generator group and help them to reach a consensus"
    next_group: str = "Debugger"

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.set_actions([CheckConsensus, MakeConsensus])
        self._watch([WriteCode])


class CodeWriter(Role):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.set_actions([WriteCode, ReWriteCode])
        self._watch([Analyze, Debug])
        self._set_react_mode(react_mode="react")

    async def _react(self) -> Message:
        if self.latest_observed_msg.cause_by == "ProblemAnalyzer.Analyze":
            self._set_state(0)
        elif self.latest_observed_msg.cause_by == "Debugger.Debug":
            self._set_state(1)
        else:
            logger.error("bug")
        rsp = await self._act()
        return rsp

    async def _act(self) -> Message:
        todo = self.rc.todo
        if isinstance(todo, ReWriteCode):
            debug = self.latest_observed_msg.content
            prevmemory = self.rc.memory.get_by_action(WriteCode)[-1]
            assert prevmemory.role == self.profile
            prevcode = prevmemory.content
            code = await todo.run(instruction=self.rc.env.UserPrompt, prevcode=prevcode, debug=debug)
            self.rc.env.FinalResult = code
            return
        elif isinstance(todo, WriteCode):
            # 解析接收到的消息中的指令
            analysis = self.latest_observed_msg.content
            # 执行写代码的动作
            code = await todo.run(analysis=analysis, instruction=self.rc.env.UserPrompt)
            # code = cut_def_question(func_code=code, question=self.rc.env.UserPrompt, entry_point=self.rc.env.EntryPoint)
            msg = Message(role=self.profile, content=code, cause_by=todo, send_to="Code Generator Consensus Maker")
            self.rc.memory.add(msg)
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
