from logic_utils.logic_utils import logic_eval, optimized_sop
from TruthTableHTML.html_tt import html_tt
import json
import re
import os
import math
from urllib.parse import quote
from pathlib import Path
import copy
from itertools import product
import random




TEMPLATE_DIR = Path(__file__).resolve().parent / "templates"

TEMPLATES = {
    "2state": TEMPLATE_DIR / "fsm_2state.json",
    "3state": TEMPLATE_DIR / "fsm_3state.json",
    "4state": TEMPLATE_DIR / "fsm_4state.json",
}


class FSM():

    def __init__(self, filename, state_notation = "Q"):

        """
        Loads an FSM Explorer file and gets the appropriate data

        filename: txt file saved from FSM Explorer
        state_notation: What to name the bits of the state, default "Q1", "Q0" etc.
        """

        self.state_notation = state_notation

        # Get filename without extension
        self.name = os.path.splitext(os.path.basename(filename))[0]

        with open(filename, "r") as f:
            self.fsm_json = json.load(f)

        self._rebuild(self.state_notation)

    def get_inputs_from_json(self):
        
        """
        Sets up a list of input names
        and another list of all possible input combinations
        """

        # First check for inputs explicitly specified in FSMExplorer
        if "inputs" in self.fsm_json and self.fsm_json["inputs"]:
            text = self.fsm_json["inputs"]
            text = text.replace(",", " ")
            spec_inputs = text.split(" ")
            # Get rid of empty
            inputs = [i for i in spec_inputs if i]

        # Otherwise extract them from the arcs
        else:
            inputs = []
            # Parse groups of letters from the arcs
            for arc in self.fsm_json["fsmArcs"] + self.fsm_json["fsmSelfArcs"]:

                # Get stuff from left of /
                text = arc["outputText"].split("/")[0]

                # Get rid of special characters (except _ and -)
                text = re.sub("[^0-9a-zA-Z_-]+", " " , text)
                arc_inputs = text.split(" ")

                # Add non-empty, non-duplicate strings
                inputs += [i for i in arc_inputs if i and i not in inputs]

            # Remove strings made up of other strings, like "ab"
            for i in inputs:
                for j in inputs:
                    if i + j in inputs:
                        inputs.remove(i + j)
        
        self.input_names = inputs
        self.num_inputs = len(self.input_names)

        # Make all binary strings from 0 to 2^num_inputs
        self.input_combos = [f"{i:0{self.num_inputs}b}" for i in range(2 ** self.num_inputs)] \
                            if self.num_inputs > 0 else [""]
        # That last part was so that evaluate_all_combos still loops through
        # every state once when there are no inputs


    def get_outputs_from_json(self):
    
        """
        Sets up lists of Moore and Mealy output names
        """
    
        # Parse Moore outputs from states
        outputs = []
        for node in self.fsm_json["fsmNodes"]:
            
            text = node["outputText"]

            # Get rid of special characters (except _ and -)
            text = re.sub("[^0-9a-zA-Z_]+", " " , text)
            output_words = text.split(" ")
            # makes output_words something like ["F", "0", "G", "1"]

            # Add non-empty, non-duplicate strings that don't start with a number
            outputs += [o for o in output_words if o and o not in outputs 
                        and not o[0].isdigit()]
            
        self.moore_names = outputs

        # Parse Mealy outputs from arcs
        outputs = []
        for arc in self.fsm_json["fsmArcs"] + self.fsm_json["fsmSelfArcs"]:
            # Get the text after the /
            text = arc["outputText"].split("/")[1] if "/" in arc["outputText"] else ""

            # Get rid of special characters (except _ and -)
            text = re.sub("[^0-9a-zA-Z_]+", " " , text)
            output_words = text.split(" ")
            # makes outputs something like ["F", "0", "G", "1"]

            # Add non-empty, non-duplicate strings that don't start with a number
            outputs += [o for o in output_words if o and o not in outputs 
                        and not o[0].isdigit()]
        
        self.mealy_names = outputs

        self.output_names = self.moore_names+ self.mealy_names

    def get_states_from_json(self, state_notation):

        """
        Sets up a list of state names
        and another list of all possible combos of state bits
        and some more for state bit names

        So for a 3 state FSM:
        state_names = ["00", "01", "10"]
        state_bit_combos = ["00", "01", "10", "11"]
        state_bit_names = ["Q1", "Q0"]
        next_state_bit_names = ["Q1+", "Q0+"]
        (this will be needed for the truth table)
        """

        self.state_names = []
        for node in self.fsm_json["fsmNodes"]:
            self.state_names.append(node["stateName"])
        self.state_names = sorted(self.state_names)

        self.num_state_bits = max(1, math.ceil(math.log2(len(self.state_names))))
        # Get all binary strings from 0 to 2^num_state_bits
        self.state_bit_combos = ([f"{i:0{self.num_state_bits}b}" 
                                  for i in range(2 ** self.num_state_bits)])
        
        # Make state bit names like Q1, Q0, Q1+, Q0+
        self.state_bit_names = [state_notation + str(i) for i in range(self.num_state_bits)]
        self.state_bit_names.reverse()
        self.next_state_bit_names = [i + "+" for i in self.state_bit_names]
        
        # Figure out if there is a reset_state
        if self.fsm_json["fsmResetArcs"]:
            # Need to index into the list of states
            arc = self.fsm_json["fsmResetArcs"][0]
            self.has_reset = True
            self.reset_state = self.fsm_json["fsmNodes"][arc["node"]]["stateName"]
            self.reset_input_name = arc["outputText"]
        else:
            self.has_reset = False

    def get_state_data_from_json(self):

        """
        Sets up a list of dictionaries for each state with its arcs and outputs
        """

        # Not sure where else to put these tbh
        self.all_output_names = self.next_state_bit_names + self.output_names
        self.all_input_names = self.state_bit_names + self.input_names

        self.state_data = []

        for state in self.state_names:
            
            # Figure out what outputs the state has
            outputs = {}
            # Find the output text corresponding to the current state
            for node in self.fsm_json["fsmNodes"]:
                if node["stateName"] == state:
                    text = node["outputText"]

            # Get rid of special characters except _ and -
            text = re.sub("[^0-9a-zA-Z_-]+", " " , text)
            output_words = text.split(" ")
            # This brings up a list like ["F", "1", "G", "0"]
            
            for output in self.moore_names:
                # If an output exists under the state name
                if output in output_words:
                    # Copy its value to the output dictionary
                    output_value = output_words[output_words.index(output) + 1]
                    outputs[output] = str(output_value)
                # Otherwise assume it's 0
                else:
                    outputs[output] = "0"
            
            # Get expressions, next_states, and Mealy outputs from each arc
            arcs = []
            # Since arcs anchor to node ID and not state name, we have to use 
            # the arc's start node ID to index into the list of states
            # They are also stored in two separate lists: fsmArcs and fsmSelfArcs
            for arc in self.fsm_json["fsmArcs"] + self.fsm_json["fsmSelfArcs"]:
                
                # Index into the list of nodes based on if it's a self arc
                if arc in self.fsm_json["fsmArcs"]:
                    state_arc_leaves = self.fsm_json["fsmNodes"][arc["startNode"]]["stateName"]
                    state_arc_goes_to = self.fsm_json["fsmNodes"][arc["endNode"]]["stateName"]
                elif arc in self.fsm_json["fsmSelfArcs"]:
                    state_arc_leaves = self.fsm_json["fsmNodes"][arc["node"]]["stateName"]
                    state_arc_goes_to = state_arc_leaves

                # Get the expression
                exp_text = arc["outputText"].split("/")[0]

                # Get the output values
                arc_outputs = {}
                out_text = arc["outputText"].split("/")[1] if "/" in arc["outputText"] else ""

                # Get rid of special characters except _ and -
                out_text = re.sub("[^0-9a-zA-Z_-]+", " " , out_text)
                output_words = out_text.split(" ")
                # This brings up a list like ["F", "1", "G", "0"]

                for output in self.mealy_names:
                    # If an output exists under the state name
                    if output in output_words:
                        # Copy its value to the output dictionary
                        output_value = output_words[output_words.index(output) + 1]
                        arc_outputs[output] = str(output_value)
                    # Otherwise assume it's 0
                    else:
                        arc_outputs[output] = "0"

                # If on the state we're dealing with, set up and add arc dictionary
                if state_arc_leaves == state:
                    arc_dict = {"expression": exp_text,
                                "next_state": state_arc_goes_to,
                                "outputs": arc_outputs}
                    arcs.append(arc_dict)

                    
            state_dict = {"state": state, "outputs": outputs, "arcs": arcs}
            self.state_data.append(state_dict)

    def get_state(self, state_name):

        """
        Returns a state dictionary from state_data that matches
        the state name argument

        Returns None if no match found
        """

        state = [d for d in self.state_data if d["state"] == state_name]

        return state[0] if state else None

    def evaluate_all_combos(self):

        """
        Evaluates all combinations of state and input to find out
        what the next state and output should be

        Sets up a list of dictionaries of each combo, its next state(s), 
        and its output
        """

        rows = []
        # Iterate over all possible combos of state and input
        for state_combo in self.state_bit_combos:
            for input_combo in self.input_combos:

                row = {}

                # Current state
                row["state"] = state_combo

                # map bits of the input combo to inputs of the FSM
                for input_name, bit in zip(self.input_names, input_combo):
                    row[input_name] = bit

                # Find the next state
                row["next_states"] = []
                state_dict = self.get_state(state_combo)

                # If the state exists,
                # go through all arcs to find the next state
                if state_dict:
                    arcs = state_dict["arcs"]
                    for arc in arcs:
                        expression = arc["expression"]
                        # If the expression on the arc evaluates to true
                        # under the current input combo (or is empty),
                        # copy the arc's next state and Mealy outputs
                        # into the list
                        if logic_eval(self.input_names, input_combo, expression):
                            row["next_states"].append(arc["next_state"])
                            for output in self.mealy_names:
                                # 8 levels of indentation
                                # I am the best programmer to walk this earth
                                # Doug wishes he were me
                                row[output] = arc["outputs"][output]

                    # If the state exists, also process it to get Moore output
                    for output in self.moore_names:
                        row[output] = state_dict["outputs"][output]

                # If the state combo is unused, we don't care
                # about next state or output
                else:
                    row["next_states"].append("x" * len(state_combo))
                    for output in self.output_names:
                        row[output] = "x"

                rows.append(row)

        self.rows = rows

    def is_properly_specified(self):
        
        """
        Checks to make sure all state and input combos produce exactly
        one next state
        """

        for row in self.rows:
            if len(row["next_states"]) != 1:
                return False
            
        return True
    
    def verify(self):

        """
        Checks for proper specification and throws an error if improper
        """

        if not self.is_properly_specified():

            # Make error text
            multiple = [str(row) for row in self.rows if len(row["next_states"]) > 1]
            none = [str(row) for row in self.rows if len(row["next_states"]) == 0]
            multiple = "\n".join(multiple)
            none = "\n".join(none)

            error_text = "FSM is not properly specified!"
            if multiple:
                error_text += "\nThe following rows have multiple next states:\n" + multiple
            if none: 
                error_text += "\nThe following rows have no next state:\n" + multiple

            raise ValueError("FSM is not properly specified!\n" \
                            f"Multiple next states:\n{multiple}" \
                            f"No next states:\n{none}")
    
    def make_output_columns(self):
        
        """
        Sets up a list of output columns
        Each column is a string, separated by output
        """

        # Initialize dictionary of empty columns
        output_columns = {}
        for name in self.all_output_names:
            output_columns[name] = ""

        # Go through every row
        for row in self.rows:

            # Start with next state
            # Check for improperly specified states
            if len(row["next_states"]) == 0:
                raise ValueError(f"No state specified for the following row: {row}")
            elif len(row["next_states"]) > 1:
                raise ValueError(f"Multiple states specified for the following row: {row}")
            
            # Add the next state to the column
            next_state = row["next_states"][0]
            for i, next_state_bit in zip(range(self.num_state_bits), self.next_state_bit_names):
                output_columns[next_state_bit] += next_state[i]

            # Then do outputs
            for output in self.output_names:
                output_columns[output] += row[output]
    
        self.output_columns = output_columns
        return output_columns

    def make_html_truth_table(self):
        
        """
        Returns HTML truth table of FSM next state and outputs
        """
                
        if not hasattr(self, "output_columns"):
            self.make_output_columns()
        
        columns = [self.output_columns[output_name] for output_name in self.all_output_names]
        headers = self.all_input_names + self.all_output_names

        return html_tt(columns, headers)
    

    def find_output_expressions(self, include_reset = True):

        """
        Returns a dictionary of each next state / output with its optimized SOP

        include_reset: Whether to include the reset bit in the expressions
        """
        if not hasattr(self, "output_columns"):
            self.make_output_columns()

        output_expressions = {}
        for output in self.all_output_names:
            column = self.output_columns[output]
            output_expressions[output] = optimized_sop(self.all_input_names, column)

        # If there is a reset state and we want to include it:
        if include_reset and self.has_reset:

            # Add the appropriate r or r'
            for bit, output in zip(self.reset_state, self.next_state_bit_names):
                if bit == "1":
                    output_expressions[output] = \
                        f"({output_expressions[output]}) + {self.reset_input_name}"
                else:
                    output_expressions[output] = \
                        f"({output_expressions[output]}){self.reset_input_name}'"

        self.output_expressions = output_expressions
        return output_expressions
    
    def dump_output_expressions(self, filename = "outputs.txt", include_reset = True, clear = False):

        """
        Writes the logic for the FSM's output expressions to a file,
        so that circuit diagrams can be made for it if need be.

        filename: file to write to
        clear: whether or not to empty the file before writing to it
        """

        if not hasattr(self, "output_expressions"):
            self.find_output_expressions(include_reset)

        # Clear the file if chosen
        if clear:
            with open(filename, "w") as f:
                pass

        # Re-open the file in append mode to not overwrite previous stuff
        f = open(filename, "a") 

        # Heading
        f.write(f"{self.name} outputs:\n")
        
        # Outputs
        for output_name in self.output_expressions:
            output_expression = self.output_expressions[output_name]
            f.write(f"{output_name} = {output_expression}\n")
        
        f.write("\n")

        f.close()

    def follow(self, sequence, starting_state):

        """
        Simulates the FSM, following the sequence of inputs from the 
        starting state.

        sequence: can be multiple types:
            - list of strings for more than one input
            - string for one input
            - number of iterations for no inputs
        starting_state: string for starting state of the FSM

        Returns:
        state_sequence: list of states it follows, includes 1st state but
            excludes end state
        output_sequences: dictionary of lists of what each output is
        ending_state: the ending state
        """

        # Process sequence argument into a list

        # For no input, turn number into list of empty strings
        if type(sequence) is int and self.num_inputs == 0:
            sequence = ["" for _ in range(sequence)]
        # For one input, turn string into list
        elif type(sequence) is str and self.num_inputs == 1:
            sequence = [i for i in sequence]
        # For one or more inputs and a list argument, it's already a list
        elif type(sequence) is list and self.num_inputs >= 1:
            pass
        else:
            raise ValueError("Sequence argument type doesn't match number of inputs")

        sequence_length = len(sequence)

        # Initialize the stuff to keep track of
        state = starting_state
        state_sequence = []
        output_sequences = {}
        for output in self.output_names:
            output_sequences[output] = []

        # Move through the sequence
        for step in range(sequence_length):

            # Find the row containing the state and its inputs
            inputs = sequence[step]
            row = self.get_row(state, inputs)

            # Check to make sure it's properly specified
            if len(row["next_states"]) != 1:
                raise ValueError(f"state {state} is improperly specified")

            # Add state to the state sequence
            state_sequence.append(state)

            # Find each output and add it to the output sequences
            for output in self.moore_names:
                output_value = self.get_moore_output_value(state, output)
                output_sequences[output].append(output_value)
            for output in self.mealy_names:
                output_value = self.get_mealy_output_value(state, inputs, output)
                output_sequences[output].append(output_value)

            # Go to the next state
            next_state = row["next_states"][0]
            state = next_state
        
        # Return everything when pattern is finished
        ending_state = state
        return ending_state, state_sequence, output_sequences
    
    def get_row(self, state, input_combo):

        """
        Comb through the dictionaries to find a row with a specific
        state and input combo
        """

        for row in self.rows:

            # Go through all inputs and make sure they are correct
            correct_input = True
            for input, input_value in zip(self.input_names, input_combo):
                if row[input] != input_value:
                    correct_input = False
            
            # Ensure state is correct
            correct_state = (row["state"] == state)

            if correct_input and correct_state:
                return row
    
        # Error if nothing found
        raise ValueError(f"State {state} not found")
    
    def get_rows_from_state(self, state):

        """
        Comb through the dictionaries to find all rows with a specific state
        """

        rows = []
        for combo in self.input_combos:
            rows.append(self.get_row(state, combo))
        return rows

    def get_moore_outputs(self, state):

        """
        Returns the dictionary of outputs for a given state (dict or string)
        """

        if type(state) is str:
            state = self.get_state(state)
        
        return state["outputs"]
    
    def get_moore_output_value(self, state, output_name):

        """
        Returns the output value 0 or 1 for a specific state and output
        
        state: dict or string
        output_name: string
        """

        if type(state) is str:
            state = self.get_state(state)
        
        return state["outputs"][output_name]
    
    def get_mealy_outputs(self, state_name, input_combo):

        """
        Returns the dictionary of outputs for a given state (string)
        and input combo (string)
        """

        row = self.get_row(state_name, input_combo)

        mealy = {}
        for output in self.mealy_names:
            mealy[output] = row[output]

        return mealy
    
    def get_mealy_output_value(self, state_name, input_combo, output_name):

        """
        Returns the output value for a specific state, input combo, and output
        
        state: string
        input_combo: string
        output_name: string
        """

        outputs = self.get_mealy_outputs(state_name, input_combo)
        return outputs[output_name]

    def _rebuild(self, state_notation="Q"):
        """
        Recompute all derived FSM data after any edit to self.fsm_json.
        """
        self.get_inputs_from_json()
        self.get_outputs_from_json()
        self.get_states_from_json(state_notation)
        self.get_state_data_from_json()
        self.evaluate_all_combos()

    @classmethod
    def from_template(cls, template_name, state_notation="Q"):
        if template_name not in TEMPLATES:
            raise ValueError(f"Unknown template '{template_name}'")
        return cls(str(TEMPLATES[template_name]), state_notation=state_notation)
    
    def _get_node_index(self, state_name):
        for i, node in enumerate(self.fsm_json["fsmNodes"]):
            if node["stateName"] == state_name:
                return i
        raise ValueError(f"State '{state_name}' not found")

    def _get_state_name_from_index(self, idx):
        return self.fsm_json["fsmNodes"][idx]["stateName"]
    
    def list_arcs(self):
        arcs = []

        for i, arc in enumerate(self.fsm_json.get("fsmArcs", [])):
            arcs.append({
                "kind": "normal",
                "index": i,
                "start": self._get_state_name_from_index(arc["startNode"]),
                "end": self._get_state_name_from_index(arc["endNode"]),
                "label": arc.get("outputText", "")
            })

        for i, arc in enumerate(self.fsm_json.get("fsmSelfArcs", [])):
            state = self._get_state_name_from_index(arc["node"])
            arcs.append({
                "kind": "self",
                "index": i,
                "start": state,
                "end": state,
                "label": arc.get("outputText", "")
            })

        for i, arc in enumerate(self.fsm_json.get("fsmResetArcs", [])):
            state = self._get_state_name_from_index(arc["node"])
            arcs.append({
                "kind": "reset",
                "index": i,
                "start": "RESET",
                "end": state,
                "label": arc.get("outputText", "")
            })

        return arcs
    
    def remove_arc(self, start_state, end_state, occurrence=0):
        """
        Remove an arc from start_state to end_state.
        Handles both normal arcs and self-arcs.
        """
        count = 0

        if start_state == end_state:
            node_idx = self._get_node_index(start_state)
            for i, arc in enumerate(self.fsm_json.get("fsmSelfArcs", [])):
                if arc["node"] == node_idx:
                    if count == occurrence:
                        del self.fsm_json["fsmSelfArcs"][i]
                        self._rebuild()
                        return
                    count += 1
        else:
            start_idx = self._get_node_index(start_state)
            end_idx = self._get_node_index(end_state)

            for i, arc in enumerate(self.fsm_json.get("fsmArcs", [])):
                if arc["startNode"] == start_idx and arc["endNode"] == end_idx:
                    if count == occurrence:
                        del self.fsm_json["fsmArcs"][i]
                        self._rebuild()
                        return
                    count += 1

        raise ValueError(f"No arc found from {start_state} to {end_state}")
    
    def label_arc(self, start_state, end_state, new_label, occurrence=0):
        """
        Change the outputText of an arc.
        """
        count = 0

        if start_state == end_state:
            node_idx = self._get_node_index(start_state)
            for arc in self.fsm_json.get("fsmSelfArcs", []):
                if arc["node"] == node_idx:
                    if count == occurrence:
                        arc["outputText"] = new_label
                        self._rebuild()
                        return
                    count += 1
        else:
            start_idx = self._get_node_index(start_state)
            end_idx = self._get_node_index(end_state)

            for arc in self.fsm_json.get("fsmArcs", []):
                if arc["startNode"] == start_idx and arc["endNode"] == end_idx:
                    if count == occurrence:
                        arc["outputText"] = new_label
                        self._rebuild()
                        return
                    count += 1

        raise ValueError(f"No arc found from {start_state} to {end_state}")
    
    def remove_reset_arc(self, occurrence=0):
        if occurrence >= len(self.fsm_json.get("fsmResetArcs", [])):
            raise ValueError("No reset arc at that occurrence")

        del self.fsm_json["fsmResetArcs"][occurrence]
        self._rebuild()

    def label_reset_arc(self, new_label, occurrence=0):
        if occurrence >= len(self.fsm_json.get("fsmResetArcs", [])):
            raise ValueError("No reset arc at that occurrence")

        self.fsm_json["fsmResetArcs"][occurrence]["outputText"] = new_label
        self._rebuild()

    def get_json(self):
        return self.fsm_json

    def get_json_string(self, indent=None):
        return json.dumps(self.fsm_json, separators=(",", ":")) if indent is None else json.dumps(self.fsm_json, indent=indent)
    
    def get_fsm_explorer_url(self):
        json_string = json.dumps(self.fsm_json, separators=(",", ":"))
        encoded = quote(json_string, safe="")
        return f"https://dougsummerville.github.io/FSM-Explorer/fsmexplorer.html?{encoded}"
    
    def save_json(self, filename=None, indent=2):
        if filename is None:
            filename = f"{self.name}_modified.txt"

        with open(filename, "w") as f:
            json.dump(self.fsm_json, f, indent=indent)

    def can_remove_arc(self, start_state, end_state, occurrence=0):
        """
        Check whether removing an arc would keep the FSM valid,
        without permanently changing the FSM.
        """
        old_json = copy.deepcopy(self.fsm_json)

        try:
            self.remove_arc(start_state, end_state, occurrence)
            self.verify()
            result = True
        except Exception:
            result = False

        self.fsm_json = old_json
        self._rebuild()
        return result
    
    def find_removable_arcs(self):
        """
        Return removable non-reset arcs.
        """
        removable = []
        seen = {}

        for arc in self.list_arcs():
            if arc["kind"] not in ("normal", "self"):
                continue

            key = (arc["kind"], arc["start"], arc["end"])
            occurrence = seen.get(key, 0)
            seen[key] = occurrence + 1

            if self.can_remove_arc(arc["start"], arc["end"], occurrence):
                arc_copy = dict(arc)
                arc_copy["occurrence"] = occurrence
                removable.append(arc_copy)

        return removable
        
    def get_outgoing_arcs(self, state_name):
        arcs = []
        for arc in self.list_arcs():
            if arc["kind"] in ("normal", "self") and arc["start"] == state_name:
                arcs.append(arc)
        return arcs
    
    def make_input_patterns(input_names):
        patterns = []
        for bits in product([0, 1], repeat=len(input_names)):
            parts = []
            for name, bit in zip(input_names, bits):
                parts.append(name if bit == 1 else f"{name}'")
            patterns.append(" ".join(parts))
        return patterns
    
    def choose_random_fsm_type():
        return random.choice(["moore", "mealy"])

    def assign_random_moore_outputs(self, output_names):
        for node in self.fsm_json["fsmNodes"]:
            values = "".join(random.choice(["0", "1"]) for _ in output_names)
            node["outputText"] = values

    def format_moore_arc_label(input_pattern):
        return input_pattern

    def format_mealy_arc_label(input_pattern, output_bits):
        return f"{input_pattern}/{output_bits}"