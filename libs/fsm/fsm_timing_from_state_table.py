"""
fsm_timing_from_state_table.py

Generate random synchronous timing diagrams from a condensed FSM state table.

This file is the bridge between your state-table utilities and your WaveDrom
helpers. It does four main things:

1. Validates a condensed FSM state table.
2. Builds a transition lookup table from that state table.
3. Generates a random input sequence and simulates the FSM across clock cycles.
4. Renders the resulting timing diagram using your wave_utils helpers.

Supported state table formats
-----------------------------
Moore:
    next_states_rows = [
        ["S0", "S1"],
        ["S1", "S0"],
    ]
    outputs_by_state = ["0", "1"]

Mealy (packed outputs in input-column order):
    next_states_rows = [
        ["S0", "S1"],
        ["S1", "S0"],
    ]
    outputs_by_state = ["0 / 1", "1 / 0"]

Input-column order is assumed to be standard binary order:
    0, 1                for 1 input
    00, 01, 10, 11      for 2 inputs
    etc.

Typical workflow
----------------
1. Define or obtain a state table.
2. Call simulate_fsm_from_state_table(...).
3. Call render_timing_diagram(...) or make_timing_link(...).

This file intentionally works even if your repo layout changes a little. It
tries to import your existing wave_utils helpers first, and falls back to local
implementations if needed.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Sequence, Tuple
import math
import random
import sys
import urllib.parse


# -----------------------------------------------------------------------------
# Flexible imports / fallbacks
# -----------------------------------------------------------------------------
PROJECT_ROOT = Path(__file__).resolve().parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.append(str(PROJECT_ROOT))


def _fallback_to_dotted(dotless: str) -> str:
    dotted = ""
    last = ""
    for ch in dotless:
        if ch == last:
            dotted += "."
        else:
            dotted += ch
            last = ch
    return dotted


def _fallback_to_dotless(dotted: str) -> str:
    dotless = ""
    last = "0"
    seen = False
    for ch in dotted:
        if ch == ".":
            if not seen:
                raise ValueError("dotted waveform cannot start with '.'")
            dotless += last
        else:
            dotless += ch
            last = ch
            seen = True
    return dotless


def _fallback_make_clock(length: int, period: int = 2, first_rising_edge: int = 1) -> str:
    if period % 2 != 0:
        raise ValueError("period must be even")
    values = []
    val = 0
    for i in range(length + period):
        if i % (period // 2) == 0:
            val = 1 - val
        values.append(str(val))
    start = period - first_rising_edge
    return _fallback_to_dotted("".join(values[start:start + length]))


try:
    from wave_utils.wave_utils import (
        to_dotted as _wave_to_dotted,
        to_dotless as _wave_to_dotless,
        make_clock as _wave_make_clock,
        make_wavedrom_image as _wave_make_wavedrom_image,
        make_wavedrom_link as _wave_make_wavedrom_link,
    )
except Exception:
    _wave_to_dotted = _fallback_to_dotted
    _wave_to_dotless = _fallback_to_dotless
    _wave_make_clock = _fallback_make_clock
    _wave_make_wavedrom_image = None
    _wave_make_wavedrom_link = None


to_dotted = _wave_to_dotted
to_dotless = _wave_to_dotless
make_clock = _wave_make_clock


# -----------------------------------------------------------------------------
# Data containers
# -----------------------------------------------------------------------------
@dataclass(slots=True)
class TimingDiagramResult:
    fsm_type: str
    input_names: List[str]
    output_names: List[str]
    state_names: List[str]
    state_encoding: Dict[str, str]
    initial_state: str
    cycles: int
    input_patterns: List[str]
    cycle_inputs: List[str]
    clock: str
    signals: Dict[str, str]
    title: str


# -----------------------------------------------------------------------------
# Low-level helpers
# -----------------------------------------------------------------------------
def min_bits(n: int) -> int:
    return max(1, math.ceil(math.log2(max(1, n))))


def int_to_bits(value: int, width: int) -> str:
    return format(value, f"0{width}b")


def all_bitstrings(width: int) -> List[str]:
    return [int_to_bits(i, width) for i in range(1 << width)]


def default_input_names(width: int) -> List[str]:
    if width == 1:
        return ["X"]
    return [f"X{i}" for i in range(width - 1, -1, -1)]


def make_input_patterns(input_names: Sequence[str]) -> List[str]:
    patterns = []
    for bits in all_bitstrings(len(input_names)):
        terms = [name if bit == "1" else f"{name}'" for name, bit in zip(input_names, bits)]
        patterns.append(" ".join(terms))
    return patterns


def infer_input_width(next_states_rows: Sequence[Sequence[str]]) -> int:
    cols = len(next_states_rows[0])
    if cols == 0 or (cols & (cols - 1)) != 0:
        raise ValueError("number of next-state columns must be a positive power of 2")
    return cols.bit_length() - 1


def infer_fsm_type(outputs_by_state: Sequence[str], num_input_patterns: int) -> str:
    has_slash = any("/" in s for s in outputs_by_state)
    if not has_slash:
        return "moore"

    # Require every row to look packed if any row does
    for row in outputs_by_state:
        parts = [p.strip() for p in row.split("/")]
        if len(parts) != num_input_patterns:
            raise ValueError(
                f"packed Mealy output row '{row}' must contain {num_input_patterns} slash-separated entries"
            )
    return "mealy"


def infer_output_width(outputs_by_state: Sequence[str], fsm_type: str) -> int:
    sample = outputs_by_state[0].strip()
    if fsm_type == "moore":
        sample = sample.replace(" ", "")
        if not sample or any(ch not in "01" for ch in sample):
            raise ValueError(f"invalid Moore output '{outputs_by_state[0]}'")
        return len(sample)

    parts = [p.strip().replace(" ", "") for p in sample.split("/")]
    if not parts or any(not p for p in parts):
        raise ValueError(f"invalid packed Mealy output '{outputs_by_state[0]}'")
    width = len(parts[0])
    for p in parts:
        if len(p) != width or any(ch not in "01" for ch in p):
            raise ValueError(f"invalid packed Mealy output '{outputs_by_state[0]}'")
    return width


def build_state_encoding(state_names: Sequence[str]) -> Dict[str, str]:
    width = min_bits(len(state_names))
    return {name: int_to_bits(i, width) for i, name in enumerate(state_names)}


# -----------------------------------------------------------------------------
# State-table validation + LUT build
# -----------------------------------------------------------------------------
def validate_condensed_state_table(
    next_states_rows: Sequence[Sequence[str]],
    outputs_by_state: Sequence[str],
    state_names: Sequence[str],
) -> Tuple[str, int, int]:
    """
    Validate a condensed state table.

    Returns
    -------
    (fsm_type, m_in, p_out)
    """
    if not next_states_rows:
        raise ValueError("next_states_rows cannot be empty")
    if len(next_states_rows) != len(outputs_by_state):
        raise ValueError("outputs_by_state must have one entry per state row")
    if len(next_states_rows) != len(state_names):
        raise ValueError("state_names must have one entry per state row")
    if len(set(state_names)) != len(state_names):
        raise ValueError("state_names must be unique")

    num_cols = len(next_states_rows[0])
    if num_cols == 0:
        raise ValueError("state table must have at least one input column")

    for row in next_states_rows:
        if len(row) != num_cols:
            raise ValueError("all next-state rows must have the same number of columns")
        for ns in row:
            if ns not in state_names:
                raise ValueError(f"unknown next state '{ns}' in state table")

    m_in = infer_input_width(next_states_rows)
    num_patterns = 1 << m_in
    fsm_type = infer_fsm_type(outputs_by_state, num_patterns)
    p_out = infer_output_width(outputs_by_state, fsm_type)

    if fsm_type == "moore":
        for y in outputs_by_state:
            bits = y.replace(" ", "")
            if len(bits) != p_out or any(ch not in "01" for ch in bits):
                raise ValueError(f"invalid Moore output row '{y}'")
    else:
        for row in outputs_by_state:
            parts = [p.strip().replace(" ", "") for p in row.split("/")]
            if len(parts) != num_patterns:
                raise ValueError(f"invalid packed Mealy row '{row}'")
            for part in parts:
                if len(part) != p_out or any(ch not in "01" for ch in part):
                    raise ValueError(f"invalid Mealy output bits '{part}'")

    return fsm_type, m_in, p_out


def build_transition_lut_from_state_table(
    next_states_rows: Sequence[Sequence[str]],
    outputs_by_state: Sequence[str],
    state_names: Sequence[str],
) -> Tuple[str, Dict[Tuple[str, str], Tuple[str, str]], Dict[str, str], int, int]:
    """
    Build a LUT keyed by (present_state_name, input_bits).

    Returns
    -------
    (fsm_type, lut, moore_outputs, m_in, p_out)
    """
    fsm_type, m_in, p_out = validate_condensed_state_table(next_states_rows, outputs_by_state, state_names)

    lut: Dict[Tuple[str, str], Tuple[str, str]] = {}
    moore_outputs: Dict[str, str] = {}
    patterns = all_bitstrings(m_in)

    for state_name, row, out_row in zip(state_names, next_states_rows, outputs_by_state):
        if fsm_type == "moore":
            moore_outputs[state_name] = out_row.replace(" ", "")
            out_parts = [moore_outputs[state_name]] * len(patterns)
        else:
            out_parts = [p.strip().replace(" ", "") for p in out_row.split("/")]

        for x_bits, ns_name, y_bits in zip(patterns, row, out_parts):
            lut[(state_name, x_bits)] = (ns_name, y_bits)

    return fsm_type, lut, moore_outputs, m_in, p_out


# -----------------------------------------------------------------------------
# Random input generation
# -----------------------------------------------------------------------------
def generate_random_cycle_inputs(
    m_in: int,
    cycles: int,
    *,
    hold_probability: float = 0.35,
    rng: Optional[random.Random] = None,
) -> List[str]:
    """
    Generate one input vector per cycle.

    hold_probability controls how often the next cycle reuses the previous input.
    """
    rng = rng or random
    choices = all_bitstrings(m_in)

    sequence = [rng.choice(choices)]
    for _ in range(1, cycles):
        if rng.random() < hold_probability:
            sequence.append(sequence[-1])
        else:
            sequence.append(rng.choice(choices))
    return sequence


# -----------------------------------------------------------------------------
# Simulation
# -----------------------------------------------------------------------------
def simulate_fsm_from_state_table(
    next_states_rows: Sequence[Sequence[str]],
    outputs_by_state: Sequence[str],
    state_names: Sequence[str],
    *,
    input_names: Optional[Sequence[str]] = None,
    output_names: Optional[Sequence[str]] = None,
    cycles: int = 8,
    initial_state: Optional[str] = None,
    title: str = "FSM Timing Diagram",
    rng: Optional[random.Random] = None,
) -> TimingDiagramResult:
    """
    Simulate a synchronous FSM from a condensed state table.

    The clock has a rising edge at indices 1, 3, 5, ...
    Inputs remain stable within each cycle.
    State updates on each rising edge.
    """
    rng = rng or random
    fsm_type, lut, moore_outputs, m_in, p_out = build_transition_lut_from_state_table(
        next_states_rows, outputs_by_state, state_names
    )

    if input_names is None:
        input_names = default_input_names(m_in)
    else:
        input_names = list(input_names)
        if len(input_names) != m_in:
            raise ValueError(f"expected {m_in} input names, got {len(input_names)}")

    if output_names is None:
        output_names = ["F"] if p_out == 1 else [f"F{i}" for i in range(p_out - 1, -1, -1)]
    else:
        output_names = list(output_names)
        if len(output_names) != p_out:
            raise ValueError(f"expected {p_out} output names, got {len(output_names)}")

    if initial_state is None:
        initial_state = state_names[0]
    if initial_state not in state_names:
        raise ValueError(f"unknown initial state '{initial_state}'")

    state_encoding = build_state_encoding(state_names)
    cycle_inputs = generate_random_cycle_inputs(m_in, cycles, rng=rng)

    # Timeline length: one sample before first edge, then one sample per edge pair,
    # plus a trailing sample after the last cycle.
    t_len = 2 * cycles + 1
    clock = make_clock(t_len, period=2, first_rising_edge=1)

    state_values: List[str] = [""] * t_len
    output_values: List[str] = [""] * t_len
    input_values_per_bit: List[List[str]] = [[""] * t_len for _ in range(m_in)]

    current_state = initial_state

    for cycle_idx, x_bits in enumerate(cycle_inputs):
        t_even = 2 * cycle_idx
        t_odd = t_even + 1

        # Inputs are stable through the whole cycle.
        for bit_i, bit in enumerate(x_bits):
            input_values_per_bit[bit_i][t_even] = bit
            input_values_per_bit[bit_i][t_odd] = bit

        state_values[t_even] = state_encoding[current_state]

        next_state, mealy_y = lut[(current_state, x_bits)]

        if fsm_type == "moore":
            output_values[t_even] = moore_outputs[current_state]
        else:
            output_values[t_even] = mealy_y

        # Rising edge: state updates.
        current_state = next_state
        state_values[t_odd] = state_encoding[current_state]

        if fsm_type == "moore":
            output_values[t_odd] = moore_outputs[current_state]
        else:
            # After the edge, the output is combinational on the new state and same inputs.
            output_values[t_odd] = lut[(current_state, x_bits)][1]

    # Fill trailing sample with final state and hold last input.
    t_last = t_len - 1
    last_x = cycle_inputs[-1]
    for bit_i, bit in enumerate(last_x):
        input_values_per_bit[bit_i][t_last] = bit
    state_values[t_last] = state_encoding[current_state]
    if fsm_type == "moore":
        output_values[t_last] = moore_outputs[current_state]
    else:
        output_values[t_last] = lut[(current_state, last_x)][1]

    # Convert sampled strings into WaveDrom dotted signals.
    signals: Dict[str, str] = {"clk": clock}

    for name, values in zip(input_names, input_values_per_bit):
        signals[name] = to_dotted("".join(values))

    k_state = len(next(iter(state_encoding.values())))
    for bit_i in range(k_state):
        bit_values = "".join(state[bit_i] for state in state_values)
        signals[f"Q{(k_state - 1) - bit_i}"] = to_dotted(bit_values)

    for bit_i in range(p_out):
        bit_values = "".join(y[bit_i] for y in output_values)
        signals[output_names[bit_i]] = to_dotted(bit_values)

    return TimingDiagramResult(
        fsm_type=fsm_type,
        input_names=list(input_names),
        output_names=list(output_names),
        state_names=list(state_names),
        state_encoding=state_encoding,
        initial_state=initial_state,
        cycles=cycles,
        input_patterns=make_input_patterns(input_names),
        cycle_inputs=cycle_inputs,
        clock=clock,
        signals=signals,
        title=title,
    )


# -----------------------------------------------------------------------------
# Rendering helpers
# -----------------------------------------------------------------------------
def render_timing_diagram(
    result: TimingDiagramResult,
    *,
    out_filename: str = "fsm_timing.svg",
    signal_order: Optional[Sequence[str]] = None,
) -> str:
    """
    Render the timing diagram to an SVG using wave_utils.make_wavedrom_image.

    Returns the output filename.
    """
    if _wave_make_wavedrom_image is None:
        raise RuntimeError(
            "make_wavedrom_image could not be imported from wave_utils.wave_utils. "
            "Copy this file into your repo or fix your Python path."
        )

    if signal_order is None:
        signal_order = ["clk"] + result.input_names + sorted(
            [k for k in result.signals if k.startswith("Q")], reverse=True
        ) + result.output_names

    gen_sigs = [result.signals[name] for name in signal_order]
    _wave_make_wavedrom_image(result.title, list(signal_order), gen_sigs, out_filename=out_filename)
    return out_filename


def make_timing_link(
    result: TimingDiagramResult,
    *,
    signal_order: Optional[Sequence[str]] = None,
    link_text: str = "WaveDrom Link",
) -> str:
    """
    Build a WaveDrom editor link using wave_utils.make_wavedrom_link if available.
    Falls back to a direct GitHub WaveDrom editor link.
    """
    if signal_order is None:
        signal_order = ["clk"] + result.input_names + sorted(
            [k for k in result.signals if k.startswith("Q")], reverse=True
        ) + result.output_names

    sig_names = list(signal_order)
    sigs = [result.signals[name] for name in sig_names]

    if _wave_make_wavedrom_link is not None:
        return _wave_make_wavedrom_link(result.title, sig_names, sigs, [], link_text=link_text, use_dotless=False)

    # Fallback: generate the editor URL directly.
    base_link = "https://dougsummerville.github.io/wavedrom/editor.html?"
    lines = []
    for name, sig in zip(sig_names, sigs):
        lines.append(f'{{name: "{name}", wave: "{to_dotless(sig)}"}},')
    payload = "{ head:{text:'%s'}, signal:[ %s ], foot:{tick:0}}" % (result.title, " ".join(lines))
    url = base_link + urllib.parse.quote(payload)
    return f'<a href="{url}" target="_blank">{link_text}</a>'


# -----------------------------------------------------------------------------
# Convenience wrapper
# -----------------------------------------------------------------------------
def state_table_to_random_timing_diagram(
    next_states_rows: Sequence[Sequence[str]],
    outputs_by_state: Sequence[str],
    state_names: Sequence[str],
    *,
    input_names: Optional[Sequence[str]] = None,
    output_names: Optional[Sequence[str]] = None,
    cycles: int = 8,
    initial_state: Optional[str] = None,
    title: str = "FSM Timing Diagram",
    out_filename: Optional[str] = None,
    rng: Optional[random.Random] = None,
) -> TimingDiagramResult:
    """
    One-call helper:
    - simulate the FSM from the state table
    - optionally render the SVG
    - return the TimingDiagramResult
    """
    result = simulate_fsm_from_state_table(
        next_states_rows,
        outputs_by_state,
        state_names,
        input_names=input_names,
        output_names=output_names,
        cycles=cycles,
        initial_state=initial_state,
        title=title,
        rng=rng,
    )

    if out_filename:
        render_timing_diagram(result, out_filename=out_filename)

    return result


# -----------------------------------------------------------------------------
# Example usage
# -----------------------------------------------------------------------------
def _demo() -> None:
    # Example 1: Moore machine
    next_states_rows = [
        ["S0", "S1"],
        ["S1", "S0"],
    ]
    outputs_by_state = ["0", "1"]
    state_names = ["S0", "S1"]

    result = state_table_to_random_timing_diagram(
        next_states_rows,
        outputs_by_state,
        state_names,
        input_names=["A"],
        output_names=["F"],
        cycles=10,
        initial_state="S0",
        title="Demo Moore FSM Timing",
        out_filename="demo_fsm_timing.svg",
        rng=random.Random(7),
    )

    print("FSM type:", result.fsm_type)
    print("Inputs:", result.input_names)
    print("Input patterns:", result.input_patterns)
    print("Initial state:", result.initial_state)
    print("Cycle inputs:", result.cycle_inputs)
    print("Signals:")
    for name, sig in result.signals.items():
        print(f"  {name}: {sig}")
    print(make_timing_link(result))


if __name__ == "__main__":
    _demo()
