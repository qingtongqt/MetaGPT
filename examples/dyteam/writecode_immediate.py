# -*- coding:utf-8 -*-
"""
作者:qingtong
日期:2024年04月14日
"""
from human_eval.data import write_jsonl, read_problems
import asyncio
from metagpt.logs import logger
import re
from metagpt.llm import LLM

PROMPT_TEMPLATE: str = """
Complete the following code. Use ```python to put the completed Python code, including the necessary imports, in markdown quotes:\n{code}
"""


def parse_code(rsp):
    pattern = r"```python(.*)```"
    match = re.search(pattern, rsp, re.DOTALL)
    code_text = match.group(1) if match else rsp
    if code_text.startswith("```python"):
        code_text = code_text[len("```python"):]
    return code_text


async def main():
    llm = LLM()
    samples = []
    problems = read_problems()
    for i, (task_id, v) in enumerate(problems.items()):
        logger.info(f"task_id:{task_id}")
        idea = v["prompt"]
        instruction = PROMPT_TEMPLATE.format(code=idea)
        completion = await llm.aask(instruction)
        completion = parse_code(completion)
        logger.info(completion)
        samples.append({"task_id": task_id, "completion": completion})
    write_jsonl("gpt-3.5-turbo-0125-simple.jsonl", samples)


if __name__ == "__main__":
    asyncio.run(main())
