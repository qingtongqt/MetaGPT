# -*- coding:utf-8 -*-
import json

from metagpt.actions.action import Action
from metagpt.roles.role import Role
from metagpt.schema import Message
from metagpt.logs import logger
from route import get_route, clear_route, route_top
from human_eval.data import read_problems
from human_eval.execution_once import check_correctness
from ConsensusMaker import MakeConsensus


class Debug(Action):
    name: str = "Debug"

    async def run(self, task_id: str, completion: str):
        problems = read_problems()
        result = check_correctness(problems[task_id], completion, timeout=10)
        return result


class Debugger(Role):
    name: str = "David"
    goal: str = "Debug the code"
    profile: str = "Debugger"
    task_id: str = ""
    rewrite_num: int = 0

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
            logger.debug(f"{self._setting} observed {len(self.rc.news)} message: {news_text}")
        return len(self.rc.news)

    async def _act(self) -> Message:
        # 解析接收到的消息中的指令
        code = self.latest_observed_msg.content
        # 执行写代码的动作
        debug_result = await self.todo.run(task_id=self.task_id, completion=code)
        logger.info(f"debug result:{debug_result}")
        route = get_route()
        logger.info(f"route:{[r.profile for r in route]}")
        if debug_result["passed"]:
            for r in route:
                r.n += 1
                r.w += 1
            clear_route()
            self.rc.env.FinalResult = code
            return
        else:
            for r in route:
                r.n += 1
            clear_route()
            # 最大重写次数
            if self.rewrite_num >= 2:
                self.rc.env.FinalResult = code
                logger.info("max rewrite")
                return
            self.rewrite_num += 1
            content = json.dumps({"code": code, "result": debug_result["result"]})
            msg = Message(role=self.profile, content=content,
                          cause_by=self.rc.todo, send_to={"Code Generator"})
            return msg
