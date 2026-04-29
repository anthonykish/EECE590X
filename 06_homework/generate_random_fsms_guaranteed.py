import copy
import json
import random
import sys
from itertools import product
from pathlib import Path
from urllib.parse import quote

LIBS_DIR = Path(__file__).resolve().parents[1] / "libs"
if str(LIBS_DIR) not in sys.path:
    sys.path.append(str(LIBS_DIR))

from logic_utils.logic_utils import logic_eval, optimized_sop

# ---------------- Config ----------------
NUM_VARIANTS = 5
TEMPLATE_NAME = "4state"          # "2state", "3state", or "4state"
ALLOW_ONE_OR_TWO_INPUTS = True     # if False, always uses one input
OUTPUT_NAMES = ["z"]              # one output bit for now
SAVE_DIRNAME = "temp_pools"
MAX_ATTEMPTS = 100


# ---------------- Template loading ----------------

def find_template_file(template_name: str) -> Path:
    here = Path(__file__).resolve()
    repo_root = here.parents[1] if len(here.parents) > 1 else here.parent

    candidates = [
        repo_root / "libs" / "fsm" / "templates" / f"fsm_{template_name}.json",
        repo_root / "libs" / "fsm" / "templates" / f"fsm_{template_name}.txt",
        repo_root / "libs" / "fsm" / "templates" / f"{template_name}.json",
        repo_root / "libs" / "fsm" / "templates" / f"{template_name}.txt",
        Path(f"fsm_{template_name}.json"),
        Path(f"fsm_{template_name}.txt"),
        Path(f"{template_name}.json"),
        Path(f"{template_name}.txt"),
    ]

    for candidate in candidates:
        if candidate.exists():
            return candidate

    raise FileNotFoundError(f"Could not find template file for '{template_name}'")


# ---------------- Small helpers ----------------

def explorer_url(fsm_json: dict) -> str:
    compact = json.dumps(fsm_json, separators=(",", ":"))
    return "https://dougsummerville.github.io/FSM-Explorer/fsmexplorer.html?" + quote(compact, safe="")


def state_to_index_map(fsm_json: dict) -> dict[str, int]:
    return {node["stateName"]: i for i, node in enumerate(fsm_json["fsmNodes"])}


def index_to_state_map(fsm_json: dict) -> dict[int, str]:
    return {i: node["stateName"] for i, node in enumerate(fsm_json["fsmNodes"])}


def choose_input_names() -> list[str]:
    if ALLOW_ONE_OR_TWO_INPUTS and random.random() < 0.5:
        return ["x", "y"]
    return ["x"]


def make_input_patterns(input_names: list[str]) -> list[str]:
    patterns = []
    for bits in product([0, 1], repeat=len(input_names)):
        parts = []
        for name, bit in zip(input_names, bits):
            parts.append(name if bit == 1 else f"{name}'")
        patterns.append(" ".join(parts))
    return patterns


def input_combos(input_names: list[str]) -> list[str]:
    return ["".join(str(bit) for bit in bits) for bits in product([0, 1], repeat=len(input_names))]


def reduce_patterns(input_names: list[str], assigned_patterns: list[str], all_patterns: list[str]) -> str:
    """
    Reduce a list of minterm-style input patterns into optimized SOP form.

    The expression "1" means the condition is always true.
    """
    if not assigned_patterns:
        return ""

    ones = set(assigned_patterns)
    column = "".join("1" if pattern in ones else "0" for pattern in all_patterns)
    return optimized_sop(input_names, column) or "1"


def random_output_bits(width: int) -> str:
    return "".join(random.choice("01") for _ in range(width))


def normalize_term(term: str) -> tuple[str, str | None]:
    term = term.strip()
    if "/" in term:
        cond, out = term.split("/", 1)
        return cond.strip(), out.strip()
    return term, None


# ---------------- Arc access ----------------

def get_outgoing_arcs(base_json: dict, state_name: str) -> list[dict]:
    idx_by_name = state_to_index_map(base_json)
    src_idx = idx_by_name[state_name]
    result = []

    for arc in base_json.get("fsmArcs", []):
        if arc["startNode"] == src_idx:
            result.append({
                "kind": "normal",
                "src": state_name,
                "dst": base_json["fsmNodes"][arc["endNode"]]["stateName"],
                "template_arc": arc,
            })

    for arc in base_json.get("fsmSelfArcs", []):
        if arc["node"] == src_idx:
            result.append({
                "kind": "self",
                "src": state_name,
                "dst": state_name,
                "template_arc": arc,
            })

    return result


# ---------------- Guaranteed-valid behavior generation ----------------

def choose_surjective_pattern_assignment(destinations: list[str], patterns: list[str]) -> dict[str, list[str]]:
    """
    Assign every input pattern to exactly one destination.
    Every chosen destination gets at least one pattern.
    This guarantees complete coverage with no duplicates.
    """
    if not destinations:
        raise ValueError("No available destinations for assignment")

    max_used = min(len(destinations), len(patterns))
    used_count = random.randint(1, max_used)
    used_destinations = random.sample(destinations, used_count)

    grouped: dict[str, list[str]] = {dst: [] for dst in used_destinations}
    shuffled_patterns = patterns[:]
    random.shuffle(shuffled_patterns)

    # First pass: guarantee each chosen destination gets at least one pattern.
    for dst, pattern in zip(used_destinations, shuffled_patterns):
        grouped[dst].append(pattern)

    # Remaining patterns go to a random already-chosen destination.
    for pattern in shuffled_patterns[used_count:]:
        grouped[random.choice(used_destinations)].append(pattern)

    # Keep labels stable-looking.
    for dst in grouped:
        grouped[dst].sort(key=patterns.index)

    return grouped


def generate_state_plan(base_json: dict, state_name: str, patterns: list[str], fsm_type: str, output_width: int) -> list[dict]:
    outgoing = get_outgoing_arcs(base_json, state_name)
    destinations = [arc["dst"] for arc in outgoing]

    grouped = choose_surjective_pattern_assignment(destinations, patterns)
    outgoing_by_dest = {arc["dst"]: arc for arc in outgoing}

    planned_arcs = []
    for dst, assigned_patterns in grouped.items():
        arc_info = outgoing_by_dest[dst]
        if fsm_type == "moore":
            terms = [reduce_patterns(base_json["inputs"].split(), assigned_patterns, patterns)]
        else:
            by_output: dict[str, list[str]] = {}
            for pattern in assigned_patterns:
                by_output.setdefault(random_output_bits(output_width), []).append(pattern)

            terms = [
                f"{reduce_patterns(base_json['inputs'].split(), terms_for_output, patterns)}/{output_bits}"
                for output_bits, terms_for_output in sorted(by_output.items())
            ]

        planned_arcs.append({
            "kind": arc_info["kind"],
            "dst": dst,
            "label": " | ".join(terms),
            "template_arc": arc_info["template_arc"],
        })

    return planned_arcs


def build_fsm_from_template(base_json: dict, fsm_type: str, input_names: list[str], output_names: list[str]) -> dict:
    patterns = make_input_patterns(input_names)
    output_width = len(output_names)
    state_names = [node["stateName"] for node in base_json["fsmNodes"]]

    fsm_json = copy.deepcopy(base_json)
    fsm_json["inputs"] = " ".join(input_names)
    fsm_json["outputs"] = " ".join(output_names)

    kept_normal = []
    kept_self = []

    # Build the outgoing transition set for each state from scratch.
    for state_name in state_names:
        plan = generate_state_plan(fsm_json, state_name, patterns, fsm_type, output_width)

        for item in plan:
            arc = copy.deepcopy(item["template_arc"])
            arc["outputText"] = item["label"]
            if item["kind"] == "self":
                kept_self.append(arc)
            else:
                kept_normal.append(arc)

    fsm_json["fsmArcs"] = kept_normal
    fsm_json["fsmSelfArcs"] = kept_self

    # Reset arc: keep exactly one and point it somewhere valid.
    if fsm_json.get("fsmResetArcs"):
        idx_by_name = state_to_index_map(fsm_json)
        reset_arc = copy.deepcopy(fsm_json["fsmResetArcs"][0])
        reset_target = random.choice(state_names)
        reset_arc["node"] = idx_by_name[reset_target]
        reset_arc["outputText"] = "reset"
        fsm_json["fsmResetArcs"] = [reset_arc]

    # Node outputs.
    if fsm_type == "moore":
        for node in fsm_json["fsmNodes"]:
            node["outputText"] = random_output_bits(output_width)
    else:
        for node in fsm_json["fsmNodes"]:
            node["outputText"] = ""

    return fsm_json


# ---------------- Validation ----------------

def validate_generated_fsm(fsm_json: dict, fsm_type: str, input_names: list[str], output_names: list[str]) -> tuple[bool, str]:
    output_width = len(output_names)
    state_names = [node["stateName"] for node in fsm_json["fsmNodes"]]
    idx_to_name = index_to_state_map(fsm_json)
    combos = input_combos(input_names)

    outgoing_by_state: dict[str, list[str]] = {state: [] for state in state_names}

    for arc in fsm_json.get("fsmArcs", []):
        outgoing_by_state[idx_to_name[arc["startNode"]]].append(arc.get("outputText", "").strip())
    for arc in fsm_json.get("fsmSelfArcs", []):
        outgoing_by_state[idx_to_name[arc["node"]]].append(arc.get("outputText", "").strip())

    for state in state_names:
        labels = outgoing_by_state[state]
        if not labels:
            return False, f"State {state} has no outgoing arcs"

        match_count_by_combo = {combo: 0 for combo in combos}
        for label in labels:
            if not label:
                return False, f"State {state} has a blank outgoing label"

            for raw_term in label.split("|"):
                cond, out = normalize_term(raw_term)

                for combo in combos:
                    try:
                        match_count_by_combo[combo] += logic_eval(input_names, combo, cond)
                    except Exception:
                        return False, f"State {state} has invalid condition '{cond}'"

                if fsm_type == "mealy":
                    if out is None:
                        return False, f"Mealy term '{raw_term.strip()}' is missing an output"
                    if len(out) != output_width or any(bit not in "01" for bit in out):
                        return False, f"Mealy term '{raw_term.strip()}' has invalid output bits"
                else:
                    if out is not None:
                        return False, f"Moore term '{raw_term.strip()}' should not contain a transition output"

        for combo, match_count in match_count_by_combo.items():
            if match_count == 0:
                return False, f"State {state} has no next state for input {combo}"
            if match_count > 1:
                return False, f"State {state} has multiple next states for input {combo}"

    for node in fsm_json["fsmNodes"]:
        node_out = node.get("outputText", "").strip()
        if fsm_type == "moore":
            if len(node_out) != output_width or any(bit not in "01" for bit in node_out):
                return False, f"Moore state {node['stateName']} has invalid output '{node_out}'"
        else:
            if node_out != "":
                return False, f"Mealy state {node['stateName']} should not have a state output"

    for reset_arc in fsm_json.get("fsmResetArcs", []):
        if reset_arc.get("outputText", "").strip().lower() != "reset":
            return False, "Reset arc must be labeled 'reset'"

    return True, "OK"

def is_fully_connected_fsm(fsm_json):
    """
    Return True if the FSM is strongly connected:
    from every state, every other state is reachable.

    Reset arcs are ignored.
    """
    nodes = fsm_json.get("fsmNodes", [])
    arcs = fsm_json.get("fsmArcs", [])
    self_arcs = fsm_json.get("fsmSelfArcs", [])

    num_states = len(nodes)
    if num_states == 0:
        return False

    # Build adjacency list by node index
    adjacency = {i: set() for i in range(num_states)}

    for arc in arcs:
        start = arc["startNode"]
        end = arc["endNode"]
        adjacency[start].add(end)

    for arc in self_arcs:
        node = arc["node"]
        adjacency[node].add(node)

    def dfs(start):
        visited = set()
        stack = [start]

        while stack:
            current = stack.pop()
            if current in visited:
                continue
            visited.add(current)
            stack.extend(adjacency[current] - visited)

        return visited

    # Strong connectivity:
    # every state must reach all states
    for state in range(num_states):
        reachable = dfs(state)
        if len(reachable) != num_states:
            return False

    return True


# ---------------- One variant + main ----------------

def generate_one_variant(base_json):
    for _ in range(100):
        input_names = choose_input_names()
        fsm_type = random.choice(["moore", "mealy"])
        output_names = ["z"]

        fsm_json = build_fsm_from_template(base_json, fsm_type, input_names, output_names)
        is_valid, _message = validate_generated_fsm(fsm_json, fsm_type, input_names, output_names)

        if is_valid and is_fully_connected_fsm(fsm_json):
            return fsm_json, {
                "fsm_type": fsm_type,
                "inputs": input_names,
                "input_patterns": make_input_patterns(input_names),
                "outputs": output_names,
            }

    raise ValueError("Could not generate a fully connected FSM after many attempts")


def main() -> None:
    template_file = find_template_file(TEMPLATE_NAME)
    base_json = json.loads(template_file.read_text())

    save_dir = Path(__file__).resolve().parents[1] / SAVE_DIRNAME
    save_dir.mkdir(parents=True, exist_ok=True)

    made = 0
    attempts = 0

    while made < NUM_VARIANTS and attempts < MAX_ATTEMPTS:
        attempts += 1
        print(f"\n--- Generating FSM Variant {made + 1} ---")

        try:
            fsm_json, meta = generate_one_variant(base_json)
        except Exception as e:
            print(f"Retrying: {e}")
            continue

        out_file = save_dir / f"{TEMPLATE_NAME}_{meta['fsm_type']}_variant_{made + 1}.json"
        out_file.write_text(json.dumps(fsm_json, indent=2))

        print(f"Type: {meta['fsm_type'].upper()}")
        print(f"Inputs: {' '.join(meta['inputs'])}")
        print(f"Input patterns: {', '.join(meta['input_patterns'])}")
        print(f"Outputs: {' '.join(meta['outputs'])}")
        print(f"Saved: {out_file}")
        print("FSM Explorer URL:")
        print(explorer_url(fsm_json))

        made += 1

    if made < NUM_VARIANTS:
        print(f"\nOnly generated {made} valid FSMs after {attempts} attempts.")


if __name__ == "__main__":
    main()
