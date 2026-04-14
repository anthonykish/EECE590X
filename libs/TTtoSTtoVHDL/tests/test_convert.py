from TTtoSTtoVHDL import converter
import pytest

def test_moore_condensed_roundtrip_truth():
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
        next_state, output_by_state, state_encoding=enc, m_in=2, p_out=1
    )

    truth = converter.transitions_to_truth(transitions, k_state=2, m_in=2, p_out=1)
    transitions2 = converter.truth_to_transitions(truth, k_state=2, m_in=2, p_out=1)
    truth2 = converter.transitions_to_truth(transitions2, k_state=2, m_in=2, p_out=1)

    assert truth2 == truth

def test_reject_duplicate_state_names():
    with pytest.raises(ValueError):
        converter.build_state_encoding(["SA", "SA"], k_state=1)

def test_missing_transition_raises():
    states = ["SA", "SB", "SC", "SD"]
    enc = converter.build_state_encoding(states, k_state=2)

    next_state = {
        "SA": {"00": "SA"},  # missing 01,10,11
        "SB": {"00": "SA", "01": "SA", "10": "SC", "11": "SD"},
        "SC": {"00": "SD", "01": "SC", "10": "SC", "11": "SC"},
        "SD": {"00": "SA", "01": "SD", "10": "SA", "11": "SD"},
    }
    output_by_state = {"SA": "0", "SB": "1", "SC": "0", "SD": "0"}

    with pytest.raises(ValueError):
        converter.condensed_moore_to_transitions(
            next_state, output_by_state, state_encoding=enc, m_in=2, p_out=1
        )