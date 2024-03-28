# -*- coding:utf-8 -*-
from metagpt.actions.action import Action
from metagpt.roles.role import Role
from metagpt.schema import Message
from metagpt.logs import logger


class TestEngineer(Role):
    name: str = "Bob"
    profile: str = "Test Engineer"
    goal: str = "Write test cases based on the problem description and expected output. " \
                "Run the generated code, checking for correctness and edge conditions"
    desc: str = ("As a seasoned test engineer, you specialize in devising comprehensive testing strategies "
                 "that ensure software reliability and correctness.  Your experience has equipped you with the ability "
                 "to anticipate potential issues and meticulously plan for a wide range of test scenarios, "
                 "including edge cases.  You are skilled in creating detailed test cases that assess every "
                 "aspect of a program's functionality, ensuring that all requirements are met and the solution "
                 "performs as expected under various conditions.")


class BugFixer(Role):
    name: str = "Bob"
    profile: str = "BugFixer"
    goal: str = "Write test cases based on the problem description and expected output. " \
                "Run the generated code, checking for correctness and edge conditions"
    desc: str = ("With a proven track record in debugging and error resolution, "
                 "you have developed a sharp eye for identifying the root causes of software bugs. "
                 "Your approach to problem-solving is methodical, enabling you to meticulously analyze code "
                 "for flaws and implement effective fixes. Your expertise not only lies in correcting errors "
                 "but also in optimizing code to prevent future issues, ensuring that the software is robust, "
                 "efficient, and aligned with best practices.")
