from __future__ import annotations

"""
state_table_timing_tools.py

Utilities for:
- generating random condensed FSM state tables (Moore or Mealy)
- converting state tables to timing diagrams / WaveDrom signals
- converting timing-diagram traces back into condensed state tables
- generating random timing diagrams and recovering their state tables

This module is designed to sit near your FSM tools (for example in libs/fsm)
and to work with your existing converter.py, bits.py, html_st(), and wave_utils.
"""

from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, List, Tuple, Optional, Any
import copy
import random
import sys
import urllib.parse
from wave_utils.wave_utils import make_wavedrom_link_rows, make_wavedrom_image_rows

# -----------------------------------------------------------------------------
# Import bootstrap
# -----------------------------------------------------------------------------
# If this file is placed in libs/fsm, add the parent libs directory so imports
# like TTtoSTtoVHDL.converter and wave_utils.wave_utils work reliably.
THIS_FILE = Path(__file__).resolve()
for candidate in [THIS_FILE.parent, THIS_FILE.parent.parent, THIS_FILE.parent.parent.parent]:
    candidate_str = str(candidate)
    if candidate_str not in sys.path:
        sys.path.append(candidate_str)

from TTtoSTtoVHDL.converter import (  # type: ignore
    build_state_encoding,
    state_table_to_truth_columns,
    truth_columns_to_state_table,
)
from TTtoSTtoVHDL import bits  # type: ignore
from wave_utils.wave_utils import (  # type: ignore
    make_clock,
    make_wavedrom_image,
    make_wavedrom_link,
    to_dotted,
    to_dotless,
)
from TruthTableHTML.html_tt import html_st  # type: ignore


# -----------------------------------------------------------------------------
# Data containers
# -----------------------------------------------------------------------------
@dataclass(slots=True)
@dataclass
class TimingDiagramResult:
    machine_type: str
    state_names: List[str]
    input_names: List[str]
    output_names: List[str]
    input_codes: List[str]
    next_states_rows: List[List[str]]
    outputs_by_state: List[str]
    initial_state: str
    input_sequence: List[str]
    state_sequence: List[str]
    next_state_sequence: List[str]
    output_sequence: List[str]
    clk: str
    input_signals: Dict[str, str]
    state_bit_signals: Dict[str, str]
    output_bit_signals: Dict[str, str]
    signal_names: List[str]
    signal_waves: List[str]
    display_rows: List[Dict[str, Any]]
    wavedrom_link: str
    svg_path: Optional[str] = None


@dataclass(slots=True)
class RecoveredStateTable:
    machine_type: str
    next_states_rows: List[List[str]]
    outputs_by_state: List[str]
    state_names: List[str]
    input_codes: List[str]
    observed_pairs: int
    expected_pairs: int
    complete: bool


# -----------------------------------------------------------------------------
# Small helpers
# -----------------------------------------------------------------------------
def bit_combos(width: int) -> List[str]:
    if width < 0:
        raise ValueError("width must be non-negative")
    if width == 0:
        return [""]
    return [bits.int_to_bits(i, width) for i in range(1 << width)]


def default_input_names(m_in: int) -> List[str]:
    alphabet = ["x", "y", "z", "w", "v", "u"]
    if m_in > len(alphabet):
        return [f"x{i}" for i in range(m_in)]
    return alphabet[:m_in]


def input_headers_from_codes(codes: List[str], input_names: List[str]) -> List[str]:
    headers: List[str] = []
    for code in codes:
        if not code:
            headers.append("1")
            continue
        terms = []
        for name, bit in zip(input_names, code):
            terms.append(name if bit == "1" else f"{name}'")
        headers.append(" ".join(terms))
    return headers


def infer_machine_type(outputs_by_state: List[str], m_in: int) -> str:
    expected_terms = 1 << m_in
    for out in outputs_by_state:
        if "/" in out:
            parts = [p.strip() for p in out.split("/") if p.strip()]
            if len(parts) == expected_terms:
                return "mealy"
    return "moore"


def parse_mealy_outputs(cell: str, m_in: int) -> List[str]:
    parts = [p.strip() for p in cell.split("/")]
    expected = 1 << m_in
    if len(parts) != expected:
        raise ValueError(
            f"Mealy output cell '{cell}' must contain {expected} slash-separated outputs"
        )
    return parts


def state_index_map(state_names: List[str]) -> Dict[str, int]:
    return {name: i for i, name in enumerate(state_names)}


# -----------------------------------------------------------------------------
# State-table validation / generation
# -----------------------------------------------------------------------------
def validate_state_table(
    next_states_rows: List[List[str]],
    outputs_by_state: List[str],
    state_names: List[str],
    *,
    m_in: Optional[int] = None,
) -> Tuple[str, List[str]]:
    """
    Validate a condensed FSM state table.

    Returns
    -------
    (machine_type, input_codes)
    """
    if not next_states_rows:
        raise ValueError("next_states_rows cannot be empty")
    if len(next_states_rows) != len(outputs_by_state):
        raise ValueError("outputs_by_state must have one entry per state row")
    if len(next_states_rows) != len(state_names):
        raise ValueError("state_names must have one entry per state row")

    row_width = len(next_states_rows[0])
    if row_width == 0:
        raise ValueError("each next-state row must have at least one column")
    for row in next_states_rows:
        if len(row) != row_width:
            raise ValueError("all next-state rows must have the same number of columns")

    if m_in is None:
        # row_width = 2^m_in
        if row_width & (row_width - 1):
            raise ValueError("number of columns must be a power of 2")
        m_in = row_width.bit_length() - 1

    expected_cols = 1 << m_in
    if row_width != expected_cols:
        raise ValueError(f"expected {expected_cols} columns for m_in={m_in}, got {row_width}")

    state_set = set(state_names)
    for row in next_states_rows:
        for ns in row:
            if ns not in state_set:
                raise ValueError(f"unknown next state '{ns}'")

    machine_type = infer_machine_type(outputs_by_state, m_in)
    if machine_type == "mealy":
        for cell in outputs_by_state:
            parse_mealy_outputs(cell, m_in)

    return machine_type, bit_combos(m_in)


def is_fully_connected_state_table(next_states_rows: List[List[str]], state_names: List[str]) -> bool:
    idx = state_index_map(state_names)
    n = len(state_names)
    adjacency = {i: set() for i in range(n)}
    for state, row in zip(state_names, next_states_rows):
        s = idx[state]
        for ns in row:
            adjacency[s].add(idx[ns])

    def dfs(start: int) -> set[int]:
        seen: set[int] = set()
        stack = [start]
        while stack:
            cur = stack.pop()
            if cur in seen:
                continue
            seen.add(cur)
            stack.extend(adjacency[cur] - seen)
        return seen

    return all(len(dfs(i)) == n for i in range(n))


def generate_random_state_table(
    *,
    n_states: int = 4,
    m_in: int = 1,
    p_out: int = 1,
    machine_type: Optional[str] = None,
    state_prefix: str = "S",
    require_full_connectivity: bool = True,
    max_attempts: int = 200,
) -> Tuple[List[List[str]], List[str], List[str], str]:
    """
    Generate a random valid condensed FSM state table.

    Returns
    -------
    next_states_rows, outputs_by_state, state_names, machine_type
    """
    if n_states < 2:
        raise ValueError("n_states must be at least 2")
    if m_in < 1:
        raise ValueError("m_in must be at least 1")
    if p_out < 1:
        raise ValueError("p_out must be at least 1")

    if machine_type is None:
        machine_type = random.choice(["moore", "mealy"])
    machine_type = machine_type.lower()
    if machine_type not in {"moore", "mealy"}:
        raise ValueError("machine_type must be 'moore' or 'mealy'")

    state_names = [f"{state_prefix}{i}" for i in range(n_states)]
    input_codes = bit_combos(m_in)

    for _ in range(max_attempts):
        next_states_rows = []
        for _state in state_names:
            row = [random.choice(state_names) for _ in input_codes]
            next_states_rows.append(row)

        if machine_type == "moore":
            outputs_by_state = [bits.int_to_bits(random.randrange(1 << p_out), p_out) for _ in state_names]
        else:
            outputs_by_state = []
            for _state in state_names:
                per_input = [bits.int_to_bits(random.randrange(1 << p_out), p_out) for _ in input_codes]
                outputs_by_state.append(" / ".join(per_input))

        if require_full_connectivity and not is_fully_connected_state_table(next_states_rows, state_names):
            continue

        validate_state_table(next_states_rows, outputs_by_state, state_names, m_in=m_in)
        return next_states_rows, outputs_by_state, state_names, machine_type

    raise ValueError("Could not generate a fully connected random state table")


# -----------------------------------------------------------------------------
# Transition LUT / simulation
# -----------------------------------------------------------------------------
def build_transition_lut_from_state_table(
    next_states_rows: List[List[str]],
    outputs_by_state: List[str],
    state_names: List[str],
) -> Tuple[Dict[Tuple[str, str], Tuple[str, str]], str, List[str], int]:
    """
    Build LUT mapping (present_state_name, input_code) -> (next_state_name, output_bits)
    from a condensed state table.
    """
    machine_type, input_codes = validate_state_table(next_states_rows, outputs_by_state, state_names)
    m_in = (len(input_codes) - 1).bit_length() if len(input_codes) > 1 else 0

    lut: Dict[Tuple[str, str], Tuple[str, str]] = {}

    if machine_type == "moore":
        p_out = len(outputs_by_state[0])
        for ps_name, row, y in zip(state_names, next_states_rows, outputs_by_state):
            for x_code, ns_name in zip(input_codes, row):
                lut[(ps_name, x_code)] = (ns_name, y)
    else:
        sample_outputs = parse_mealy_outputs(outputs_by_state[0], m_in)
        p_out = len(sample_outputs[0])
        for ps_name, row, cell in zip(state_names, next_states_rows, outputs_by_state):
            per_input_outputs = parse_mealy_outputs(cell, m_in)
            for x_code, ns_name, y in zip(input_codes, row, per_input_outputs):
                lut[(ps_name, x_code)] = (ns_name, y)

    return lut, machine_type, input_codes, p_out


def random_input_sequence(
    *,
    m_in: int,
    cycles: int,
    allow_repeat: bool = True,
) -> List[str]:
    codes = bit_combos(m_in)
    if cycles <= 0:
        raise ValueError("cycles must be positive")
    if allow_repeat:
        return [random.choice(codes) for _ in range(cycles)]

    seq = []
    while len(seq) < cycles:
        block = codes[:]
        random.shuffle(block)
        seq.extend(block)
    return seq[:cycles]


def simulate_fsm_from_state_table(
    next_states_rows: List[List[str]],
    outputs_by_state: List[str],
    state_names: List[str],
    *,
    input_sequence: List[str],
    initial_state: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Simulate a condensed FSM state table across the provided input sequence.

    Returns present-state, next-state, and output sequences at cycle granularity.
    """
    lut, machine_type, input_codes, p_out = build_transition_lut_from_state_table(
        next_states_rows, outputs_by_state, state_names
    )

    if initial_state is None:
        initial_state = state_names[0]
    if initial_state not in state_names:
        raise ValueError("initial_state must be in state_names")

    for code in input_sequence:
        if code not in input_codes:
            raise ValueError(f"input code '{code}' not valid for this FSM")

    ps_seq: List[str] = []
    ns_seq: List[str] = []
    y_seq: List[str] = []

    current = initial_state
    for x_code in input_sequence:
        ps_seq.append(current)
        ns, y = lut[(current, x_code)]
        ns_seq.append(ns)
        y_seq.append(y)
        current = ns

    return {
        "machine_type": machine_type,
        "input_codes": input_codes,
        "p_out": p_out,
        "initial_state": initial_state,
        "present_states": ps_seq,
        "next_states": ns_seq,
        "outputs": y_seq,
    }


# -----------------------------------------------------------------------------
# Timing-diagram signal creation
# -----------------------------------------------------------------------------
def _expand_per_cycle(values: Iterable[str], *, prefill: Optional[str] = None) -> str:
    """
    Expand one value per cycle into a half-cycle dotless trace.

    If values are [a,b,c], returns prefill + aa bb cc in dotless form.
    """
    vals = list(values)
    if not vals:
        raise ValueError("values cannot be empty")
    first = vals[0] if prefill is None else prefill
    pieces = [first]
    for v in vals:
        pieces.append(v)
        pieces.append(v)
    return "".join(pieces)


def _clock_for_cycles(cycles: int) -> str:
    # length = initial sample + 2 samples per cycle
    length = 1 + 2 * cycles
    return make_clock(length=length, period=2, first_rising_edge=1)

def _state_trace_to_bus_wave(state_trace: List[str]) -> Tuple[str, List[str]]:
    """
    Convert a symbolic state trace like:
        ["S0", "S0", "S1", "S1", "S0"]
    into WaveDrom bus representation:
        wave="=.=.="
        data=["S0", "S1", "S0"]
    """
    if not state_trace:
        return "", []

    wave = "="
    data = [state_trace[0]]

    for i in range(1, len(state_trace)):
        if state_trace[i] == state_trace[i - 1]:
            wave += "."
        else:
            wave += "="
            data.append(state_trace[i])

    return wave, data


def simulation_to_timing_signals(
    next_states_rows: List[List[str]],
    outputs_by_state: List[str],
    state_names: List[str],
    *,
    input_names: Optional[List[str]] = None,
    input_sequence: Optional[List[str]] = None,
    cycles: int = 8,
    initial_state: Optional[str] = None,
    title: str = "FSM Timing Diagram",
    out_svg: Optional[str] = None,
) -> TimingDiagramResult:
    """
    Convert a condensed state table to timing-diagram signals.

    Keeps internal state-bit signals for reconstruction, but displays a symbolic
    'state' bus row in the timing diagram.
    """
    machine_type, input_codes = validate_state_table(
        next_states_rows, outputs_by_state, state_names
    )
    m_in = (len(input_codes) - 1).bit_length() if len(input_codes) > 1 else 0

    input_names = default_input_names(m_in) if input_names is None else input_names
    if len(input_names) != m_in:
        raise ValueError("input_names length must match number of input bits")

    if input_sequence is None:
        input_sequence = random_input_sequence(m_in=m_in, cycles=cycles)
    else:
        cycles = len(input_sequence)

    sim = simulate_fsm_from_state_table(
        next_states_rows,
        outputs_by_state,
        state_names,
        input_sequence=input_sequence,
        initial_state=initial_state,
    )

    encoding = build_state_encoding(state_names)
    k_state = len(next(iter(encoding.values())))
    p_out = sim["p_out"]

    # Exam-style output names
    output_names = [f"f{i}" for i in range(p_out)]

    clk = _clock_for_cycles(cycles)

    # ------------------------------------------------------------------
    # Inputs: stable across each cycle
    # ------------------------------------------------------------------
    input_signals: Dict[str, str] = {}
    for bit_idx, name in enumerate(input_names):
        per_cycle = [code[bit_idx] for code in input_sequence]
        input_signals[name] = to_dotted(
            _expand_per_cycle(per_cycle, prefill=per_cycle[0])
        )

    # ------------------------------------------------------------------
    # Internal state-bit signals: KEEP THESE for timing -> state-table
    # reconstruction, even though we won't display them as rows.
    # ------------------------------------------------------------------
    ps_bits_per_cycle = [encoding[s] for s in sim["present_states"]]
    first_state_bits = encoding[sim["initial_state"]]

    state_bit_signals: Dict[str, str] = {}
    for bit_idx in range(k_state):
        per_cycle = [code[bit_idx] for code in ps_bits_per_cycle]
        state_bit_signals[f"Q{k_state - 1 - bit_idx}"] = to_dotted(
            _expand_per_cycle(per_cycle, prefill=first_state_bits[bit_idx])
        )

    # ------------------------------------------------------------------
    # Outputs
    # ------------------------------------------------------------------
    output_bit_signals: Dict[str, str] = {}
    for bit_idx, out_name in enumerate(output_names):
        per_cycle = [code[bit_idx] for code in sim["outputs"]]
        output_bit_signals[out_name] = to_dotted(
            _expand_per_cycle(per_cycle, prefill=per_cycle[0])
        )

    # ------------------------------------------------------------------
    # Symbolic state bus for display
    # ------------------------------------------------------------------
    state_wave, state_data = _state_trace_to_bus_wave(sim["present_states"])

    # Student-facing display rows
    display_rows: List[Dict[str, Any]] = []
    display_rows.append({"name": "clk", "wave": clk})

    for n in input_names:
        display_rows.append({"name": n, "wave": input_signals[n]})

    display_rows.append({
        "name": "state",
        "wave": state_wave,
        "data": state_data,
    })

    for n in output_names:
        display_rows.append({"name": n, "wave": output_bit_signals[n]})

    # Keep these for compatibility with existing result usage
    signal_names = ["clk"] + input_names + ["state"] + output_names
    signal_waves = (
        [clk]
        + [input_signals[n] for n in input_names]
        + [state_wave]
        + [output_bit_signals[n] for n in output_names]
    )

    # Bus-aware WaveDrom helpers
    link_html = make_wavedrom_link_rows(title, display_rows)
    svg_path = None
    if out_svg:
        make_wavedrom_image_rows(title, display_rows, out_filename=out_svg)
        svg_path = out_svg

    return TimingDiagramResult(
        machine_type=machine_type,
        state_names=state_names,
        input_names=input_names,
        output_names=output_names,
        input_codes=input_codes,
        next_states_rows=copy.deepcopy(next_states_rows),
        outputs_by_state=copy.deepcopy(outputs_by_state),
        initial_state=sim["initial_state"],
        input_sequence=input_sequence,
        state_sequence=sim["present_states"],
        next_state_sequence=sim["next_states"],
        output_sequence=sim["outputs"],
        clk=clk,
        input_signals=input_signals,
        state_bit_signals=state_bit_signals,   # keep for reconstruction
        output_bit_signals=output_bit_signals,
        signal_names=signal_names,
        signal_waves=signal_waves,
        display_rows=display_rows,
        svg_path=svg_path,
        wavedrom_link=link_html,
    )


def state_table_to_timing_diagram(
    next_states_rows: List[List[str]],
    outputs_by_state: List[str],
    state_names: List[str],
    **kwargs: Any,
) -> TimingDiagramResult:
    return simulation_to_timing_signals(next_states_rows, outputs_by_state, state_names, **kwargs)


# -----------------------------------------------------------------------------
# Timing-diagram -> state-table reconstruction
# -----------------------------------------------------------------------------
def _cycle_values_from_signal(signal: str, cycles: int) -> List[str]:
    dotless = to_dotless(signal)
    expected_len = 1 + 2 * cycles
    if len(dotless) != expected_len:
        raise ValueError(
            f"signal length {len(dotless)} does not match expected {expected_len} for {cycles} cycles"
        )
    # One stable value from the middle of each cycle region.
    return [dotless[1 + 2 * i] for i in range(cycles)]


def timing_signals_to_state_table(
    *,
    input_signals: Dict[str, str],
    state_bit_signals: Dict[str, str],
    output_bit_signals: Dict[str, str],
    state_names: Optional[List[str]] = None,
    state_prefix: str = "S",
) -> RecoveredStateTable:
    """
    Reconstruct a condensed state table from timing-diagram traces.

    Supports non-power-of-two state counts such as 3 states.
    Only the actual encoded states are treated as real states.
    """
    if not input_signals:
        raise ValueError("input_signals cannot be empty")
    if not state_bit_signals:
        raise ValueError("state_bit_signals cannot be empty")
    if not output_bit_signals:
        raise ValueError("output_bit_signals cannot be empty")

    sample_signal = next(iter(input_signals.values()))
    cycles = (len(to_dotless(sample_signal)) - 1) // 2

    input_names_sorted = list(input_signals.keys())
    state_bits_sorted = sorted(state_bit_signals.keys(), reverse=True)
    output_names_sorted = list(output_bit_signals.keys())

    in_per_cycle = {name: _cycle_values_from_signal(sig, cycles) for name, sig in input_signals.items()}
    q_per_cycle = {name: _cycle_values_from_signal(sig, cycles) for name, sig in state_bit_signals.items()}
    z_per_cycle = {name: _cycle_values_from_signal(sig, cycles) for name, sig in output_bit_signals.items()}

    ps_codes: List[str] = []
    x_codes: List[str] = []
    y_codes: List[str] = []
    ns_codes: List[str] = []

    for i in range(cycles - 1):
        ps = "".join(q_per_cycle[name][i] for name in state_bits_sorted)
        x = "".join(in_per_cycle[name][i] for name in input_names_sorted)
        y = "".join(z_per_cycle[name][i] for name in output_names_sorted)
        ns = "".join(q_per_cycle[name][i + 1] for name in state_bits_sorted)

        ps_codes.append(ps)
        x_codes.append(x)
        y_codes.append(y)
        ns_codes.append(ns)

    m_in = len(input_names_sorted)
    input_codes = bit_combos(m_in)

    observed_state_codes = sorted(set(ps_codes) | set(ns_codes), key=lambda b: int(b, 2))

    if state_names is None:
        state_names = [f"{state_prefix}{i}" for i in range(len(observed_state_codes))]
        ordered_state_codes = observed_state_codes
        code_to_name = {code: name for code, name in zip(ordered_state_codes, state_names)}
    else:
        encoding = build_state_encoding(state_names)
        code_to_name = {code: name for name, code in encoding.items()}
        ordered_state_codes = [encoding[name] for name in state_names]

        unknown_codes = [code for code in observed_state_codes if code not in code_to_name]
        if unknown_codes:
            raise ValueError(
                f"Observed state codes {unknown_codes} are not valid for state_names={state_names}"
            )

    observed: Dict[Tuple[str, str], Tuple[str, str]] = {}
    for ps, x, ns, y in zip(ps_codes, x_codes, ns_codes, y_codes):
        observed[(ps, x)] = (ns, y)

    expected_pairs = len(state_names) * len(input_codes)

    next_states_rows: List[List[str]] = []
    outputs_by_state: List[str] = []
    machine_type = "moore"

    for ps_code in ordered_state_codes:
        row: List[str] = []
        per_input_outputs: List[str] = []

        for x_code in input_codes:
            key = (ps_code, x_code)
            if key not in observed:
                row.append("?")
                per_input_outputs.append("?")
            else:
                ns_code, y = observed[key]
                row.append(code_to_name.get(ns_code, "?"))
                per_input_outputs.append(y)

        known_outputs = [v for v in per_input_outputs if v != "?"]
        if known_outputs and len(set(known_outputs)) == 1 and "?" not in per_input_outputs:
            outputs_by_state.append(known_outputs[0])
        else:
            machine_type = "mealy"
            outputs_by_state.append(" / ".join(per_input_outputs))

        next_states_rows.append(row)

    complete = len(observed) == expected_pairs and all("?" not in row for row in next_states_rows)
    if machine_type == "moore" and any("?" in out for out in outputs_by_state):
        complete = False

    return RecoveredStateTable(
        machine_type=machine_type,
        next_states_rows=next_states_rows,
        outputs_by_state=outputs_by_state,
        state_names=state_names,
        input_codes=input_codes,
        observed_pairs=len(observed),
        expected_pairs=expected_pairs,
        complete=complete,
    )


# -----------------------------------------------------------------------------
# Random timing generation with round-trip back to state table
# -----------------------------------------------------------------------------
def random_state_table_to_timing_diagram(
    *,
    n_states: int = 4,
    m_in: int = 1,
    p_out: int = 1,
    machine_type: Optional[str] = None,
    cycles: int = 10,
    require_full_connectivity: bool = True,
    out_svg: Optional[str] = None,
    title: str = "Random FSM Timing Diagram",
) -> TimingDiagramResult:
    next_states_rows, outputs_by_state, state_names, machine_type = generate_random_state_table(
        n_states=n_states,
        m_in=m_in,
        p_out=p_out,
        machine_type=machine_type,
        require_full_connectivity=require_full_connectivity,
    )
    return state_table_to_timing_diagram(
        next_states_rows,
        outputs_by_state,
        state_names,
        input_names=default_input_names(m_in),
        cycles=cycles,
        out_svg=out_svg,
        title=title,
    )


def random_timing_diagram_to_state_table(
    *,
    n_states: int = 4,
    m_in: int = 1,
    p_out: int = 1,
    machine_type: Optional[str] = None,
    cycles: int = 24,
    require_full_connectivity: bool = True,
    max_attempts: int = 50,
    out_svg: Optional[str] = None,
    title: str = "Random Timing Diagram",
) -> Tuple[TimingDiagramResult, RecoveredStateTable]:
    """
    Generate a random FSM, make a random timing diagram from it, then recover
    a state table from the timing traces. Retries until the recovered table is complete.
    """
    for _ in range(max_attempts):
        diag = random_state_table_to_timing_diagram(
            n_states=n_states,
            m_in=m_in,
            p_out=p_out,
            machine_type=machine_type,
            cycles=cycles,
            require_full_connectivity=require_full_connectivity,
            out_svg=out_svg,
            title=title,
        )
        recovered = timing_signals_to_state_table(
            input_signals=diag.input_signals,
            state_bit_signals=diag.state_bit_signals,
            output_bit_signals=diag.output_bit_signals,
            state_names=diag.state_names,
        )
        if recovered.complete:
            return diag, recovered

    raise ValueError("Could not generate a timing diagram with full state/input coverage")


# -----------------------------------------------------------------------------
# HTML / convenience wrappers
# -----------------------------------------------------------------------------
def state_table_html(
    next_states_rows: List[List[str]],
    outputs_by_state: List[str],
    state_names: List[str],
    *,
    input_names: Optional[List[str]] = None,
) -> str:
    machine_type, input_codes = validate_state_table(next_states_rows, outputs_by_state, state_names)
    m_in = (len(input_codes) - 1).bit_length() if len(input_codes) > 1 else 0
    input_names = default_input_names(m_in) if input_names is None else input_names
    headers = input_headers_from_codes(input_codes, input_names)
    return html_st(next_states_rows, outputs_by_state, input_headers=headers, state_names=state_names)


def make_timing_link(result: TimingDiagramResult, link_text: str = "WaveDrom Link") -> str:
    return make_wavedrom_link(
        "FSM Timing Diagram",
        result.signal_names,
        result.signal_waves,
        fill_sig_names=[],
        link_text=link_text,
    )


# -----------------------------------------------------------------------------
# Demo
# -----------------------------------------------------------------------------
def _demo() -> None:
    print("--- Example 1: random state table -> timing diagram ---")
    diag = random_state_table_to_timing_diagram(
        n_states=3,
        m_in=1,
        p_out=1,
        machine_type=None,
        cycles=12,
        title="Demo FSM Timing",
        out_svg="fsm_timing_demo.svg",
    )
    print("machine type:", diag.machine_type)
    print("state names:", diag.state_names)
    print("input sequence:", diag.input_sequence)
    print("state table:")
    for state, row, out in zip(diag.state_names, diag.next_states_rows, diag.outputs_by_state):
        print(f"  {state}: {row} | {out}")
    print("svg:", diag.svg_path)
    print("link:", diag.wavedrom_link)

    print("\n--- Example 2: random timing diagram -> recovered state table ---")
    diag2, recovered = random_timing_diagram_to_state_table(
        n_states=2,
        m_in=1,
        p_out=1,
        cycles=20,
        title="Round Trip FSM Timing",
        out_svg="fsm_roundtrip_demo.svg",
    )
    print("generated machine type:", diag2.machine_type)
    print("recovered machine type:", recovered.machine_type)
    print(f"coverage: {recovered.observed_pairs}/{recovered.expected_pairs}")
    for state, row, out in zip(recovered.state_names, recovered.next_states_rows, recovered.outputs_by_state):
        print(f"  {state}: {row} | {out}")


if __name__ == "__main__":
    _demo()
