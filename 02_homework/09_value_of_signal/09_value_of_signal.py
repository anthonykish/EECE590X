import d2l
import random
import re
import textwrap

pools = d2l.QuestionPool("Valid ways in VHDL to specify 8-bit std_logic_vectors", "pool.csv")

for i in range(20):
    # build the random signals across 10 iterations
    signalA = ""
    signalF = ""
    signalFChange = ""

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

    process_code = textwrap.dedent(f"""\
    process(ALL) begin
        f <= "{signalF}";
        if a = '{randomA}' then
            f <= "{signalFChange}";
        end if;
    end process;
    """)


    escaped = process_code.replace("<", "&lt;").replace(">", "&gt;")
    
    html_process = escaped.replace(" ", "&nbsp;").replace("\n", "<br/>")

    qtext = (
        f"<p>Given the VHDL process below. Assume the value of signal <code>a</code> is "
        f"'<code>{signalA}</code>'. What is the value of signal <code>f</code>?</p>"
        f"<pre style='margin:0; padding:0; background:transparent; border:none;"
        f"font-family:monospace; white-space:pre; line-height:1.2; tab-size:4;'>"
        f"{html_process}</pre>"
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

