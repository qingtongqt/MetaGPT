# -*- coding:utf-8 -*-
from human_eval.data import write_jsonl, read_problems
from human_eval.execution_once import check_correctness
from ProblemAnalyzer import ProblemAnalyzer
from CodeGenerator import (
    AlgorithmDeveloper,
    ComputerScientist,
    Programmer,
    SoftwareArchitect,
    CodeArtist,
    CodeGeneratorConsensusMaker,
)
from metagpt.const import SERDESER_PATH
from route import get_route, clear_route
from metagpt.dyteam import DyTeam
from metagpt.logs import logger
import asyncio
import platform
import json


def write_json(filename, data):
    with open(filename, 'w', encoding='utf-8') as f:
        for entry in data:
            f.write(json.dumps(entry) + '\n')


# RM = ResultMaker(addresses={"Result Maker"})
PA = ProblemAnalyzer(addresses={"Problem Analyzer"})
AD = AlgorithmDeveloper(addresses={"Code Generator"})
CS = ComputerScientist(addresses={"Code Generator"})
P = Programmer(addresses={"Code Generator"})
SA = SoftwareArchitect(addresses={"Code Generator"})
CA = CodeArtist(addresses={"Code Generator"})
CGCM = CodeGeneratorConsensusMaker(addresses={"Code Generator Consensus Maker"})

problems = read_problems()
samples = []


async def simplewritecode(dyteam: DyTeam, idea: str, n_round: int = 5):
    dyteam.run_project(idea, send_to="Problem Analyzer")  # send debate topic to Biden and let him speak first
    completion = await dyteam.run(n_round=n_round)
    return completion


def humaneval(invesment: float = 10.0, n_round: int = 5):
    dyteam_writecode = DyTeam()
    dyteam_writecode.hire([PA, AD, CS, P, SA, CA, CGCM])
    dyteam_writecode.invest(invesment)
    if platform.system() == "Windows":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    loop = asyncio.get_event_loop()
    for i, (task_id, v) in enumerate(problems.items()):
        logger.info(f"task_id:{task_id}")
        idea = v["prompt"]
        dyteam_writecode.env.UserPrompt = idea
        dyteam_writecode.env.FinalResult = ""
        dyteam_writecode.run_project(idea, send_to="Problem Analyzer")
        completion = loop.run_until_complete(dyteam_writecode.run(n_round=n_round))
        # 清除记忆
        for r in dyteam_writecode.env.roles.values():
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
        if i % 5 == 0:  # N是您决定的保存频率，例如每10个任务保存一次
            write_jsonl("samples_temp.jsonl", samples)

    write_jsonl("samples_gpt-3.5-turbo-1106.jsonl", samples)


if __name__ == "__main__":
    humaneval(n_round=5)
