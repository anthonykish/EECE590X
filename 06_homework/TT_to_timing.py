import math
import os
import random
import re
import sys
import urllib.parse


THIS_DIR = os.path.dirname(__file__)
PROJECT_ROOT = os.path.abspath(os.path.join(THIS_DIR, ".."))
LIBS_DIR = os.path.join(PROJECT_ROOT, "libs")

for path in (PROJECT_ROOT, LIBS_DIR):
    if path not in sys.path:
        sys.path.append(path)

from d2l.question import SAQuestion
from d2l.questionpool import QuestionPool
from libs.TruthTableHTML import html_tt as tt
from libs.TTtoSTtoVHDL import converter as conv
from libs.fsm import fsm_timing_from_state_table as timing


POOL_TITLE = "Truth Table to Timing Diagram"
POOL_FILE = os.path.join(THIS_DIR, "pool.csv")
NUM_QUESTIONS = 20


def min_state_bits(num_states):
    return max(1, math.ceil(math.log2(num_states)))


def state_bit_labels(num_states):
    width = min_state_bits(num_states)
    return [f"Q{i}" for i in range(width - 1, -1, -1)]


def next_state_bit_labels(num_states):
    return [f"{label}+" for label in state_bit_labels(num_states)]


def output_labels(num_outputs):
    if num_outputs == 1:
        return ["f"]
    return [f"f{i}" for i in range(num_outputs - 1, -1, -1)]


def bit_combos(width):
    return [format(i, f"0{width}b") for i in range(1 << width)]


def default_input_names(num_inputs):
    alphabet = ["x", "y", "z", "w", "v", "u"]
    if num_inputs <= len(alphabet):
        return alphabet[:num_inputs]
    return [f"x{i}" for i in range(num_inputs)]


def is_fully_connected(next_states, state_names):
    index = {state: i for i, state in enumerate(state_names)}
    adjacency = {i: set() for i in range(len(state_names))}

    for state, row in zip(state_names, next_states):
        adjacency[index[state]].update(index[next_state] for next_state in row)

    def reachable(start):
        seen = set()
        stack = [start]
        while stack:
            current = stack.pop()
            if current in seen:
                continue
            seen.add(current)
            stack.extend(adjacency[current] - seen)
        return seen

    return all(len(reachable(i)) == len(state_names) for i in range(len(state_names)))


def generate_random_state_table(n_states, m_in, p_out, machine_type, max_attempts=200):
    state_names = [f"S{i}" for i in range(n_states)]
    input_codes = bit_combos(m_in)

    for _ in range(max_attempts):
        next_states = [
            [random.choice(state_names) for _ in input_codes]
            for _state in state_names
        ]
        if not is_fully_connected(next_states, state_names):
            continue

        if machine_type == "moore":
            outputs = [
                format(random.randrange(1 << p_out), f"0{p_out}b")
                for _state in state_names
            ]
        else:
            outputs = []
            for _state in state_names:
                per_input = [
                    format(random.randrange(1 << p_out), f"0{p_out}b")
                    for _code in input_codes
                ]
                outputs.append(" / ".join(per_input))

        return next_states, outputs, state_names, machine_type

    raise ValueError("Could not generate a connected random state table")


def choose_problem_size():
    """Keep the generated truth tables readable for Brightspace."""
    return {
        "n_states": random.choice([2, 3, 4]),
        "m_in": random.choice([1, 2]),
        "p_out": 1,
        "machine_type": random.choice(["moore", "mealy"]),
        "cycles": random.choice([6, 7, 8]),
    }


def generate_problem():
    size = choose_problem_size()
    input_names = default_input_names(size["m_in"])

    next_states, outputs, state_names, machine_type = generate_random_state_table(
        size["n_states"],
        size["m_in"],
        size["p_out"],
        size["machine_type"],
    )

    q_labels = state_bit_labels(size["n_states"])
    q_next_labels = next_state_bit_labels(size["n_states"])
    y_labels = output_labels(size["p_out"])
    input_labels = q_labels + input_names

    output_columns, input_labels, table_output_labels = conv.state_table_to_truth_columns(
        next_states,
        outputs,
        state_names,
        input_labels=input_labels,
        next_state_labels=q_next_labels,
        output_labels=y_labels,
    )

    diag = timing.state_table_to_random_timing_diagram(
        next_states,
        outputs,
        state_names,
        input_names=input_names,
        output_names=y_labels,
        cycles=size["cycles"],
        initial_state=state_names[0],
        title="Truth Table Timing Diagram",
    )

    signal_order = (
        ["clk"]
        + input_names
        + sorted([name for name in diag.signals if name.startswith("Q")], reverse=True)
        + y_labels
    )

    return {
        "truth_table_html": tt.html_tt(output_columns, input_labels + table_output_labels),
        "diag": diag,
        "signal_order": signal_order,
        "machine_type": machine_type,
        "state_names": state_names,
        "state_encoding": diag.state_encoding,
    }


def signal_answer_text(diag, signal_order):
    return "; ".join(f"{name}={timing.to_dotless(diag.signals[name])}" for name in signal_order)


def output_answer_text(diag):
    return f"f={timing.to_dotless(diag.signals['f'])}"


def make_wavedrom_practice_link(diag, link_text="Open WaveDrom timing diagram"):
    rows = []
    filled_names = ["clk"] + diag.input_names

    for name in filled_names:
        rows.append(f'{{name: "{name}", wave: "{timing.to_dotless(diag.signals[name])}"}},')

    rows.append('{name: "f", wave: ""},')

    payload = (
        "{ head:{text:'Truth Table to Timing Diagram'}, "
        f"signal:[ {' '.join(rows)} ], "
        "foot:{tick:0}}"
    )
    link = "https://dougsummerville.github.io/wavedrom/editor.html?" + urllib.parse.quote(payload)
    return f'<a href="{link}" target="_blank">{link_text}</a>'


def wavedrom_row_regex(name, dotted_signal):
    dotless = timing.to_dotless(dotted_signal)
    dotted = re.escape(dotted_signal)
    dotless = re.escape(dotless)
    escaped_name = re.escape(name)

    assignment = rf"{escaped_name}\s*=\s*(?:{dotted}|{dotless})"
    wavedrom_row = (
        rf"\{{?\s*name\s*:\s*['\"]{escaped_name}['\"]\s*,\s*"
        rf"wave\s*:\s*['\"](?:{dotted}|{dotless})['\"]"
        rf"\s*\}}?"
    )
    return rf"(?:{assignment}|{wavedrom_row})"


def timing_answer_regex(diag, signal_order):
    lookaheads = []
    for name in signal_order:
        lookaheads.append(rf"(?=.*{wavedrom_row_regex(name, diag.signals[name])})")
    return r"(?is)^\s*" + "".join(lookaheads) + r".*\s*$"


def output_answer_regex(diag):
    dotted = re.escape(diag.signals["f"])
    dotless = re.escape(timing.to_dotless(diag.signals["f"]))
    raw_wave = rf"(?:{dotted}|{dotless})"
    return (
        r"(?is)^\s*(?:"
        + wavedrom_row_regex("f", diag.signals["f"])
        + rf"|{raw_wave}"
        + r")\s*,?\s*$"
    )


def state_encoding_html(state_encoding):
    rows = "".join(
        f"<tr><td style='padding:4px 12px'>{state}</td><td style='padding:4px 12px'>{code}</td></tr>"
        for state, code in state_encoding.items()
    )
    return (
        "<table style='border-collapse:collapse;text-align:center'>"
        "<tr><th style='padding:4px 12px;border-bottom:1px solid black'>State</th>"
        "<th style='padding:4px 12px;border-bottom:1px solid black'>Encoding</th></tr>"
        f"{rows}</table>"
    )


def question_text(problem):
    diag = problem["diag"]

    return (
        "<p>Given the FSM truth table below, complete the matching timing diagram "
        "in WaveDrom. The clock and input signal(s) are already filled in; solve "
        "only for the output signal <code>f</code>.</p>"
        f"{problem['truth_table_html']}"
        "<p><b>State encoding:</b></p>"
        f"{state_encoding_html(problem['state_encoding'])}"
        f"<p><b>Initial state:</b> {diag.initial_state}</p>"
        f"<p>{make_wavedrom_practice_link(diag)}</p>"
        "<p><b>Answer format:</b> enter only the output row, such as "
        "<code>f=...</code> or <code>{name: \"f\", wave: \"...\"}</code>.</p>"
        "<p>You may use dotted WaveDrom form or the equivalent full binary wave string for <code>f</code>.</p>"
    )


def build_question():
    problem = generate_problem()
    question = SAQuestion(
        text=question_text(problem),
        title=POOL_TITLE,
        points=10,
        difficulty=3,
    )
    question.add_answer(
        output_answer_regex(problem["diag"]),
        points=100,
        is_regex=True,
    )
    question.add_feedback(
        "<p>One correct compact answer is: "
        f"<code>{output_answer_text(problem['diag'])}</code></p>"
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
