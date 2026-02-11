import random
import d2l
import html

pool = d2l.QuestionPool("VHDL slicing + reductions (randomized matching)", "pools.csv")


def rand_bits(n: int) -> str:
    return "".join(random.choice("01") for _ in range(n))


def bits_to_slv_literal(bits: str) -> str:
    # 4-bit or 8-bit vector literal
    return f"\"{bits}\""


def bit_literal(b: int) -> str:
    return f"'{b}'"


def slice_bits(vec_bits: str, hi: int, lo: int) -> str:
    # vec_bits is MSB..LSB string of length 8
    # returns MSB..LSB string of the slice hi downto lo
    # index 7 is vec_bits[0], index 0 is vec_bits[7]
    out = []
    for idx in range(hi, lo - 1, -1):
        out.append(vec_bits[7 - idx])
    return "".join(out)


def reduce_xor(bits: str) -> int:
    # parity: 1 if odd number of '1's
    ones = sum(1 for b in bits if b == "1")
    return ones % 2


def reduce_xnor(bits: str) -> int:
    # XNOR reduction = NOT XOR reduction (even parity -> 1)
    return 1 - reduce_xor(bits)


def make_question():
    # --- Randomly assign *roles* to signal names ---
    names = ["a", "b", "c", "d", "e", "f", "g", "h"]
    random.shuffle(names)

    role = {
        "bit_xor": names[0],     # std_logic, gets XOR reduction
        "bit_xnor": names[1],    # std_logic, gets XNOR reduction on slice
        "bit_c": names[2],       # std_logic, first of 2-bit slice
        "bit_d": names[3],       # std_logic, second of 2-bit slice
        "vec4_1": names[4],      # std_logic_vector(3 downto 0)
        "vec4_2": names[5],      # std_logic_vector(3 downto 0)
        "vec8_src": names[6],    # std_logic_vector(7 downto 0) source assigned literal
        "vec8_out": names[7],    # std_logic_vector(7 downto 0) derived by concat
    }

    # --- Random source vector and random slice params ---
    g_bits = rand_bits(8)  # MSB..LSB (bit7..bit0)

    # concat split point k: h <= g(k-1 downto 0) & g(7 downto k)
    # (a rotate-ish split; always valid for 1..7)
    k = random.randint(1, 7)

    # vec4 assignment: split into two 4-bit chunks, maybe swapped
    # (keep it always correct and clean)
    upper4 = slice_bits(g_bits, 7, 4)
    lower4 = slice_bits(g_bits, 3, 0)
    swapped = random.choice([True, False])

    # XNOR slice: choose a random downto range within 7..0, length 2..8
    hi = random.randint(1, 7)
    lo = random.randint(0, hi - 1)  # ensures at least 2 bits

    # (c,d) slice: random 2-bit slice
    cd_hi = random.randint(1, 7)
    cd_lo = cd_hi - 1

    # --- Compute resulting values ---
    # vec8_out bits:
    left = slice_bits(g_bits, k - 1, 0)     # low part
    right = slice_bits(g_bits, 7, k)        # high part
    h_bits = left + right

    # vec4s:
    v4_1_bits, v4_2_bits = (lower4, upper4) if swapped else (upper4, lower4)

    # reductions:
    a_bit = reduce_xor(g_bits)
    b_bit = reduce_xnor(slice_bits(g_bits, hi, lo))

    # (c,d) from g(cd_hi downto cd_lo):
    cd_bits = slice_bits(g_bits, cd_hi, cd_lo)  # 2 bits, MSB..LSB
    c_bit = int(cd_bits[0])
    d_bit = int(cd_bits[1])

    # Map computed values back onto the randomized signal names
    values = {
        role["vec8_src"]: bits_to_slv_literal(g_bits),
        role["vec8_out"]: bits_to_slv_literal(h_bits),
        role["vec4_1"]: bits_to_slv_literal(v4_1_bits),
        role["vec4_2"]: bits_to_slv_literal(v4_2_bits),
        role["bit_xor"]: bit_literal(a_bit),
        role["bit_xnor"]: bit_literal(b_bit),
        role["bit_c"]: bit_literal(c_bit),
        role["bit_d"]: bit_literal(d_bit),
    }
    

    # --- Build declarations (grouped nicely) ---
    bits_group = ", ".join([role["bit_xor"], role["bit_xnor"], role["bit_c"], role["bit_d"]])
    v4_group = ", ".join([role["vec4_1"], role["vec4_2"]])
    v8_group = ", ".join([role["vec8_src"], role["vec8_out"]])

    decl = (
        f"signal {bits_group}: std_logic;\n"
        f"signal {v4_group}: std_logic_vector(3 downto 0);\n"
        f"signal {v8_group}: std_logic_vector(7 downto 0);\n"
    )

    # --- Build concurrent assignments (VHDL-ish notation like your prompt) ---
    # Use <= and parentheses/concat like your example.
    src = role["vec8_src"]
    out = role["vec8_out"]
    v41 = role["vec4_1"]
    v42 = role["vec4_2"]
    bxor = role["bit_xor"]
    bxnor = role["bit_xnor"]
    bc = role["bit_c"]
    bd = role["bit_d"]

    assigns = []
    assigns.append(f'{src} <= {bits_to_slv_literal(g_bits)};')
    assigns.append(f'{out} <= {src}({k-1} downto 0) & {src}(7 downto {k});')

    if swapped:
        assigns.append(f'({v41}, {v42}) <= ({src}(3 downto 0), {src}(7 downto 4));')
    else:
        assigns.append(f'({v41}, {v42}) <= ({src}(7 downto 4), {src}(3 downto 0));')

    assigns.append(f'{bxor} <= XOR({src});')
    assigns.append(f'{bxnor} <= XNOR({src}({hi} downto {lo}));')
    assigns.append(f'({bc}, {bd}) <= {src}({cd_hi} downto {cd_lo});')

    code_block = decl + "\n" + "\n".join(assigns)

    # --- Make Matching layout: values are (a)(b)(c)..., student matches signal names to letters ---
    letters = ["(a)", "(b)", "(c)", "(d)", "(e)", "(f)", "(g)", "(h)"]
    # Shuffle the value list so it’s not in the same order as the signals
    items = list(values.items())  # [(signalName, literalStr), ...]
    random.shuffle(items)
    
    # items is list of (signal, literal) already shuffled
    lines = []
    for i, (_, lit) in enumerate(items):
        lit = str(lit).replace("\r\n", "\n").replace("\r", "\n")  # normalize
        lines.append(f"{letters[i]} {lit}")

    value_lines = "\n".join(lines) + "\n"  # <-- force trailing newline


    value_lines = "\n".join([f"{letters[i]} {lit}" for i, (_, lit) in enumerate(items)])

    qtext = (
        "<p><b>Given the following signal declarations and concurrent signal assignments:</b></p>"
        f"<pre style='margin:0; padding:0; background:transparent; border:none; font-family:monospace; white-space:pre;'>"
        f"{html.escape(code_block)}"
        f"</pre>"
        "<p><b>Using correct VHDL notation for literals, match each signal to its value.</b></p>"
        "<p><b>Values:</b></p>"
        f"<pre style='margin:0; padding:0; background:transparent; border:none; font-family:monospace; white-space:pre;'>"
        f"{html.escape(value_lines)}"
        f"</pre>"
    )

    question = d2l.MQuestion(text=qtext, points=10, shuffle=True)

    # Add answers: term is the SIGNAL NAME; match is the letter for its value line
    # We need: signal -> (letter for that signal's value line)
    signal_to_letter = {sig: letters[i] for i, (sig, _) in enumerate(items)}

    # You can also randomize which subset of signals to ask about by sampling here.
    for sig in sorted(signal_to_letter.keys()):
        question.add_answer(sig, signal_to_letter[sig])

    return question


# Generate a bunch
for _ in range(20):
    pool.add_question(make_question())

pool.package()
