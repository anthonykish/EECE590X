import copy
import json
import os
import random
import re
import sys
import tempfile
import urllib.parse


THIS_DIR = os.path.dirname(__file__)
PROJECT_ROOT = os.path.abspath(os.path.join(THIS_DIR, ".."))
LIBS_DIR = os.path.join(PROJECT_ROOT, "libs")

for path in (PROJECT_ROOT, LIBS_DIR, THIS_DIR):
    if path not in sys.path:
        sys.path.append(path)

from d2l.question import SAQuestion
from d2l.questionpool import QuestionPool
from libs.fsm.fsm import FSM
from libs.fsm import fsm_timing_from_state_table as timing
from generate_random_fsms_guaranteed import (
    explorer_url,
    find_template_file,
    generate_one_variant,
)
from ST_to_timing import (
    simulate_state_sequence,
    state_answer_regex,
    state_answer_text,
    state_sequence_to_bus_wave,
    state_sequence_to_data,
)


POOL_TITLE = "FSM to Timing Diagram"
POOL_FILE = os.path.join(THIS_DIR, "fsm_to_timing_pool.csv")
NUM_QUESTIONS = 20


def normalize_fsm_json_for_parser(fsm_json):
    fsm_json = copy.deepcopy(fsm_json)
    output_names = fsm_json.get("outputs", "").split()

    if output_names:
        for node in fsm_json.get("fsmNodes", []):
            text = node.get("outputText", "").strip()
            if text and all(ch in "01" for ch in text):
                node["outputText"] = " ".join(
                    f"{name} {bit}" for name, bit in zip(output_names, text)
                )

        for arc in fsm_json.get("fsmArcs", []) + fsm_json.get("fsmSelfArcs", []):
            if "/" not in arc.get("outputText", ""):
                continue

            condition, output_part = arc["outputText"].split("/", 1)
            output_part = output_part.strip()
            if output_part and all(ch in "01" for ch in output_part.replace(" ", "")):
                arc["outputText"] = f"{condition}/{output_names[0]} {output_part}"

    return fsm_json


def generate_random_fsm_json():
    template_name = random.choice(["2state", "3state", "4state"])
    template_file = find_template_file(template_name)

    with open(template_file, "r") as file:
        base_json = json.load(file)

    fsm_json, metadata = generate_one_variant(base_json)
    fsm_json["outputs"] = "f"
    return normalize_fsm_json_for_parser(fsm_json), metadata


def fsm_from_json(fsm_json):
    temp_name = None
    try:
        with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as file:
            json.dump(fsm_json, file)
            temp_name = file.name

        fsm = FSM(temp_name)
        fsm.verify()
        return fsm
    finally:
        if temp_name and os.path.exists(temp_name):
            os.unlink(temp_name)


def fsm_to_state_table(fsm):
    state_names = fsm.state_names
    input_names = fsm.input_names
    input_combos = fsm.input_combos
    is_mealy = bool(fsm.mealy_names)

    next_states = []
    outputs = []

    for state_name in state_names:
        state_code = fsm.state_combo_map[state_name]
        row = []
        per_input_outputs = []

        for input_combo in input_combos:
            table_row = fsm.get_row(state_code, input_combo)
            next_state_code = table_row["next_states"][0]
            row.append(fsm.state_name_map[next_state_code])
            per_input_outputs.append(
                "".join(table_row[output_name] for output_name in fsm.output_names)
            )

        next_states.append(row)
        if not is_mealy and len(set(per_input_outputs)) == 1:
            outputs.append(per_input_outputs[0])
        else:
            outputs.append(" / ".join(per_input_outputs))

    return next_states, outputs, state_names, input_names


def make_wavedrom_practice_link(problem, link_text="Open WaveDrom timing diagram"):
    diag = problem["diag"]
    rows = [f'{{name: "clk", wave: "{timing.to_dotless(diag.clock)}"}},']

    for name in diag.input_names:
        rows.append(f'{{name: "{name}", wave: "{timing.to_dotless(diag.signals[name])}"}},')

    rows.append('{name: "state", wave: "", data: []},')
    rows.append(f'{{name: "f", wave: "{timing.to_dotless(diag.signals["f"])}"}},')

    payload = (
        "{ head:{text:'FSM to Timing Diagram'}, "
        f"signal:[ {' '.join(rows)} ], "
        "foot:{tick:0}}"
    )
    link = "https://dougsummerville.github.io/wavedrom/editor.html?" + urllib.parse.quote(payload)
    return f'<a href="{link}" target="_blank">{link_text}</a>'


def generate_problem():
    for _ in range(100):
        fsm_json, metadata = generate_random_fsm_json()
        fsm = fsm_from_json(fsm_json)
        next_states, outputs, state_names, input_names = fsm_to_state_table(fsm)

        diag = timing.state_table_to_random_timing_diagram(
            next_states,
            outputs,
            state_names,
            input_names=input_names,
            output_names=["f"],
            cycles=random.choice([7, 8, 9]),
            initial_state=state_names[0],
            title="FSM Timing Diagram",
        )

        state_sequence = simulate_state_sequence(
            next_states,
            state_names,
            diag.cycle_inputs,
            diag.initial_state,
        )
        state_wave = state_sequence_to_bus_wave(state_sequence)

        if state_wave.count("=") < 2 or "." not in state_wave:
            continue

        return {
            "fsm_url": explorer_url(fsm_json),
            "diag": diag,
            "state_wave": state_wave,
            "state_data": state_sequence_to_data(state_sequence),
            "state_names": state_names,
            "fsm_type": metadata["fsm_type"],
        }

    raise ValueError("Could not generate a varied FSM timing diagram")


def question_text(problem):
    diag = problem["diag"]

    return (
        "<p>Given the FSM diagram below, complete the matching timing diagram "
        "in WaveDrom. The clock, input signal(s), and output <code>f</code> are "
        "already filled in; solve only for the symbolic <code>state</code> bus wave.</p>"
        f"<p><a href=\"{problem['fsm_url']}\" target=\"_blank\">Open FSM diagram</a></p>"
        f"<p><b>Initial state:</b> {diag.initial_state}</p>"
        f"<p>{make_wavedrom_practice_link(problem)}</p>"
        "<p><b>Answer format:</b> enter only the state bus wave, such as "
        "<code>=.==..=</code>. In this wave, <code>=</code> starts a new state "
        "segment and <code>.</code> extends the previous state segment.</p>"
    )


def build_question():
    problem = generate_problem()
    question = SAQuestion(
        text=question_text(problem),
        title=POOL_TITLE,
        points=10,
        difficulty=3,
    )
    question.add_answer(state_answer_regex(problem), points=100, is_regex=True)
    question.add_feedback(
        "<p>One correct state bus wave is: "
        f"<code>{state_answer_text(problem)}</code></p>"
    )
    return question


def main():
    pool = QuestionPool(POOL_TITLE, POOL_FILE)

    for _ in range(NUM_QUESTIONS):
        pool.add_question(build_question())

    pool.package()
    print(f"Wrote {NUM_QUESTIONS} questions to {POOL_FILE}")


if __name__ == "__main__":
    main()
