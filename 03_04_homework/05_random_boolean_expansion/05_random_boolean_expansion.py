import random
import d2l

pools = d2l.QuestionPool("Expansion Theorem factoring", "pool.csv")

BASE_FUNCS = [
    "ab'c'd'+a'bcd+c'd",
    "a'cd+abc+ab'c'+b'd",
    "a'd+a'b'c+abc'd'+a'b'c'd'",
    "a'b'd+b'c'd'+a'bcd+ab'cd+ad",
    "a'b'+a'bc'+abcd+ab'cd'",
    "abd'+c'd+cd'+a'd'",
]

VARS = ["a", "b", "c", "d"]

def eval_term(term, asg):
    # term like "ab'c" (no +), AND of literals
    i = 0
    while i < len(term):
        v = term[i]
        if v in VARS:
            neg = (i + 1 < len(term) and term[i + 1] == "'")
            bit = asg[v]
            if (bit == 1 and neg) or (bit == 0 and not neg):
                return 0
            i += 2 if neg else 1
        else:
            return 0
    return 1

def eval_sop(expr, asg):
    # expr like "ab'+c'd"
    expr = expr.replace(" ", "")
    for t in expr.split("+"):
        if t == "1":
            return 1
        if t == "0" or t == "":
            continue
        if eval_term(t, asg):
            return 1
    return 0

def assignments(vars_list):
    n = len(vars_list)
    for i in range(2**n):
        bits = [(i >> (n-1-j)) & 1 for j in range(n)]
        yield {vars_list[j]: bits[j] for j in range(n)}

def minterm(vars_list, asg):
    return "".join(v if asg[v] else f"{v}'" for v in vars_list)

def outside_terms_sop(original_sop: str, x: str) -> str:
    s = original_sop.replace(" ", "")
    outs = []
    for t in s.split("+"):
        if x not in t:
            outs.append(t)
    if not outs:
        return "0"
    seen = set()
    uniq = []
    for t in outs:
        if t not in seen:
            uniq.append(t)
            seen.add(t)
    return "+".join(uniq)

# small 3-var simplifier based on truth table patterns
def simplify_3var_sop(rem_vars, ones_set):
    # ones_set is set of tuples bits (a,b,c) in rem_vars order
    n = len(rem_vars)  # should be 3
    if len(ones_set) == 0:
        return "0"
    if len(ones_set) == 2**n:
        return "1"

    # Try single-literal forms: v or v'
    for idx, v in enumerate(rem_vars):
        ones_if_v1 = {(b0,b1,b2) for (b0,b1,b2) in ones_set if (b0,b1,b2)[idx] == 1}
        ones_if_v0 = {(b0,b1,b2) for (b0,b1,b2) in ones_set if (b0,b1,b2)[idx] == 0}
        if len(ones_if_v1) == 4 and len(ones_set) == 4 and len(ones_if_v0) == 0:
            return v
        if len(ones_if_v0) == 4 and len(ones_set) == 4 and len(ones_if_v1) == 0:
            return f"{v}'"

    # Try simple 2-literal AND: v w, v w', v' w, v' w'
    lits = []
    for i in range(n):
        for j in range(i+1, n):
            vi, vj = rem_vars[i], rem_vars[j]
            for ni in [0,1]:
                for nj in [0,1]:
                    # term holds when vi=ni and vj=nj
                    cover = set()
                    for asg in assignments(rem_vars):
                        if asg[vi]==ni and asg[vj]==nj:
                            cover.add(tuple(asg[v] for v in rem_vars))
                    if cover == ones_set:
                        ti = vi if ni==1 else f"{vi}'"
                        tj = vj if nj==1 else f"{vj}'"
                        return f"{ti}{tj}"

    # Fallback: canonical minterm SOP (still max 8 terms)
    parts = []
    for bits in sorted(ones_set):
        asg = {rem_vars[k]: bits[k] for k in range(n)}
        parts.append(minterm(rem_vars, asg))
    return "+".join(parts)

def cofactor_sop(original_sop, x, xval):
    rem = [v for v in VARS if v != x]
    ones = set()
    for asg in assignments(rem):
        full = dict(asg)
        full[x] = xval
        if eval_sop(original_sop, full) == 1:
            ones.add(tuple(asg[v] for v in rem))
    return simplify_3var_sop(rem, ones)

def drop_one_product(sop: str) -> str:
    if sop in ("0", "1") or "+" not in sop:
        return sop
    parts = sop.split("+")
    parts.pop(random.randrange(len(parts)))
    return "+".join(parts) if parts else "0"

def add_outside_inside(sop: str, outside: str) -> str:
    if outside == "0":
        return sop
    if sop == "0":
        return outside
    parts = set(sop.split("+"))
    for ot in outside.split("+"):
        parts.add(ot)
    return "+".join(sorted(parts, key=lambda x: (len(x), x)))

def build_question(original_sop, x):
    outside = outside_terms_sop(original_sop, x)

    f0 = cofactor_sop(original_sop, x, 0)
    f1 = cofactor_sop(original_sop, x, 1)

    # correct: include outside inside both cofactors (your style)
    f0c = add_outside_inside(f0, outside)
    f1c = add_outside_inside(f1, outside)
    correct = f"f(a,b,c,d)={x}'({f0c})+{x}({f1c})"

    wrongs = []
    if outside != "0":
        wrongs.append(f"f(a,b,c,d)={x}'({f0})+{x}({f1})+{outside}")
    wrongs.append(f"f(a,b,c,d)={x}'({f1c})+{x}({f0c})")
    wrongs.append(f"f(a,b,c,d)={x}'({drop_one_product(f0c)})+{x}({f1c})")
    wrongs.append(f"f(a,b,c,d)={x}'({f0c})+{x}({drop_one_product(f1c)})")
    if outside != "0":
        wrongs.append(f"f(a,b,c,d)={x}'({f0c})+{x}({f1})")
    else:
        wrongs.append(f"f(a,b,c,d)={x}'({f0c})+{x}({f1c})+a'b'")

    # unique, exactly 6 options
    seen = {correct}
    options = [correct]
    for w in wrongs:
        if w not in seen:
            options.append(w)
            seen.add(w)
        if len(options) == 6:
            break

    while len(options) < 6:
        pad = f"f(a,b,c,d)={x}'({f0})+{x}({f1})"
        if pad not in seen:
            options.append(pad)
            seen.add(pad)
        else:
            options.append(f"f(a,b,c,d)={x}'({f0})+{x}({f1})+c'd")
            break

    qtext = (
        "<p>Which of the following is the correct form of the Boolean equation<br>"
        f"<b>f(a,b,c,d)={original_sop}</b><br><br>"
        f"factored on <b>{x}</b> by applying the Expansion Theorem? "
        "Note that there may be multiple equivalent expressions, but only one matches "
        "application of the Expansion Theorem.<p>"
    )
    return qtext, correct, options

for _ in range(20):
    sop = random.choice(BASE_FUNCS)
    x = random.choice(VARS)

    qtext, correct, options = build_question(sop, x)

    question = d2l.MCQuestion(text=qtext, points=10, shuffle=True)
    for opt in options:
        question.add_answer(opt, 100 if opt == correct else 0)

    pools.add_question(question)

pools.package()
