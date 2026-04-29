import os
import random
import re
import sys
import urllib.parse


THIS_DIR = os.path.dirname(__file__)
PROJECT_ROOT = os.path.abspath(os.path.join(THIS_DIR, ".."))
LIBS_DIR = os.path.join(PROJECT_ROOT, "libs")

for path in (PROJECT_ROOT, LIBS_DIR, THIS_DIR):
    if path not in sys.path:
        sys.path.append(path)

from d2l.question import SAQuestion
from d2l.questionpool import QuestionPool
from libs.TruthTableHTML.html_tt import html_st
from libs.fsm import fsm_timing_from_state_table as timing
from TT_to_timing import (
    bit_combos,
    default_input_names,
    generate_random_state_table,
)


POOL_TITLE = "State Table to Timing Diagram"
POOL_FILE = os.path.join(THIS_DIR, "state_table_to_timing_pool.csv")
NUM_QUESTIONS = 20


def choose_problem_size():
    return {
        "n_states": random.choice([2, 3, 4]),
        "m_in": random.choice([1, 2]),
        "p_out": 1,
        "machine_type": random.choice(["moore", "mealy"]),
        "cycles": random.choice([7, 8, 9]),
    }


def input_headers(input_names):
    headers = []
    for code in bit_combos(len(input_names)):
        terms = [
            name if bit == "1" else f"{name}'"
            for name, bit in zip(input_names, code)
        ]
        headers.append(" ".join(terms))
    return headers


def simulate_state_sequence(next_states, state_names, cycle_inputs, initial_state):
    current_state = initial_state
    state_sequence = []

    for input_code in cycle_inputs:
        state_sequence.append(current_state)
        input_index = int(input_code, 2)
        state_index = state_names.index(current_state)
        current_state = next_states[state_index][input_index]

    return state_sequence


def state_sequence_to_bus_wave(state_sequence):
    wave = "="

    for index in range(1, len(state_sequence)):
        if state_sequence[index] == state_sequence[index - 1]:
            wave += "."
        else:
            wave += "="

    return wave


def state_sequence_to_data(state_sequence):
    data = [state_sequence[0]]

    for index in range(1, len(state_sequence)):
        if state_sequence[index] != state_sequence[index - 1]:
            data.append(state_sequence[index])

    return data


def generate_problem():
    for _ in range(100):
        size = choose_problem_size()
        input_names = default_input_names(size["m_in"])

        next_states, outputs, state_names, machine_type = generate_random_state_table(
            size["n_states"],
            size["m_in"],
            size["p_out"],
            size["machine_type"],
        )

        diag = timing.state_table_to_random_timing_diagram(
            next_states,
            outputs,
            state_names,
            input_names=input_names,
            output_names=["f"],
            cycles=size["cycles"],
            initial_state=state_names[0],
            title="State Table Timing Diagram",
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
            "state_table_html": html_st(
                next_states,
                outputs,
                input_headers=input_headers(input_names),
                state_names=state_names,
            ),
            "diag": diag,
            "state_wave": state_wave,
            "state_data": state_sequence_to_data(state_sequence),
            "state_names": state_names,
            "machine_type": machine_type,
        }

    raise ValueError("Could not generate a varied state timing diagram")


def make_wavedrom_practice_link(problem, link_text="Open WaveDrom timing diagram"):
    diag = problem["diag"]
    rows = [f'{{name: "clk", wave: "{timing.to_dotless(diag.clock)}"}},']

    for name in diag.input_names:
        rows.append(f'{{name: "{name}", wave: "{timing.to_dotless(diag.signals[name])}"}},')

    rows.append('{name: "state", wave: "", data: []},')
    rows.append(f'{{name: "f", wave: "{timing.to_dotless(diag.signals["f"])}"}},')

    payload = (
        "{ head:{text:'State Table to Timing Diagram'}, "
        f"signal:[ {' '.join(rows)} ], "
        "foot:{tick:0}}"
    )
    link = "https://dougsummerville.github.io/wavedrom/editor.html?" + urllib.parse.quote(payload)
    return f'<a href="{link}" target="_blank">{link_text}</a>'


def state_answer_text(problem):
    return problem["state_wave"]


def state_answer_regex(problem):
    wave = re.escape(problem["state_wave"])
    return (
        r"(?is)^\s*(?:"
        + wave
        + r"|state\s*=\s*"
        + wave
        + r"|\{?\s*name\s*:\s*['\"]state['\"]\s*,\s*wave\s*:\s*['\"]"
        + wave
        + r"['\"](?:\s*,\s*data\s*:\s*\[[^\]]*\])?\s*\}?"
        + r")\s*,?\s*$"
    )


def question_text(problem):
    diag = problem["diag"]

    return (
        "<p>Given the FSM state table below, complete the matching timing diagram "
        "in WaveDrom. The clock, input signal(s), and output <code>f</code> are "
        "already filled in; solve only for the symbolic <code>state</code> bus wave.</p>"
        f"{problem['state_table_html']}"
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
