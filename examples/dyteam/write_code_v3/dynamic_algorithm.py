# -*- coding:utf-8 -*-
from human_eval.data import write_jsonl, read_problems
from human_eval.execution_once import check_correctness
from TaskAssigner import TaskAssigner
from CodeGenerator import (
    AlgorithmDeveloper,
    ComputerScientist,
    Programmer,
    SoftwareArchitect,
    CodeArtist,
    CodeGeneratorConsensusMaker,
)
from Debugger import Debugger
from metagpt.const import SERDESER_PATH
from route import get_route, clear_route
from metagpt.dyteam import DyTeam
from metagpt.logs import logger
import asyncio
import platform
import json
from utils import cut_def_question


def write_json(filename, data):
    with open(filename, 'w', encoding='utf-8') as f:
        for entry in data:
            f.write(json.dumps(entry) + '\n')


# RM = ResultMaker(addresses={"Result Maker"})
TA = TaskAssigner(addresses={"Problem Assigner"})
AD = AlgorithmDeveloper(addresses={"Code Generator", "Algorithm Developer"})
CS = ComputerScientist(addresses={"Code Generator", "Computer Scientist"})
P = Programmer(addresses={"Code Generator", "Programmer"})
SA = SoftwareArchitect(addresses={"Code Generator", "Software Architect"})
CA = CodeArtist(addresses={"Code Generator", "Code Artist"})
CGCM = CodeGeneratorConsensusMaker(addresses={"Code Generator Consensus Maker"})
D = Debugger(addresses={"Debugger"})

problems = read_problems()
samples = []


def humaneval(invesment: float = 5.0, n_round: int = 6):
    roles = [TA, AD, CS, P, SA, CA, CGCM, D]
    with open('roles_data.txt', 'r') as file:
        i = 0
        for line in file:
            profile, w, n = line.strip().split(',')
            w, n = int(w), int(n)
            assert profile == roles[i].profile
            roles[i].set_w_n(w=w, n=n)
            i += 1
    dyteam_writecode = DyTeam()
    dyteam_writecode.hire(roles)
    dyteam_writecode.invest(invesment)
    if platform.system() == "Windows":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    loop = asyncio.get_event_loop()
    for i, (task_id, v) in enumerate(problems.items()):
        logger.info(f"task_id:{task_id}")
        dyteam_writecode.env.UserPrompt = v["prompt"]
        dyteam_writecode.env.FinalResult = ""
        # dyteam_writecode.env.EntryPoint = v["entry_point"]
        dyteam_writecode.run_project(v["prompt"], send_to="Problem Analyzer")
        completion = loop.run_until_complete(dyteam_writecode.run(n_round=n_round))
        logger.info(f"Final Result:\n{completion}")
        completion = cut_def_question(completion, v["prompt"], v["entry_point"])
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
        if i % 5 == 0:
            write_jsonl("samples_temp.jsonl", samples)
        with open('roles_data.txt', 'w') as file:
            for role in roles:
                file.write(f"{role.profile},{role.w},{role.n}\n")


    write_jsonl("samples_gpt-3.5-turbo-1106.jsonl", samples)


if __name__ == "__main__":
    humaneval(n_round=5)
