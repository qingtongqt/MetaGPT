# -*- coding:utf-8 -*-
from metagpt.actions.action import Action
from metagpt.roles.role import Role
from metagpt.schema import Message
from metagpt.logs import logger
from ConsensusMaker import MakeConsensus
from route import route_top


class Debug(Action):
    PROMPT_TEMPLATE: str = """
    Here is a function signature and its implementation by the Code Writer:
    {instruction}
    The Code Writer's implementation:
    {completion}
    Debug this version of implementation and write your feedback as a debugger.
    please ensure that the input parameters match exactly with the function signature I provided.
    """
    name: str = "Debug"

    async def run(self, instruction: str, completion: str):
        logger.info(f"original_result:{completion}")
        prompt = self.PROMPT_TEMPLATE.format(instruction=instruction, completion=completion)
        rsp = await self._aask(prompt)
        return rsp


class Debugger(Role):
    name: str = "David"
    goal: str = "Debug the code"
    profile: str = "Debugger"

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.set_actions([Debug])
        self._watch([MakeConsensus])

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
            n for n in news if
            n.cause_by in self.rc.watch and n.role == "Code Generator Consensus Maker" and n not in old_messages
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

    async def _act(self) -> Message:
        # 解析接收到的消息中的指令
        code = self.latest_observed_msg.content
        # 执行写代码的动作
        debug_result = await self.todo.run(instruction=self.rc.env.UserPrompt, completion=code)
        send_to = route_top().profile
        logger.info(f"{send_to}")
        msg = Message(role=self.profile, content=debug_result, cause_by=self.rc.todo, send_to=send_to)
        return msg


class TestEngineer(Debugger):
    name: str = "David"
    profile: str = "Test Engineer"
    desc: str = ("As a seasoned test engineer, you specialize in devising comprehensive testing strategies "
                 "that ensure software reliability and correctness.  Your experience has equipped you with the ability "
                 "to anticipate potential issues and meticulously plan for a wide range of test scenarios, "
                 "including edge cases.  You are skilled in creating detailed test cases that assess every "
                 "aspect of a program's functionality, ensuring that all requirements are met and the solution "
                 "performs as expected under various conditions.")


class BugFixer(Debugger):
    name: str = "Ryan"
    profile: str = "BugFixer"
    desc: str = ("With a proven track record in debugging and error resolution, "
                 "you have developed a sharp eye for identifying the root causes of software bugs. "
                 "Your approach to problem-solving is methodical, enabling you to meticulously analyze code "
                 "for flaws and implement effective fixes. Your expertise not only lies in correcting errors "
                 "but also in optimizing code to prevent future issues, ensuring that the software is robust, "
                 "efficient, and aligned with best practices.")


class Reflector(Debugger):
    name: str = "Lily"
    profile: str = "Reflector"
    desc: str = (
        "As a reflector, you possesses an advanced understanding of various programming languages and algorithms.")
