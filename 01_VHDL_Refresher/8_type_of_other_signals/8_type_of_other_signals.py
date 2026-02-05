import random
import d2l

pool = d2l.QuestionPool("VHDL Slice Types", "pool.csv")

def slv(nbits: int) -> str:
    return f"std_logic_vector({nbits-1} downto 0)"

def pick_slice(width: int, max_bit: int = 7):
    lo = random.randint(0, max_bit - (width - 1))
    hi = lo + (width - 1)
    return hi, lo

def build_question():
    # --- Randomize ONLY the slices/indices ---
    # sig_c: random width 2..7
    c_width = random.randint(2, 7)
    c_hi, c_lo = pick_slice(c_width)

    # sig_d: fixed “bit & bit & slice” shape, random bit and slice width 2..6
    d_bit = random.randint(0, 7)
    d_width = random.randint(2, 6)      # tail slice width
    d_hi, d_lo = pick_slice(d_width)
    d_total = 2 + d_width               # two single bits + tail slice

    # sig_e: split into k and 8-k chunks (both non-empty), optionally swapped
    k = random.randint(1, 7)
    left = (7, 8 - k)
    right = (7 - k, 0)
    if random.choice([True, False]):
        e1, e2 = left, right
    else:
        e1, e2 = right, left

    # sig_f: random single bit
    f_bit = random.randint(0, 7)

    # --- Build question text in FIXED signal order ---
    # Start with an HTML tag so your d2l library marks it as HTML (line breaks render)
    qtext = (
        "<p>A VHDL description contains the concurrent signal assignments below.&nbsp; "
        "You know that sig_a has type std_logic_vector(7 downto 0).&nbsp; "
        "Determine the type of the other signals.</p>"
        "<pre>"
        f"sig_b <= sig_a;\n"
        f"sig_c <= sig_a({c_hi} downto {c_lo});\n"
        f"sig_d <= sig_a({d_bit}) & sig_a({d_bit}) & sig_a({d_hi} downto {d_lo});\n"
        f"sig_e <= (sig_a({e1[0]} downto {e1[1]}), sig_a({e2[0]} downto {e2[1]}));\n"
        f"sig_f <= sig_a({f_bit});\n"
        "</pre>"
    )

    question = d2l.MQuestion(text=qtext, points=10, shuffle=True)

    # --- Add correct matches (also fixed order) ---
    question.add_answer("sig_b", slv(8))
    question.add_answer("sig_c", slv(c_width))
    question.add_answer("sig_d", slv(d_total))
    question.add_answer("sig_e", slv(8))
    question.add_answer("sig_f", "std_logic")

    # --- Add extra unused choices (optional) ---
    choice_bank = ["std_logic"] + [slv(n) for n in range(2, 9)]  # 2..8 bits + std_logic
    used = {slv(8), slv(c_width), slv(d_total), "std_logic"}
    for ch in choice_bank:
        if ch not in used:
            question.add_answer("", ch)  # empty match => shows as option, matches nothing

    return question

# Generate multiple versions; signal order stays the same every time
for _ in range(15):
    pool.add_question(build_question())

pool.package()
