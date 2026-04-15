# test_state_table_timing.py

from matplotlib.table import table
from numpy import rint

from fsm.state_table_timing_tools import (
    generate_random_state_table,
    state_table_to_timing_diagram,
    random_timing_diagram_to_state_table,
    state_table_html
)

from wave_utils.wave_utils import (
    make_wavedrom_link,
    make_wavedrom_image,
    make_wavedrom_link_rows,
    make_wavedrom_image_rows,
    to_dotless,
    to_dotted,
    make_clock,
)
from TruthTableHTML.html_tt import html_st


def print_state_table(table, title):
    print("\n" + "="*50)
    print(title)
    print("="*50)

    next_states, outputs, state_names, machine_type = table

    print("States:", state_names)
    print("\nNext State Table:")
    for row in next_states:
        print(row)

    print("\nOutputs:")
    for row in outputs:
        print(row)


def test_state_table_to_timing():
    print("\n\n===== TEST: State Table -> Timing Diagram =====")

    table = generate_random_state_table(
        n_states=3,
        m_in=2,
        p_out=1,
        machine_type="mealy"
    )

    next_states_rows, outputs_by_state, state_names, machine_type = table

    print("Machine type:", machine_type)
    print_state_table((next_states_rows, outputs_by_state, state_names, machine_type), "Generated State Table")

    result = state_table_to_timing_diagram(
        next_states_rows,
        outputs_by_state,
        state_names,
        cycles=12,
        initial_state=state_names[0]
    )

    print("\nWaveDrom Link:")
    print(result.wavedrom_link)


def test_timing_to_state_table():
    print("\n\n===== TEST: Timing Diagram -> State Table =====")

    diag, recovered = random_timing_diagram_to_state_table(
        n_states=3,
        m_in=2,
        p_out=1,
        cycles=25
    )

    table = (
        recovered.next_states_rows,
        recovered.outputs_by_state,
        recovered.state_names,
        recovered.machine_type,
    )

    print_state_table(table, "Recovered State Table")

    print(f"\nRecovered machine type: {recovered.machine_type}")
    print(f"Coverage: {recovered.observed_pairs}/{recovered.expected_pairs}")
    print(f"Complete: {recovered.complete}")

    print("\nWaveDrom Link:")
    print(diag.wavedrom_link)


def main():
    test_state_table_to_timing()
    test_timing_to_state_table()


if __name__ == "__main__":
    main()