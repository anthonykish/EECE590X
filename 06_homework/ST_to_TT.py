import random
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from d2l.question import MCQuestion
from libs.TruthTableHTML import html_tt as tt
from libs.TTtoSTtoVHDL import converter as conv

def generate_random_state_table(num_states=4, num_inputs=1, num_outputs=1):
    """Generate a random state table."""
    state_names = [f"S{i}" for i in range(num_states)]
    next_states = []
    outputs = []
    
    for _ in range(num_states):
        row = []
        for _ in range(2**num_inputs):  # 2 inputs for 1-bit input
            next_state = random.choice(state_names)
            row.append(next_state)
        next_states.append(row)
        
        output = ''.join(random.choice('01') for _ in range(num_outputs))
        outputs.append(output)
    
    return next_states, outputs, state_names

def create_wrong_truth_table(correct_columns, input_labels, output_labels):
    """Create a slightly wrong truth table by flipping some bits."""
    import copy
    wrong_columns = copy.deepcopy(correct_columns)
    # Flip a random bit in a random column
    col_idx = random.randint(0, len(wrong_columns)-1)
    row_idx = random.randint(0, len(wrong_columns[col_idx])-1)
    bit = wrong_columns[col_idx][row_idx]
    wrong_columns[col_idx] = wrong_columns[col_idx][:row_idx] + ('1' if bit == '0' else '0') + wrong_columns[col_idx][row_idx+1:]
    return wrong_columns

def main():
    # Generate a random state table
    next_states, outputs, state_names = generate_random_state_table()
    
    # Convert to truth table
    output_columns, input_labels, output_labels = conv.state_table_to_truth_columns(
        next_states_rows=next_states,
        outputs_by_state=outputs,
        state_names=state_names,
        input_labels=["Q1", "Q0", "A"],
        next_state_labels=["Q1+", "Q0+"],
        output_labels=["F"]
    )
    
    # Create state table HTML
    state_table_html = tt.html_st(
        next_states,
        outputs,
        input_headers=["a=0", "a=1"],
        state_names=state_names
    )
    
    # Create correct truth table HTML
    correct_tt_html = tt.html_tt(output_columns, input_labels + output_labels)
    
    # Create wrong options
    wrong_options = []
    for _ in range(3):
        wrong_columns = create_wrong_truth_table(output_columns, input_labels, output_labels)
        wrong_tt_html = tt.html_tt(wrong_columns, input_labels + output_labels)
        wrong_options.append(wrong_tt_html)
    
    # Create the question
    question_text = f"Given the following state table, select the corresponding truth table:<br><br>{state_table_html}"
    
    question = MCQuestion(
        text=question_text,
        title="State Table to Truth Table Conversion",
        points=10,
        difficulty=2
    )
    
    # Add correct answer
    question.add_answer(correct_tt_html, 100)
    
    # Add wrong answers
    for wrong in wrong_options:
        question.add_answer(wrong, 0)
    
    # Print the question (for testing)
    print("Question Text:")
    print(question_text)
    print("\nCorrect Answer:")
    print(correct_tt_html)
    print("\nWrong Answers:")
    for i, wrong in enumerate(wrong_options, 1):
        print(f"Wrong {i}:")
        print(wrong)

if __name__ == "__main__":
    main()
