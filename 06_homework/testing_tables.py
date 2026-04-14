from TruthTableHTML import html_tt as tt
from TTtoSTtoVHDL import converter as conv

# possibly add encoding states for state table to TT conversion

def main():
    output = tt.html_tt(["11011101", "01010101", "01010101"], ["Q1", "Q0", "A", "Q1+", "Q0+", "F"])
    print(f"Truth table: \n {output}")

    next_states, outputs, state_names = conv.truth_columns_to_state_table(
        ["11011101", "01010101", "01010101"],
        ["Q1", "Q0", "A"],
        ["Q1+", "Q0+", "F"]
    )

    print("next_states =", next_states)
    print("outputs =", outputs)
    print("state_names =", state_names)


    html = tt.html_st(
        next_states,
        outputs,
        input_headers=["a=0", "a=1"],
        state_names=["S0", "S1", "S2", "S3"]
    )

    print(f"State table: \n {html}")

    output_columns, input_labels, output_labels = conv.state_table_to_truth_columns(
    next_states_rows=next_states,
    outputs_by_state=outputs,
    state_names=state_names,
    input_labels=["Q1", "Q0", "A"],
    next_state_labels=["Q1+", "Q0+"],
)

    print("output_columns =", output_columns)
    print("input_labels   =", input_labels)
    print("output_labels  =", output_labels)
    combined_labels = input_labels + output_labels
    print("Combined lables = ", input_labels + output_labels)

    newOutput = tt.html_tt(output_columns, combined_labels)
    print (f"Reconstructed truth table: \n {newOutput}")


if __name__ == "__main__":
    main()