# -*- coding:utf-8 -*-
from human_eval.data import write_jsonl, read_problems
from CodeGenerator import (
    AlgorithmDeveloper,
    ComputerScientist,
    Programmer,
    SoftwareArchitect,
    CodeArtist,
    CodeGeneratorConsensusMaker,
    CodeGeneratorTaskAssigner
)
from Debugger import Debugger
from Administrator import Administrator
from metagpt.const import SERDESER_PATH
from route import get_route, clear_route
from dyteam import DyTeam
from metagpt.logs import logger
import asyncio
import platform
import json
from utils import cut_def_question, get_api_call


def write_json(filename, data):
    with open(filename, 'w', encoding='utf-8') as f:
        for entry in data:
            f.write(json.dumps(entry) + '\n')


CGTA = CodeGeneratorTaskAssigner(addresses={"Code Generator Problem Assigner"})
AD = AlgorithmDeveloper(addresses={"Code Generator", "Algorithm Developer"})
CS = ComputerScientist(addresses={"Code Generator", "Computer Scientist"})
P = Programmer(addresses={"Code Generator", "Programmer"})
SA = SoftwareArchitect(addresses={"Code Generator", "Software Architect"})
CA = CodeArtist(addresses={"Code Generator", "Code Artist"})
CGCM = CodeGeneratorConsensusMaker(addresses={"Code Generator Consensus Maker"})
D = Debugger(addresses={"Debugger"})
A = Administrator(group_list=[[AD, CS, P, SA, CA]])

problems = read_problems()
samples = []


def humaneval(invesment: float = 5.0, n_round: int = 10):
    roles = [CGTA, AD, CS, P, SA, CA, CGCM, D]
    # 读取角色配置
    with open('roles_data.txt', 'r') as file:
        i = 0
        for line in file:
            profile, w, n = line.strip().split(',')
            w, n = int(w), int(n)
            assert profile == roles[i].profile
            roles[i].set_w_n(w=w, n=n)
            i += 1
    dyteam_writecode = DyTeam(administrator=A)
    dyteam_writecode.hire(roles)
    dyteam_writecode.invest(invesment)
    if platform.system() == "Windows":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    loop = asyncio.get_event_loop()
    for i, (task_id, v) in enumerate(problems.items()):
        logger.info(f"task_id:{task_id}")
        dyteam_writecode.env.UserPrompt = v["prompt"]
        D.task_id = task_id
        dyteam_writecode.env.FinalResult = ""
        for r in dyteam_writecode.env.roles.values():
            r.rc.memory.clear()
            r.rc.msg_buffer.pop_all()
        D.rewrite_num = 0
        CGCM.iterate_num = 0
        dyteam_writecode.run_project(v["prompt"], send_to="Code Generator Problem Assigner")
        completion = loop.run_until_complete(dyteam_writecode.run(n_round=n_round))
        logger.info(f"Final Result:\n{completion}")
        # 清除短期记忆
        for r in dyteam_writecode.env.roles.values():
            r.rc.memory.clear()
            r.rc.msg_buffer.pop_all()
        samples.append({"task_id": task_id, "completion": completion})
        if i % 5 == 0:
            write_jsonl("samples_temp.jsonl", samples)
            with open('roles_data.txt', 'w') as file:
                for role in roles:
                    file.write(f"{role.profile},{role.w},{role.n}\n")

        logger.info(f"API CALL: {get_api_call()}")

    write_jsonl("v3_gpt-3.5-turbo-1106.jsonl", samples)
    with open('roles_data.txt', 'w') as file:
        for role in roles:
            file.write(f"{role.profile},{role.w},{role.n}\n")
    logger.info(f"final API CALL: {get_api_call()}")


if __name__ == "__main__":
    humaneval(n_round=19)
