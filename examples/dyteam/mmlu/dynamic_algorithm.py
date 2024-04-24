# -*- coding:utf-8 -*-
import os

from SolutionGenerator import (
    Lawyer,
    Historian,
    Mathematician,
    Psychologist,
    Biologist,
    Engineer,
    SolutionGeneratorConsensusMaker,
    SolutionGeneratorTaskAssigner
)
from Administrator import Administrator
from dyteam import DyTeam
from metagpt.logs import logger
import asyncio
import platform
from utils import get_api_call, get_mmlu_qa_pairs, parse_single_choice
import pandas as pd
from categories import find_category
import json


SGTA = SolutionGeneratorTaskAssigner(addresses={"Solution Generator Problem Assigner"})

lawyer = Lawyer(addresses={"Solution Generator", "Lawyer"})
historian = Historian(addresses={"Solution Generator", "Historian"})
mathematician = Mathematician(addresses={"Solution Generator", "Mathematician"})
psychologist = Psychologist(addresses={"Solution Generator", "Psychologist"})
biologist = Biologist(addresses={"Solution Generator", "Biologist"})
engineer = Engineer(addresses={"Solution Generator", "Engineer"})

SGCM = SolutionGeneratorConsensusMaker(addresses={"Solution Generator Consensus Maker"})

A = Administrator(group_list=[[lawyer, historian, mathematician, psychologist, biologist, engineer]])

samples = []
results = []
directory = 'data/test'


def mmlu(invesment: float = 5.0, n_round: int = 10):
    roles = [SGTA, lawyer, historian, mathematician, psychologist, biologist, engineer, SGCM]

    dyteam = DyTeam(administrator=A)
    dyteam.hire(roles)
    dyteam.invest(invesment)
    if platform.system() == "Windows":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    loop = asyncio.get_event_loop()
    for filename in os.listdir(directory):
        if filename.endswith("_test.csv"):
            subject = filename.split("_test.csv")[0]
            category = find_category(subject)
            if category != "other (business, health, misc.)":
                continue
            file_path = os.path.join(directory, filename)
            df = pd.read_csv(file_path, header=None)
            length = int(df.shape[0] * 0.1)
            sampled_df = df.sample(n=length)
            qa_pairs = get_mmlu_qa_pairs(sampled_df)
            success_cnt, total_cnt = 0, 0
            for que, ans in qa_pairs:
                dyteam.env.UserPrompt = que
                dyteam.env.FinalResult = ""
                for r in dyteam.env.roles.values():
                    r.rc.memory.clear()
                    r.rc.msg_buffer.pop_all()
                SGCM.iterate_num = 0
                dyteam.run_project(que, send_to="Solution Generator Problem Assigner")
                completion = loop.run_until_complete(dyteam.run(n_round=n_round))
                logger.info(f"Final Result:\n{completion}")
                samples.append({"subject": subject, "question": que, "completion": completion})

                for r in dyteam.env.roles.values():
                    r.rc.memory.clear()
                    r.rc.msg_buffer.pop_all()
                pred = parse_single_choice(completion)
                total_cnt += 1
                if pred == ans:
                    success_cnt += 1
            results.append(f"{subject},{success_cnt},{total_cnt}")
            logger.info(f"{subject} acc: {success_cnt} / {total_cnt}")
            logger.info(f"API CALL: {get_api_call()}")

    logger.info(f"final API CALL: {get_api_call()}")
    with open('other_roles_data.txt', 'w') as file:
        for role in roles:
            file.write(f"{role.profile},{role.w},{role.n}\n")

    with open('other_results.txt', "w") as file:
        for result in results:
            file.write(result + '\n')

    with open("other_raw.txt", 'w', encoding='utf-8') as f:
        for data in samples:
            f.write(json.dumps(data) + '\n')


if __name__ == "__main__":
    mmlu(n_round=7)

# with open('single_execution_results.txt', 'r') as file:
#     success, total = 0, 0
#     for line in file:
#         _, suc_cnt, total_cnt = line.strip().split(',')
#         success += int(suc_cnt)
#         total += int(total_cnt)
#     print(total)
#     print(success / total)

