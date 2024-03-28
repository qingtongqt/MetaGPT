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
    You will be given a function signature and its docstring by the user:
    {instruction}
    You must respond with python code, no free-flowing text (unless in a comment). 
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


class AlgorithmDeveloper(Role):
    name: str = "Bob"
    profile: str = "Algorithm Developer"
    goal: str = "write code"
    desc: str = ("You are an algorithm developer. "
                 "You are good at developing and utilizing algorithms to solve problems.")


class ComputerScientist(Role):
    name: str = "Bob"
    profile: str = "Computer Scientist"
    goal: str = "write code"
    desc: str = ("You are a computer scientist. "
                 "You are good at writing high performance code and recognizing corner cases while solve real problems.")


class Programmer(Role):
    name: str = "Bob"
    profile: str = "Programmer"
    goal: str = "write code"
    desc: str = ("You are an intelligent programmer. "
                 "You must complete the python function given to you by the user. ")


class SoftwareArchitect(Role):
    name: str = "Bob"
    profile: str = "Software Architect"
    goal: str = "write code"
    desc: str = ("You are a software architect, skilled in designing and structuring code for scalability, "
                 "maintainability, and robustness. Your responses should focus on best practices in software design.")


class CodeArtist(Role):
    name: str = "Bob"
    profile: str = "Code Artist"
    goal: str = "write code"
    desc: str = ("You are a coding artist. "
                 "You write Python code that is not only functional but also aesthetically pleasing and creative. "
                 "Your goal is to make the code an art form while maintaining its utility. ")


class CodeWriter(Role):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.set_actions([WriteCode])
        # TODO self._watch()

    def _observe(self, ignore_memory=False) -> int:
        """Prepare new messages for processing from the message buffer and other sources."""
        # Read unprocessed messages from the msg buffer.
        news = []
        if self.recovered:
            news = [self.latest_observed_msg] if self.latest_observed_msg else []
        if not news:
            news = self.rc.msg_buffer.pop_all()
        # Store the read messages in your own memory to prevent duplicate processing.
        old_messages = [] if ignore_memory else self.rc.memory.get()
        self.rc.memory.add_batch(news)
        # Filter out messages of interest.
        self.rc.news = [
            n for n in news if (n.cause_by in self.rc.watch or self.name in n.send_to) and n not in old_messages
        ]
        self.latest_observed_msg = self.rc.news[-1] if self.rc.news else None  # record the latest observed msg

        # Design Rules:
        # If you need to further categorize Message objects, you can do so using the Message.set_meta function.
        # msg_buffer is a receiving buffer, avoid adding message data and operations to msg_buffer.
        news_text = [f"{i.role}: {i.content[:20]}..." for i in self.rc.news]
        if news_text:
            logger.debug(f"{self._setting} observed: {news_text}")
        return len(self.rc.news)

    async def _act(self) -> Message:
        # 解析接收到的消息中的指令
        instruction = self.get_memories(k=1)
        # 执行写代码的动作
        code = await self.todo.run(instruction)
        # 将生成的代码发送给 ConsensusMaker
        self.publish_message(
            Message(role=self.name, content=code, cause_by=WriteCode, send_to="ConsensusMaker"),
        )
