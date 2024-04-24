from typing import Optional, Callable, Dict
import ast
import contextlib
import faulthandler
import io
import os
import multiprocessing
import platform
import math
import tempfile
import threading
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

API_CALL = 0


def add_api_call():
    global API_CALL
    API_CALL += 1


def get_api_call():
    return API_CALL


def calculate_cosine_similarity(reference, candidate):
    vectorizer = TfidfVectorizer()
    tfidf = vectorizer.fit_transform([reference, candidate])
    return cosine_similarity(tfidf[0:1], tfidf[1:2])[0][0]

def most_frequent(group_message: dict[str, str], cmp_func) -> dict[str, str]:
    consensus_ans = {}
    for role_profile, message in group_message.items():
        consensus_num = sum(cmp_func(message, item) for item in group_message.values())
        if consensus_num >= 0.6 * len(group_message):
            consensus_ans[role_profile] = message
    return consensus_ans


def py_is_syntax_valid(code: str) -> bool:
    try:
        ast.parse(code)
        return True
    except Exception:
        return False


def cut_def_question(func_code, question, entry_point):
    def parse_imports(src_code):
        res = []
        for line in src_code.split("\n"):
            if "import" in line:
                res.append(line)
        res = ["    " + line.strip() for line in res]
        return res

    import_lines = parse_imports(func_code)

    def extract_functions_with_body(source_code):
        # Parse the source code to an AST
        tree = ast.parse(source_code)

        functions = []
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                # Check if the function is nested inside another function
                # We can determine this by checking the ancestors of the node
                parents = [n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef)]
                nesting_level = sum(1 for parent in parents if
                                    parent.lineno <= node.lineno and parent.end_lineno >= node.end_lineno)

                if nesting_level == 1:  # Only top-level functions
                    start_line = node.lineno - 1
                    end_line = node.end_lineno
                    function_body = source_code.splitlines()[start_line:end_line]
                    functions.append("\n".join(function_body))

        return functions

    try:
        funcs = extract_functions_with_body(func_code)
    except:
        funcs = [func_code]

    def extract_func_def(src_code):
        for line in src_code.split("\n"):
            if "def" in line and entry_point in line:
                return line
        return ""

    que_func = extract_func_def(question)

    for fiid, func_ins_code in enumerate(funcs):
        if question in func_ins_code:
            func_ins_code = func_ins_code.split(question)[-1]
        elif question.strip() in func_ins_code:
            func_ins_code = func_ins_code.split(question.strip())[-1]
        elif que_func in func_ins_code:
            # remove the line before def
            res_lines = func_ins_code.split("\n")
            func_ins_code = ""
            in_func = False
            for line in res_lines:
                if in_func:
                    func_ins_code += line + "\n"
                if "def" in line:
                    in_func = True
        else:
            continue

        other_funcs = []
        for other_func in funcs[:fiid] + funcs[fiid + 1:]:
            other_func = other_func.split("\n")
            other_func = other_func[:1] + import_lines + other_func[1:]
            other_func = "\n".join(other_func)
            other_funcs.append(other_func)

        return "\n".join(import_lines) + "\n" + func_ins_code + "\n" + "\n".join(other_funcs)

    res_lines = func_code.split("\n")
    func_code = ""
    in_func = False
    for line in res_lines:
        if in_func:
            func_code += line + "\n"
        if "def" in line:
            in_func = True

    return "\n".join(import_lines) + "\n" + func_code


def calculate_nct(w, n, N):
    if N == 0:
        return math.log(2)
    elif n == 0:
        return math.log(2) * (math.log(N)) ** 0.5
    else:
        return w / n + math.log(2) * (math.log(N) / n) ** 0.5
