import d2l
import random
import re

pools = d2l.QuestionPool("Valid ways in VHDL to specify 8-bit std_logic_vectors", "pool.csv")

for i in range(20):
    # build the random signals across 10 iterations
    signalA = ""
    signalF = ""
    signalFChange = ""
    randomA = 0

    for j in range(10):
        randInt = random.randint(0, 1)

        if j == 0:
            signalA = str(randInt)
        elif 1 <= j <= 4:
            signalF += str(randInt)
        elif 5 <= j <= 8:
            signalFChange += str(randInt)
        else:
            randomA = randInt

    process_code = f"""
    process( ALL ) begin
        f <= "{signalF}";
        if a = '{str(randomA)}' then
            f <= "{signalFChange}";
        end if;
    end process;"""

    # escape angle brackets for HTML display
    html_process = process_code.replace("<", "&lt;").replace(">", "&gt;")

    qtext = (
        f"<p>Given the VHDL process below. Assume the value of signal <code>a</code> is "
        f"'<code>{signalA}</code>'. What is the value of signal <code>f</code>?</p>"
        f"<pre style='background:#f6f8fa;padding:10px;border-radius:6px;"
        f"font-family:monospace;white-space:pre;'><code>{html_process}</code></pre>"
    )

    question = d2l.SAQuestion(text=qtext, points=10)

    # Use [01]* and escape the literal bitstrings for regex safety; add as regex answer
    if signalA == str(randomA):
        pattern = f"[01]*{re.escape(signalFChange)}$"
    else:
        pattern = f"[01]*{re.escape(signalF)}$"

    question.add_answer(pattern, points=100, is_regex=True)

    pools.add_question(question)

pools.package()

