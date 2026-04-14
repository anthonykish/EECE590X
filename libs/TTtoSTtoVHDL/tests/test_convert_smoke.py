# test_convert_smoke.py
from TTtoSTtoVHDL import converter

def main():
    # --- Example from HW6 (Moore, states SA..SD, input ab (2 bits), output F (1 bit)) ---
    states = ["SA", "SB", "SC", "SD"]
    enc = converter.build_state_encoding(states, k_state=2)

    next_state = {
        "SA": {"00": "SA", "01": "SB", "10": "SC", "11": "SD"},
        "SB": {"00": "SA", "01": "SA", "10": "SC", "11": "SD"},
        "SC": {"00": "SD", "01": "SC", "10": "SC", "11": "SC"},
        "SD": {"00": "SA", "01": "SD", "10": "SA", "11": "SD"},
    }
    output_by_state = {"SA": "0", "SB": "1", "SC": "0", "SD": "0"}

    transitions = converter.condensed_moore_to_transitions(
        next_state,
        output_by_state,
        enc,
        m_in=2,
    )

    truth_rows = converter.transitions_to_truth(transitions, k_state=2, m_in=2, p_out=1)

    # Print a few rows to eyeball it
    print("Encoding:", enc)
    print("\nFirst 8 truth rows (PS||ab -> NS||F):")
    for r in truth_rows[:8]:
        print(f"{r[0]} -> {r[1]}")

    # --- Round-trip test: TT -> transitions -> TT should match ---
    transitions2 = converter.truth_to_transitions(truth_rows, k_state=2, m_in=2, p_out=1)
    truth_rows2 = converter.transitions_to_truth(transitions2, k_state=2, m_in=2, p_out=1)

    assert truth_rows2 == truth_rows, "Round-trip failed: TT -> ST -> TT mismatch"
    print("\nRound-trip OK")

if __name__ == "__main__":
    main()