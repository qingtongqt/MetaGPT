import re
import math
import pandas as pd

API_CALL = 0
MMLU_QUESTION = "Can you answer the following question as accurately as possible? {}: A) {}, B) {}, C) {}, D) {} "


def add_api_call():
    global API_CALL
    API_CALL += 1


def get_api_call():
    return API_CALL


def most_frequent(group_message: dict[str, str], cmp_func) -> dict[str, str]:
    consensus_ans = {}
    for role_profile, message in group_message.items():
        consensus_num = sum(cmp_func(message, item) for item in group_message.values())
        if consensus_num >= 0.6 * len(group_message):
            consensus_ans[role_profile] = message
    return consensus_ans


def parse_single_choice(reply):
    pattern = r'\(([ABCDabcd])\)'
    matches = re.findall(pattern, reply)

    solution = None
    for match_str in matches[::-1]:
        solution = match_str.upper()
        if solution:
            break

    if solution is None:
        alter_pattern = r'([ABCDabcd])\)'
        alter_matches = re.findall(alter_pattern, reply)
        for match_str in alter_matches[::-1]:
            solution = match_str.upper()
            if solution:
                break

    return solution


def calculate_nct(w, n, N):
    if N == 0:
        return math.log(2)
    elif n == 0:
        return math.log(2) * (math.log(N)) ** 0.5
    else:
        return w / n + math.log(2) * (math.log(N) / n) ** 0.5


def parse_question_answer(df, ix):
    question = df.iloc[ix, 0]
    a = df.iloc[ix, 1]
    b = df.iloc[ix, 2]
    c = df.iloc[ix, 3]
    d = df.iloc[ix, 4]

    question = MMLU_QUESTION.format(question, a, b, c, d)

    answer = df.iloc[ix, 5]

    return question, answer


def get_mmlu_qa_pairs(df):
    ix = len(df)
    return [parse_question_answer(df, idx) for idx in range(ix)]


def most_frequent_ans(clist):
    counter = 0
    num = clist[0]
    cmp_func = lambda x, y: parse_single_choice(x) == parse_single_choice(y)
    for i in clist:
        current_frequency = sum(cmp_func(i, item) for item in clist)
        if current_frequency > counter:
            counter = current_frequency
            num = i

    return num, counter