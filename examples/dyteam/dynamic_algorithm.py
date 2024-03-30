# -*- coding:utf-8 -*-
from human_eval.data import write_jsonl, read_problems
from ProblemAnalyzer import ProblemAnalyst, RequirementsEngineer, AlgorithmExpert, ProblemAnalyzerConsensusMaker
from CodeGenerator import (
    AlgorithmDeveloper,
    ComputerScientist,
    Programmer,
    SoftwareArchitect,
    CodeArtist,
    CodeGeneratorConsensusMaker,
)
from ResultMaker import ResultMaker
from metagpt.team import Team
import asyncio
import platform
import fire

test_prompt = "from typing import List\n\n\ndef has_close_elements(numbers: List[float], threshold: float) -> bool:\n" \
              "    \"\"\" Check if in given list of numbers, are any two numbers closer to each other than\n " \
              "   given threshold.\n    >>> has_close_elements([1.0, 2.0, 3.0], 0.5)\n    False\n" \
              "    >>> has_close_elements([1.0, 2.8, 3.0, 4.0, 5.0, 2.0], 0.3)\n    True\n    \"\"\"\n"


async def writecodetest(idea: str, investment: float = 10.0, n_round: int = 8):
    PA = ProblemAnalyst(addresses={"Problem Analyzer"})
    RE = RequirementsEngineer(addresses={"Problem Analyzer"})
    AE = AlgorithmExpert(addresses={"Problem Analyzer"})
    PACM = ProblemAnalyzerConsensusMaker(addresses={"Problem Analyzer", "Problem Analyzer Consensus Maker"})

    AD = AlgorithmDeveloper(addresses={"Code Generator"})
    CS = ComputerScientist(addresses={"Code Generator"})
    P = Programmer(addresses={"Code Generator"})
    SA = SoftwareArchitect(addresses={"Code Generator"})
    CA = CodeArtist(addresses={"Code Generator"})
    CGCM = CodeGeneratorConsensusMaker(addresses={"Code Generator Consensus Maker"})

    RM = ResultMaker(addresses={"Result Maker"})

    team = Team()
    team.env.UserPrompt = test_prompt
    team.hire([PA, RE, AE, PACM, AD, CS, P, SA, CA, CGCM, RM])
    team.invest(investment)
    team.run_project(idea, send_to="Problem Analyzer")  # send debate topic to Biden and let him speak first
    await team.run(n_round=n_round)


def main(idea: str = test_prompt, investment: float = 10.0, n_round: int = 8):
    """
    :param idea: Debate topic, such as "Topic: The U.S. should commit more in climate change fighting"
                 or "Trump: Climate change is a hoax"
    :param investment: contribute a certain dollar amount to watch the debate
    :param n_round: maximum rounds of the debate
    :return:
    """
    if platform.system() == "Windows":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(writecodetest(idea, investment, n_round))


if __name__ == "__main__":
    fire.Fire(main)
