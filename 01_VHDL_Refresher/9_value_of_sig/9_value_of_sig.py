import random
import d2l

pool = d2l.QuestionPool("VHDL Aggregate Split (Fill in)", "pool.csv")

def slv(nbits: int) -> str:
    return f"std_logic_vector({nbits-1} downto 0)"

def rand_bits(n: int) -> str:
    return "".join(random.choice("01") for _ in range(n))

def partition_8_into_3():
    """Return positive integers (wb, wc, wd) with wb+wc+wd=8."""
    wb = random.randint(1, 6)         # leave at least 1 for wc and wd
    wc = random.randint(1, 7 - wb)    # leave at least 1 for wd
    wd = 8 - wb - wc
    return wb, wc, wd

for _ in range(15):
    wb, wc, wd = partition_8_into_3()
    a_bits = rand_bits(8)

    # VHDL aggregate assignment maps left-to-right from MSB to LSB
    b_bits = a_bits[:wb]
    c_bits = a_bits[wb:wb+wc]
    d_bits = a_bits[wb+wc:]

    # Force HTML rendering by starting with a tag (your library checks HTML at string start)
    qtext = (
        f"<p>Assume sig_a has type {slv(8)}, "
        f"sig_b has type {slv(wb)}, "
        f"sig_c has type {('std_logic' if wc == 1 else slv(wc))}, "
        f"and sig_d has type {slv(wd)}.&nbsp; Given the following concurrent signal assignments:</p>"
        f"<pre>"
        f"sig_a <= \"{a_bits}\";\n"
        f"(sig_b, sig_c, sig_d) <= sig_a;\n"
        f"</pre>"
        f"<p>"
        f"The value of sig_b, in binary, is ____<br>"
        f"The value of sig_c, in binary, is ____<br>"
        f"The value of sig_d, in binary, is ____<br><br>"
        f"<em>Enter your answers as: sig_b sig_c sig_d (separated by spaces or new lines).</em>"
        f"</p>"
    )

    question = d2l.SAQuestion(text=qtext, points=10)

    # Accept answers separated by spaces and/or newlines, optional commas
    # Example accepted: 010 1 1100   OR  010\n1\n1100
    question.add_answer(f"{b_bits} {c_bits} {d_bits}")            # space-separated
    question.add_answer(f"{b_bits}\n{c_bits}\n{d_bits}")          # newline-separated
    question.add_answer(f"{b_bits}\r\n{c_bits}\r\n{d_bits}")      # windows newlines
    question.add_answer(f"{b_bits},{c_bits},{d_bits}")            # comma-separated
    question.add_answer(f"{b_bits}, {c_bits}, {d_bits}")          # comma+space

    pool.add_question(question)

pool.package()
