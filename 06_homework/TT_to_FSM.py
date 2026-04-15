import random
import sys
import os
import json
import copy
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from d2l.question import MCQuestion
from libs.TruthTableHTML import html_tt as tt
from libs.fsm.fsm import FSM
from generate_random_fsms_guaranteed import generate_one_variant, find_template_file, explorer_url

def normalize_fsm_json_for_parser(fsm_json):
    """Normalize FSM JSON outputText so the parser can extract outputs."""
    output_names = fsm_json.get("outputs", "").split()

    # Moore outputs: node outputText should include the output name
    if output_names:
        for node in fsm_json.get("fsmNodes", []):
            text = node.get("outputText", "").strip()
            if text and all(ch in "01" for ch in text):
                node["outputText"] = " ".join(f"{name} {bit}" for name, bit in zip(output_names, text))

        # Mealy outputs: use output name in arc outputText if not already present
        for arc in fsm_json.get("fsmArcs", []) + fsm_json.get("fsmSelfArcs", []):
            if "/" in arc.get("outputText", ""):
                condition, output_part = arc["outputText"].split("/", 1)
                output_part = output_part.strip()
                if output_part and all(ch in "01" for ch in output_part.replace(" ", "")):
                    arc["outputText"] = f"{condition}/{output_names[0]} {output_part}"

    return fsm_json


def generate_random_fsm():
    """Generate a random FSM using the same approach as generate_random_fsms_guaranteed.py."""
    # Choose a random template (2, 3, or 4 states)
    template_name = random.choice(["2state", "3state", "4state"])
    template_file = find_template_file(template_name)

    with open(template_file, "r") as f:
        base_json = json.load(f)

    # Use the same generate_one_variant function
    fsm_json, metadata = generate_one_variant(base_json)
    fsm_json = normalize_fsm_json_for_parser(fsm_json)

    print(f"DEBUG: FSM type: {metadata['fsm_type']}")
    print(f"DEBUG: FSM inputs: {metadata['inputs']}")
    print(f"DEBUG: FSM outputs: {metadata['outputs']}")
    for i, node in enumerate(fsm_json["fsmNodes"]):
        print(f"DEBUG: Node {i} outputText: '{node['outputText']}'")
    for i, arc in enumerate(fsm_json.get("fsmArcs", [])[:2]):  # Just first 2 arcs
        print(f"DEBUG: Arc {i} outputText: '{arc['outputText']}'")

    # Create FSM object to get truth table
    # We need to save the JSON to a temp file first since FSM constructor expects a file
    import tempfile
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump(fsm_json, f)
        temp_file = f.name

    try:
        fsm = FSM(temp_file)
        return fsm_json, fsm
    finally:
        os.unlink(temp_file)

def create_wrong_fsm_by_arc(correct_json):
    """Create a wrong FSM by changing an arc destination."""
    wrong_json = copy.deepcopy(correct_json)
    if wrong_json.get("fsmArcs"):
        arc = random.choice(wrong_json["fsmArcs"])
        available_nodes = [i for i in range(len(wrong_json["fsmNodes"])) if i != arc["endNode"]]
        if available_nodes:
            arc["endNode"] = random.choice(available_nodes)
    return wrong_json

def create_wrong_fsm_by_output(correct_json):
    """Create a wrong FSM by flipping a node's output."""
    wrong_json = copy.deepcopy(correct_json)
    if wrong_json.get("fsmNodes"):
        node = random.choice(wrong_json["fsmNodes"])
        if "/" in node["outputText"]:
            # Mealy output
            parts = node["outputText"].split("/")
            if len(parts) > 1:
                output_part = parts[1].strip()
                if output_part:
                    bit_idx = random.randint(0, len(output_part)-1)
                    bit = output_part[bit_idx]
                    new_bit = '1' if bit == '0' else '0'
                    parts[1] = output_part[:bit_idx] + new_bit + output_part[bit_idx+1:]
                    node["outputText"] = "/".join(parts)
        else:
            # Moore output
            text = node["outputText"].strip()
            if text and text[0] in '01':
                node["outputText"] = ('1' if text[0] == '0' else '0') + text[1:]
    return wrong_json

def create_wrong_fsm_by_condition(correct_json):
    """Create a wrong FSM by changing an arc's condition."""
    wrong_json = copy.deepcopy(correct_json)
    if wrong_json.get("fsmArcs"):
        arc = random.choice(wrong_json["fsmArcs"])
        if arc["outputText"]:
            conditions = arc["outputText"].split(" | ")
            if conditions:
                condition = random.choice(conditions)
                if "x" in condition:
                    new_condition = condition.replace("x", "x'").replace("x''", "x")
                    arc["outputText"] = arc["outputText"].replace(condition, new_condition)
    return wrong_json

def main():
    # Generate a correct FSM
    correct_json, fsm = generate_random_fsm()

    # Get the truth table from the FSM
    truth_table_html = fsm.make_html_truth_table()

    # Create the correct FSM URL
    correct_url = explorer_url(correct_json)

    # Create wrong FSM options
    wrong_urls = [
        explorer_url(create_wrong_fsm_by_arc(correct_json)),
        explorer_url(create_wrong_fsm_by_output(correct_json)),
        explorer_url(create_wrong_fsm_by_condition(correct_json)),
    ]

    # Create the question
    question_text = f"Given the following truth table, select the corresponding finite state machine diagram:<br><br>{truth_table_html}"

    question = MCQuestion(
        text=question_text,
        title="Truth Table to FSM Conversion",
        points=10,
        difficulty=3
    )

    # Add correct answer
    question.add_answer(f'<a href="{correct_url}" target="_blank">View FSM Diagram</a>', 100)

    # Add wrong answers
    for wrong_url in wrong_urls:
        question.add_answer(f'<a href="{wrong_url}" target="_blank">View FSM Diagram</a>', 0)

    # Print the question (for testing)
    print("Question Text:")
    print(question_text)
    print("\nCorrect Answer URL:")
    print(correct_url)
    print("\nWrong Answer URLs:")
    for i, wrong_url in enumerate(wrong_urls, 1):
        print(f"Wrong {i}: <a href=\"{wrong_url}\" target=\"_blank\">View FSM Diagram</a>")

if __name__ == "__main__":
    main()
