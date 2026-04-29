import copy
import json
import os
import random
import sys
import tempfile


THIS_DIR = os.path.dirname(__file__)
PROJECT_ROOT = os.path.abspath(os.path.join(THIS_DIR, ".."))
LIBS_DIR = os.path.join(PROJECT_ROOT, "libs")

for path in (PROJECT_ROOT, LIBS_DIR, THIS_DIR):
    if path not in sys.path:
        sys.path.append(path)

from d2l.question import MSQuestion
from d2l.questionpool import QuestionPool
from libs.fsm.fsm import FSM
from logic_utils.logic_utils import logic_eval
from generate_random_fsms_guaranteed import (
    explorer_url,
    find_template_file,
    generate_one_variant,
    input_combos,
    make_input_patterns,
    normalize_term,
    reduce_patterns,
)


POOL_TITLE = "Improper FSM Conditions"
POOL_FILE = os.path.join(THIS_DIR, "improper_fsm_conditions_pool.csv")
NUM_QUESTIONS = 20


def fsm_from_json(fsm_json):
    temp_name = None
    try:
        with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as file:
            json.dump(fsm_json, file)
            temp_name = file.name

        return FSM(temp_name)
    finally:
        if temp_name and os.path.exists(temp_name):
            os.unlink(temp_name)


def combo_to_pattern(input_names, combo):
    terms = []
    for name, bit in zip(input_names, combo):
        terms.append(name if bit == "1" else f"{name}'")
    return " ".join(terms)


def combo_to_option(input_names, state_name, combo):
    assignments = ", ".join(
        f"{name}={bit}" for name, bit in zip(input_names, combo)
    )
    return f"State {state_name} when {assignments}"


def get_output_bits_for_row(fsm, row):
    return "".join(row[name] for name in fsm.output_names)


def fsm_to_transition_entries(fsm):
    entries_by_state = {state: [] for state in fsm.state_names}

    for state_name in fsm.state_names:
        state_code = fsm.state_combo_map[state_name]

        for combo in fsm.input_combos:
            row = fsm.get_row(state_code, combo)
            next_state_code = row["next_states"][0]
            entries_by_state[state_name].append({
                "combo": combo,
                "next_state": fsm.state_name_map[next_state_code],
                "output": get_output_bits_for_row(fsm, row),
            })

    return entries_by_state


def node_index_by_state(fsm_json):
    return {
        node["stateName"]: index
        for index, node in enumerate(fsm_json["fsmNodes"])
    }


def make_reference_point(fsm_json, start_index, end_index):
    start = fsm_json["fsmNodes"][start_index]["referencePoint"]
    end = fsm_json["fsmNodes"][end_index]["referencePoint"]
    return {
        "x": (start["x"] + end["x"]) / 2,
        "y": (start["y"] + end["y"]) / 2 - 45,
    }


def make_self_reference_point(fsm_json, node_index):
    point = fsm_json["fsmNodes"][node_index]["referencePoint"]
    return {"x": point["x"], "y": point["y"] - 70}


def rebuild_arcs_from_entries(fsm_json, entries_by_state, input_names, is_mealy):
    fsm_json = copy.deepcopy(fsm_json)
    index_by_state = node_index_by_state(fsm_json)
    all_patterns = make_input_patterns(input_names)

    normal_arcs = []
    self_arcs = []

    for state_name, entries in entries_by_state.items():
        groups = {}
        for entry in entries:
            key = (entry["next_state"], entry["output"] if is_mealy else "")
            groups.setdefault(key, []).append(entry["combo"])

        for (next_state, output_bits), combos in groups.items():
            patterns = [combo_to_pattern(input_names, combo) for combo in combos]
            condition = reduce_patterns(input_names, patterns, all_patterns)
            label = f"{condition}/{output_bits}" if is_mealy else condition

            start_index = index_by_state[state_name]
            end_index = index_by_state[next_state]

            if state_name == next_state:
                self_arcs.append({
                    "node": start_index,
                    "outputText": label,
                    "referencePoint": make_self_reference_point(fsm_json, start_index),
                    "selected": False,
                })
            else:
                normal_arcs.append({
                    "startNode": start_index,
                    "endNode": end_index,
                    "outputText": label,
                    "referencePoint": make_reference_point(fsm_json, start_index, end_index),
                    "selected": False,
                })

    fsm_json["fsmArcs"] = normal_arcs
    fsm_json["fsmSelfArcs"] = self_arcs
    return fsm_json


def matching_transition_counts(fsm_json, input_names):
    counts = {}
    index_to_state = {
        index: node["stateName"]
        for index, node in enumerate(fsm_json["fsmNodes"])
    }
    combos = input_combos(input_names)

    outgoing = {state: [] for state in index_to_state.values()}
    for arc in fsm_json.get("fsmArcs", []):
        outgoing[index_to_state[arc["startNode"]]].append(arc.get("outputText", ""))
    for arc in fsm_json.get("fsmSelfArcs", []):
        outgoing[index_to_state[arc["node"]]].append(arc.get("outputText", ""))

    for state_name, labels in outgoing.items():
        for combo in combos:
            count = 0
            for label in labels:
                for raw_term in label.split("|"):
                    condition, _output = normalize_term(raw_term)
                    count += logic_eval(input_names, combo, condition)
            counts[(state_name, combo)] = count

    return counts


def find_bad_conditions(fsm_json, input_names, problem_type):
    counts = matching_transition_counts(fsm_json, input_names)
    target_count = 0 if problem_type == "no_next_state" else 2

    return [
        key for key, count in counts.items()
        if count == target_count
    ]


def make_improper_fsm(valid_fsm_json, problem_type):
    fsm = fsm_from_json(valid_fsm_json)
    input_names = fsm.input_names
    entries_by_state = fsm_to_transition_entries(fsm)
    is_mealy = bool(fsm.mealy_names)

    state_name = random.choice(fsm.state_names)
    combo = random.choice(fsm.input_combos)

    entries = entries_by_state[state_name]
    original = next(entry for entry in entries if entry["combo"] == combo)

    if problem_type == "no_next_state":
        entries_by_state[state_name] = [
            entry for entry in entries
            if entry["combo"] != combo
        ]
    else:
        possible_destinations = [
            state for state in fsm.state_names
            if state != original["next_state"]
        ]
        if not possible_destinations:
            raise ValueError("Need at least two states to create multiple next states")

        entries_by_state[state_name].append({
            "combo": combo,
            "next_state": random.choice(possible_destinations),
            "output": original["output"],
        })

    improper_json = rebuild_arcs_from_entries(
        valid_fsm_json,
        entries_by_state,
        input_names,
        is_mealy,
    )

    no_next = find_bad_conditions(improper_json, input_names, "no_next_state")
    multiple = find_bad_conditions(improper_json, input_names, "multiple_next_states")

    if problem_type == "no_next_state" and len(no_next) == 1 and not multiple:
        return improper_json, input_names, fsm.state_names, no_next

    if problem_type == "multiple_next_states" and len(multiple) == 1 and not no_next:
        return improper_json, input_names, fsm.state_names, multiple

    raise ValueError("Improper FSM did not produce exactly one target condition")


def generate_valid_fsm_json():
    template_name = random.choice(["2state", "3state", "4state"])
    template_file = find_template_file(template_name)

    with open(template_file, "r") as file:
        base_json = json.load(file)

    fsm_json, _metadata = generate_one_variant(base_json)
    return fsm_json


def generate_problem():
    for _ in range(100):
        valid_json = generate_valid_fsm_json()
        problem_type = random.choice(["no_next_state", "multiple_next_states"])

        try:
            improper_json, input_names, state_names, bad_conditions = make_improper_fsm(
                valid_json,
                problem_type,
            )
        except Exception:
            continue

        return {
            "fsm_json": improper_json,
            "input_names": input_names,
            "state_names": state_names,
            "problem_type": problem_type,
            "bad_conditions": bad_conditions,
        }

    raise ValueError("Could not generate an improper FSM question")


def question_text(problem):
    target = (
        "no next state"
        if problem["problem_type"] == "no_next_state"
        else "multiple next states"
    )
    return (
        f"<p>The FSM linked below is improperly specified. Select every condition "
        f"that has <b>{target}</b>.</p>"
        f"<p><a href=\"{explorer_url(problem['fsm_json'])}\" target=\"_blank\">Open FSM diagram</a></p>"
    )


def build_question():
    problem = generate_problem()
    question = MSQuestion(
        text=question_text(problem),
        title=POOL_TITLE,
        points=10,
        difficulty=3,
        shuffle=True,
    )

    correct = set(problem["bad_conditions"])
    for state_name in problem["state_names"]:
        for combo in input_combos(problem["input_names"]):
            option = combo_to_option(problem["input_names"], state_name, combo)
            question.add_answer(option, (state_name, combo) in correct)

    return question


def main():
    pool = QuestionPool(POOL_TITLE, POOL_FILE)

    for _ in range(NUM_QUESTIONS):
        pool.add_question(build_question())

    pool.package()
    print(f"Wrote {NUM_QUESTIONS} questions to {POOL_FILE}")


if __name__ == "__main__":
    main()
