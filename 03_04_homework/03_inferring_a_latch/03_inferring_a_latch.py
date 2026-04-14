import d2l
import random

pools = d2l.QuestionPool("Inferring a latch", "pool.csv")

latch_inference = {
    '<pre><code>process(all) begin\n  if en = \'1\' then\n    q &lt;= d;\n  end if;\nend process;</code></pre>': 1,

    '<pre><code>process(all) begin\n  if sel = "00" then\n    y &lt;= a;\n  elsif sel = "01" then\n    y &lt;= b;\n  end if;\n end process;</code></pre>': 1,

    '<pre><code>process(all) begin\n  case sel is\n    when "00" =&gt; y &lt;= a;\n    when "01" =&gt; y &lt;= b;\n  end case;\n end process;</code></pre>': 1,

    '<pre><code>process(all) begin\n  case sel is\n    when "00" =&gt; y &lt;= a;\n    when others =&gt; null;\n  end case;\n end process;</code></pre>': 1,

    '<pre><code>y &lt;= a when sel = \'1\';</code></pre>': 1,

    '<pre><code>y &lt;= a when sel = "00" else\n     b when sel = "01";</code></pre>': 1,

    '<pre><code>process(clk) begin\n  if rising_edge(clk) then\n    q &lt;= d;\n  end if;\n end process;</code></pre>': 0,

    '<pre><code>process(clk) begin\n  if rising_edge(clk) then\n    if en = \'1\' then\n      q &lt;= d;\n    end if;\n  end if;\n end process;</code></pre>': 0,

    '<pre><code>process(all) begin\n  if en = \'1\' then\n    y &lt;= a;\n  else\n    y &lt;= b;\n  end if;\n end process;</code></pre>': 0,

    '<pre><code>process(all) begin\n  y &lt;= b;\n  if en = \'1\' then\n    y &lt;= a;\n  end if;\n end process;</code></pre>': 0,

    '<pre><code>process(all) begin\n  case sel is\n    when "00" =&gt; y &lt;= a;\n    when "01" =&gt; y &lt;= b;\n    when others =&gt; y &lt;= c;\n  end case;\n end process;</code></pre>': 0,

    '<pre><code>with sel select\n  y &lt;= a when "00",\n       b when "01",\n       c when others;</code></pre>': 0,

    '<pre><code>y &lt;= a and b;</code></pre>': 0,
}

for i in range(30):
    choices = random.sample( sorted(latch_inference) , 4)

    qtext = "Which of the following VHDL code snippets would infer a latch?"

    question = d2l.MSQuestion( text=qtext, points=10, shuffle=True )
    for choice in choices:
        question.add_answer( choice, latch_inference[choice])
    pools.add_question( question )

pools.package()