import random
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from d2l.question import MCQuestion
from libs.TruthTableHTML import html_tt as tt
from libs.TTtoSTtoVHDL import converter as conv

def generate_random_truth_table(num_states=2, num_inputs=1, num_outputs=1):
    """Generate a random truth table for a state machine."""
    k_state = num_states.bit_length()  # bits needed for states
    m_in = num_inputs  # input bits
    p_out = num_outputs  # output bits
    
    # Total rows = 2^(k_state + m_in)
    total_rows = 1 << (k_state + m_in)
    
    # Generate random outputs
    output_columns = []
    for _ in range(k_state + p_out):  # next state bits + output bits
        column = ''.join(random.choice('01') for _ in range(total_rows))
        output_columns.append(column)
    
    input_labels = []
    for i in range(k_state):
        input_labels.append(f"Q{i}")
    for i in range(m_in):
        input_labels.append("A")
    
    output_labels = []
    for i in range(k_state):
        output_labels.append(f"Q{i}+")
    for i in range(p_out):
        output_labels.append("F")
    
    return output_columns, input_labels, output_labels

def create_wrong_state_table(correct_next_states, correct_outputs, state_names):
    """Create a slightly wrong state table by modifying next states or outputs."""
    import copy
    wrong_next_states = copy.deepcopy(correct_next_states)
    wrong_outputs = copy.deepcopy(correct_outputs)
    
    # Randomly choose to modify next states or outputs
    if random.choice([True, False]):
        # Modify next states
        row_idx = random.randint(0, len(wrong_next_states)-1)
        col_idx = random.randint(0, len(wrong_next_states[row_idx])-1)
        current_state = wrong_next_states[row_idx][col_idx]
        # Change to a different random state
        available_states = [s for s in state_names if s != current_state]
        wrong_next_states[row_idx][col_idx] = random.choice(available_states)
    else:
        # Modify outputs
        row_idx = random.randint(0, len(wrong_outputs)-1)
        if isinstance(wrong_outputs[row_idx], str):
            # Flip a bit in the output string
            output_str = wrong_outputs[row_idx]
            bit_idx = random.randint(0, len(output_str)-1)
            bit = output_str[bit_idx]
            wrong_outputs[row_idx] = output_str[:bit_idx] + ('1' if bit == '0' else '0') + output_str[bit_idx+1:]
    
    return wrong_next_states, wrong_outputs

def main():
    # Generate a random truth table
    output_columns, input_labels, output_labels = generate_random_truth_table()
    
    # Convert to state table
    next_states, outputs, state_names = conv.truth_columns_to_state_table(
        output_columns=output_columns,
        input_labels=input_labels,
        output_labels=output_labels
    )
    
    # Create truth table HTML
    truth_table_html = tt.html_tt(output_columns, input_labels + output_labels)
    
    # Create correct state table HTML
    correct_st_html = tt.html_st(
        next_states,
        outputs,
        input_headers=["a=0", "a=1"],
        state_names=state_names
    )
    
    # Create wrong options
    wrong_options = []
    for _ in range(3):
        wrong_next_states, wrong_outputs = create_wrong_state_table(next_states, outputs, state_names)
        wrong_st_html = tt.html_st(
            wrong_next_states,
            wrong_outputs,
            input_headers=["a=0", "a=1"],
            state_names=state_names
        )
        wrong_options.append(wrong_st_html)
    
    # Create the question
    question_text = f"Given the following truth table, select the corresponding state table:<br><br>{truth_table_html}"
    
    question = MCQuestion(
        text=question_text,
        title="Truth Table to State Table Conversion",
        points=10,
        difficulty=2
    )
    
    # Add correct answer
    question.add_answer(correct_st_html, 100)
    
    # Add wrong answers
    for wrong in wrong_options:
        question.add_answer(wrong, 0)
    
    # Print the question (for testing)
    print("Question Text:")
    print(question_text)
    print("\nCorrect Answer:")
    print(correct_st_html)
    print("\nWrong Answers:")
    for i, wrong in enumerate(wrong_options, 1):
        print(f"Wrong {i}:")
        print(wrong)

if __name__ == "__main__":
    main()
