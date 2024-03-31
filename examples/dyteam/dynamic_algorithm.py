# -*- coding:utf-8 -*-
from human_eval.data import write_jsonl, read_problems
from human_eval.execution_once import check_correctness
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
from route import get_route, clear_route
from metagpt.dyteam import DyTeam
from metagpt.logs import logger
import asyncio
import platform

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

problems = read_problems()
samples = []


async def simplewritecode(dyteam: DyTeam, idea: str, n_round: int = 5):
    dyteam.run_project(idea, send_to="Problem Analyzer")  # send debate topic to Biden and let him speak first
    completion = await dyteam.run(n_round=n_round)
    return completion


def humaneval(investment: float = 30.0, n_round: int = 5):
    if platform.system() == "Windows":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    dyteam = DyTeam()
    dyteam.hire([PA, RE, AE, PACM, AD, CS, P, SA, CA, CGCM, RM])
    dyteam.invest(investment)
    for task_id, v in problems.items():
        logger.info(f"task_id:{task_id}")
        idea = v["prompt"]
        dyteam.env.UserPrompt = idea
        dyteam.env.FinalResult = ""
        dyteam.run_project(idea, send_to="Problem Analyzer")
        completion = asyncio.run(dyteam.run(n_round=n_round))
        # 清除记忆
        for r in dyteam.env.roles.values():
            r.rc.memory.clear()
        result = check_correctness(v, completion, timeout=10)
        logger.info(f"result:{result}")
        samples.append({"task_id": task_id, "completion": completion})
        route = get_route()
        logger.info(f"route:{[r.profile for r in route]}")
        for r in route:
            r.n += 1
            if result['passed']:
                r.w += 1
        clear_route()

    write_jsonl("samples_gpt-3.5-turbo-1106.jsonl", samples)


if __name__ == "__main__":
    humaneval()
