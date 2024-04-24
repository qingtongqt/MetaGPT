import os
import pandas as pd
import asyncio
from utils import get_mmlu_qa_pairs, parse_single_choice
from metagpt.llm import LLM
from metagpt.logs import logger

directory = 'data/test'

results = []

PROMPT_TEMPLATE: str = """
{question}
Put your answer in the form (X) at the end of your response. (X) represents choice (A), (B), (C), or (D).
"""


async def main():
    llm = LLM()
    for filename in os.listdir(directory):
        if filename.endswith("_test.csv"):
            subject = filename.split("_test.csv")[0]
            file_path = os.path.join(directory, filename)

            df = pd.read_csv(file_path, header=None)
            length = int(df.shape[0] * 0.1)
            sampled_df = df.sample(n=length)
            qa_pairs = get_mmlu_qa_pairs(sampled_df)
            success_cnt, total_cnt = 0, 0
            for que, ans in qa_pairs:
                instruction = PROMPT_TEMPLATE.format(question=que)
                completion = await llm.aask(instruction)
                pred = parse_single_choice(completion)
                total_cnt += 1
                if pred == ans:
                    success_cnt += 1
            logger.info(f"{subject},{success_cnt},{total_cnt}")
            results.append(f"{subject},{success_cnt},{total_cnt}")
            with open('tmp_result.txt', 'a') as f:
                f.write(f"{subject},{success_cnt},{total_cnt}\n")

    with open('results.txt', 'w') as f:
        for result in results:
            f.write(result + '\n')


if __name__ == "__main__":
    asyncio.run(main())
