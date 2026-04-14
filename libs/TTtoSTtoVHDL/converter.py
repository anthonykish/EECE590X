"""
convert.py

Finite State Machine conversion utilities.

This module converts between:

- condensed FSM tables
- transition rows
- truth tables

All formats are internally represented as TransitionRow objects.
"""

from dataclasses import dataclass
from typing import Dict, Iterable, List, Tuple
import math

from TTtoSTtoVHDL import bits


@dataclass(frozen=True, slots=True)
class TransitionRow:
    """
    Represents a single FSM transition.

    ps : present state bits
    x  : input bits
    ns : next state bits
    y  : output bits

    Example
    -------
    >>> TransitionRow("00","1","10","0")
    """
    ps: str
    x: str
    ns: str
    y: str

    def key(self) -> str:
        """
        Return combined key PS||X used for sorting or uniqueness.

        Example
        -------
        >>> t = TransitionRow("01","10","11","0")
        >>> t.key()
        '0110'
        """
        return bits.concat_bits(self.ps, self.x)


def min_state_bits(n_states: int) -> int:
    """
    Compute minimum bits required to encode states.

    Example
    -------
    >>> min_state_bits(4)
    2
    """
    return max(1, math.ceil(math.log2(n_states)))


def build_state_encoding(states: List[str], k_state: int | None = None) -> Dict[str, str]:
    """
    Assign binary encodings to symbolic state names.

    Parameters
    ----------
    states : list[str]
        Symbolic state labels
    k_state : int optional
        Number of bits used for state encoding

    Returns
    -------
    dict[str,str]

    Example
    -------
    >>> build_state_encoding(["SA","SB","SC","SD"],2)
    {'SA':'00','SB':'01','SC':'10','SD':'11'}
    """
    if k_state is None:
        k_state = min_state_bits(len(states))

    return {s: bits.int_to_bits(i, k_state) for i, s in enumerate(states)}


def truth_to_transitions(
    truth_rows: Iterable[Tuple[str, str]],
    k_state: int,
    m_in: int,
    p_out: int,
) -> List[TransitionRow]:
    """
    Convert a truth table into transition rows.

    Input format
    ----------
    inputs = PS||X
    outputs = NS||Y

    Example
    -------
    >>> truth = [("000","101")]
    >>> truth_to_transitions(truth,2,1,1)
    """
    transitions = []

    for ins, outs in truth_rows:
        ps, x = bits.split_bits(ins, k_state, m_in)
        ns, y = bits.split_bits(outs, k_state, p_out)
        transitions.append(TransitionRow(ps, x, ns, y))

    return transitions


def transitions_to_truth(
    transitions: Iterable[TransitionRow],
    k_state: int,
    m_in: int,
    p_out: int,
) -> List[Tuple[str, str]]:
    """
    Convert transition rows back into truth table rows.

    Example
    -------
    >>> t = TransitionRow("00","1","10","0")
    >>> transitions_to_truth([t],2,1,1)
    [('001','100')]
    """
    rows = []

    for t in transitions:
        ins = bits.concat_bits(t.ps, t.x)
        outs = bits.concat_bits(t.ns, t.y)
        rows.append((ins, outs))

    return rows


def condensed_moore_to_transitions(
    next_state: Dict[str, Dict[str, str]],
    outputs: Dict[str, str],
    encoding: Dict[str, str],
    m_in: int,
) -> List[TransitionRow]:
    """
    Convert a condensed Moore FSM table into transition rows.

    Moore machines:
    output depends only on state.

    Example
    -------
    next_state["SA"]["00"] = "SB"
    outputs["SA"] = "1"
    """
    transitions = []

    for state, mapping in next_state.items():

        ps = encoding[state]
        y = outputs[state]

        for inp, ns_state in mapping.items():
            ns = encoding[ns_state]
            transitions.append(TransitionRow(ps, inp, ns, y))

    return transitions

def truth_columns_to_state_table(
    output_columns: List[str],
    input_labels: List[str],
    output_labels: List[str],
    *,
    state_prefix: str = "S",
) -> Tuple[List[List[str]], List[str], List[str]]:
    """
    Convert truth-table output columns directly into a condensed state table.

    Supports unused present-state encodings by allowing rows containing X.
    Those encodings are skipped when reconstructing the condensed table.
    """

    if not output_columns:
        raise ValueError("output_columns cannot be empty")
    if not input_labels:
        raise ValueError("input_labels cannot be empty")
    if not output_labels:
        raise ValueError("output_labels cannot be empty")
    if len(output_columns) != len(output_labels):
        raise ValueError("Number of output columns must match number of output labels")

    row_count = len(output_columns[0])
    if row_count == 0:
        raise ValueError("Output columns cannot be empty strings")

    for col in output_columns:
        if len(col) != row_count:
            raise ValueError("All output columns must have the same length")
        if any(bit not in "01Xx" for bit in col):
            raise ValueError("Output columns must contain only 0, 1, or X")

    expected_rows = 1 << len(input_labels)
    if row_count != expected_rows:
        raise ValueError(
            f"Expected {expected_rows} rows from {len(input_labels)} input labels, got {row_count}"
        )

    state_input_indices = [i for i, lbl in enumerate(input_labels) if lbl.upper().startswith("Q")]
    external_input_indices = [i for i in range(len(input_labels)) if i not in state_input_indices]
    if not state_input_indices:
        raise ValueError("Could not detect present-state bits from input_labels")

    next_state_output_indices = [i for i, lbl in enumerate(output_labels) if "+" in lbl]
    fsm_output_indices = [i for i in range(len(output_labels)) if i not in next_state_output_indices]
    if not next_state_output_indices:
        raise ValueError("Could not detect next-state bits from output_labels")

    k_state = len(state_input_indices)
    m_in = len(external_input_indices)
    input_codes = [bits.int_to_bits(i, m_in) for i in range(1 << m_in)]

    observed_rows: Dict[str, Dict[str, Tuple[str, str]]] = {}

    for i in range(row_count):
        full_input_bits = bits.int_to_bits(i, len(input_labels))

        ps_bits = "".join(full_input_bits[idx] for idx in state_input_indices)
        x_bits = "".join(full_input_bits[idx] for idx in external_input_indices)

        full_output_bits = "".join(col[i] for col in output_columns)
        ns_bits = "".join(full_output_bits[idx] for idx in next_state_output_indices)
        y_bits = "".join(full_output_bits[idx] for idx in fsm_output_indices)

        if all(bit in "Xx" for bit in ns_bits + y_bits):
            continue

        if any(bit in "Xx" for bit in ns_bits + y_bits):
            raise ValueError(
                f"Row {i} mixes X and binary values; unsupported partial don't-care row"
            )

        observed_rows.setdefault(ps_bits, {})[x_bits] = (ns_bits, y_bits)

    used_state_codes = sorted(observed_rows.keys(), key=lambda b: int(b, 2))
    state_names = [f"{state_prefix}{i}" for i in range(len(used_state_codes))]
    code_to_name = {code: name for code, name in zip(used_state_codes, state_names)}

    next_states_rows: List[List[str]] = []
    outputs_by_state: List[str] = []

    for ps_code in used_state_codes:
        mapping = observed_rows[ps_code]
        row: List[str] = []
        per_input_outputs: List[str] = []

        for x_code in input_codes:
            if x_code not in mapping:
                raise ValueError(
                    f"Missing row for present-state code {ps_code} and input code {x_code}"
                )
            ns_bits, y_bits = mapping[x_code]
            if ns_bits not in code_to_name:
                raise ValueError(
                    f"Next-state code {ns_bits} is not one of the observed state encodings"
                )
            row.append(code_to_name[ns_bits])
            per_input_outputs.append(y_bits)

        if len(set(per_input_outputs)) == 1:
            outputs_by_state.append(per_input_outputs[0])
        else:
            outputs_by_state.append(" / ".join(per_input_outputs))

        next_states_rows.append(row)

    return next_states_rows, outputs_by_state, state_names


def state_table_to_truth_columns(
    next_states_rows: List[List[str]],
    outputs_by_state: List[str],
    state_names: List[str],
    *,
    input_labels: List[str],
    next_state_labels: List[str],
    output_labels: List[str] | None = None,
    state_prefix: str = "S",
) -> Tuple[List[str], List[str], List[str]]:
    """
    Convert a condensed state table into truth-table output columns.

    Supports non-power-of-two numbers of states by marking unused
    present-state encodings as X rows in the truth table.
    """

    if not next_states_rows:
        raise ValueError("next_states_rows cannot be empty")

    if len(next_states_rows) != len(outputs_by_state):
        raise ValueError("outputs_by_state must have one entry per state row")

    if len(next_states_rows) != len(state_names):
        raise ValueError("state_names must have one entry per state row")

    num_state_rows = len(next_states_rows)
    num_input_cols = len(next_states_rows[0])

    if num_input_cols == 0:
        raise ValueError("State table must have at least one input column")

    for row in next_states_rows:
        if len(row) != num_input_cols:
            raise ValueError("All rows in next_states_rows must have the same number of columns")

    if num_input_cols & (num_input_cols - 1):
        raise ValueError("Number of next-state columns must be a power of 2")

    m_in = num_input_cols.bit_length() - 1
    k_state = len(next_state_labels)

    min_k = min_state_bits(len(state_names))
    if k_state < min_k:
        raise ValueError(
            f"next_state_labels provide only {k_state} bits, but {len(state_names)} states need at least {min_k}"
        )

    first_output = outputs_by_state[0].strip()
    if "/" in first_output:
        first_parts = [part.strip() for part in first_output.split("/")]
        if not first_parts:
            raise ValueError("Could not parse packed Mealy output")
        p_out = len(first_parts[0])
    else:
        p_out = len(first_output.replace(" ", ""))

    if output_labels is None:
        if p_out == 1:
            output_labels = ["F"]
        else:
            output_labels = [f"F{i}" for i in range(p_out - 1, -1, -1)]

    if len(output_labels) != p_out:
        raise ValueError(
            f"output_labels has length {len(output_labels)}, but inferred output width is {p_out}"
        )

    encoding = build_state_encoding(state_names, k_state=k_state)
    code_to_name = {code: name for name, code in encoding.items()}
    input_codes = [bits.int_to_bits(i, m_in) for i in range(1 << m_in)]

    state_row_map = {state: row for state, row in zip(state_names, next_states_rows)}
    output_row_map = {state: out for state, out in zip(state_names, outputs_by_state)}

    full_input_count = 1 << (k_state + m_in)
    ns_columns = ["" for _ in range(k_state)]
    y_columns = ["" for _ in range(p_out)]

    for i in range(full_input_count):
        full_bits = bits.int_to_bits(i, k_state + m_in)
        ps_bits, x_bits = bits.split_bits(full_bits, k_state, m_in)

        if ps_bits not in code_to_name:
            for b in range(k_state):
                ns_columns[b] += "X"
            for b in range(p_out):
                y_columns[b] += "X"
            continue

        ps_name = code_to_name[ps_bits]
        x_index = bits.bits_to_int(x_bits)
        ns_name = state_row_map[ps_name][x_index]
        ns_bits = encoding[ns_name]

        out_cell = output_row_map[ps_name]
        if "/" in out_cell:
            per_input = [part.strip() for part in out_cell.split("/")]
            if len(per_input) != (1 << m_in):
                raise ValueError(
                    f"Mealy output row '{out_cell}' must contain {1 << m_in} slash-separated outputs"
                )
            y_bits = per_input[x_index]
        else:
            y_bits = out_cell.strip()

        if len(y_bits) != p_out:
            raise ValueError(f"Output '{y_bits}' has width {len(y_bits)}, expected {p_out}")

        for b, bit in enumerate(ns_bits):
            ns_columns[b] += bit
        for b, bit in enumerate(y_bits):
            y_columns[b] += bit

    output_columns = ns_columns + y_columns
    final_output_labels = next_state_labels + output_labels
    return output_columns, input_labels, final_output_labels

