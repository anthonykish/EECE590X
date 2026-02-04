## Decoder, Encoder, and Mux Drawing in Ascii Art
#   Implements functions for Decoder, Encoder, and Mux drawings
#   Shape of components are boxes
#   Takes parameters to determine size, input bits, and output bits
#   Provides all external connections
#   Uses parameter for output if given, else solves for solution when
#   show_ans = true

# decoderDraw(in_size)
#   Takes number of inputs as parameter
#   Optionally takes the input string, output high index, and 
#   a boolean to decide whether or not the answer should be shown
#   Returns html for ascii drawing of decoder of specified size
def decoderDraw(in_size, s="", out_ind = -1, show_ans=False):  
    import math
    out_size = 2**in_size
    
    out_def = '?'
    if out_ind > -1:
        out_def = '0'
    
    if len(s) == 0:
        s = s.zfill(in_size).replace('0', 'X')
    elif len(s) != in_size:
        return "Invalid bit string for input size"
    elif show_ans:
        if out_ind <-1:
            out_ind = int(s, 2)
        out_def = '0'

    outs_cnt = 0
    res = "<pre>  +------------------------+ <br>  |        Decoder         |<br>"
    
    for i in range(out_size):
        out_val = out_def
        if i == out_ind:
            out_val = '1'
        if i < in_size:
            if i<10:
                res+=f"{s[in_size-(1+i)]}--->in{i}             Out{i} ---> {out_val}<br>"
            elif i<100:
                res+=f"{s[in_size-(1+i)]}--->in{i}           Out{i} ---> {out_val}<br>"
            else:
                res+=f"{s[in_size-(1+i)]}--->in{i}          Out{i} ---> {out_val}<br>"
            outs_cnt += 1
        else:
            if i<10:
                res+=f"  |                  Out{i} ---> {out_val}<br>"
            elif i<100:
                res+=f"  |                 Out{i} ---> {out_val}<br>"
            else:
                res+=f"  |                Out{i} ---> {out_val}<br>"
    
    res += "  |                        |<br>  +------------------------+</pre>"
    return res

# encoderDraw(in_size)
#   Takes number of inputs as parameter
#   Optionally takes the input string, output string, and 
#   a boolean to decide whether or not the answer should be shown
#   Returns html for ascii drawing of encoder of specified size
def encoderDraw(in_size, s="", o="", show_ans=False):
    import math
    out_size = int(math.log2(in_size))
    ans = "".zfill(out_size).replace('0', 'X')
            
    if len(s) == 0:
        s = s.zfill(in_size).replace('0', 'X')
    elif len(s) != in_size:
        return "Invalid bit string for input size"
    elif s.count('1')!=1:
        return "Invalid bit string - encoder should have at most one input high"
    elif show_ans:
        val = (in_size-1) - s.find('1')
        ans = bin(val)[2:].zfill(out_size)
    
    if len(o) == out_size:
        ans = o
    
    ans_cnt = out_size-1
    res = "<pre>  +------------------------+ <br>  |        Encoder         |<br>"
    
    for i in range(in_size):
        if i < out_size:
            if (in_size-i-1)<10:
                res+=f"{s[in_size-(1+i)]}---> in{i}            Out{i} ---> {ans[ans_cnt]}<br>"
            elif (in_size-i-1)<100:
                res+=f"{s[in_size-(1+i)]}---> in{i}           Out{i} ---> {ans[ans_cnt]}<br>"
            else:
                res+=f"{s[in_size-(1+i)]}---> in{i}          Out{i} ---> {ans[ans_cnt]}<br>"
            ans_cnt -= 1
        else:
            if (in_size-i-1)<10:
                res+=f"{s[in_size-(1+i)]}---> in{i}                  |<br>"
            elif (in_size-i-1)<100:
                res+=f"{s[in_size-(1+i)]}---> in{i}                 |<br>"
            else:
                res+=f"{s[in_size-(1+i)]}---> in{i}                |<br>"
    
    res += "  |                        |<br>  +------------------------+</pre>"
    return res

# muxBoxDraw(sel_size)
#   Takes number of select signals as parameter
#   Optionally takes the input string, select string, output string, 
#   and a boolean to decide whether or not the answer should be shown
#   Returns html for ascii drawing of mux of specified size
#   Mux in shape of a box, not trapezoid
def muxBoxDraw(sel_size, sel="", ins="", o="", show_ans=False):
    import math
    in_size = 2**sel_size
    out = "X"
    sel_defined = True
    ins_defined = True

    if len(sel) == 0:
        sel = sel.zfill(sel_size).replace('0', 'X')
        sel_defined = False
    elif len(sel) != sel_size:
        sel_defined = False
        return "Invalid bit string for sel size"
    
    if len(ins)==0:
        ins=ins.zfill(in_size).replace('0', 'X')
    elif len(ins) != in_size:
        return "Invalid bit string for input size"
    
    if len(o):
        out = o
    elif show_ans:
        if sel_defined and ins_defined:
            out = ins[(in_size-1)-(int(sel,2))]

    res = "<pre>  +------------------------+ <br>  |           Mux          |<br>"
    
    for i in range(in_size):
        if (i)<10:
            res+=f"{ins[in_size-(1+i)]}---> in{i}                  |<br>"
        elif (i) <100:
            res+=f"{ins[in_size-(1+i)]}---> in{i}                 |<br>"
        else:
            res+=f"{ins[in_size-(1+i)]}---> in{i}                |<br>"
    
    res += f"  |                   Out ---> {out}<br>" 
    
    if sel_size<9:
        res+= f"  |        sel[{sel_size-1}:0]        |<br>"
    else:
        res+= f"  |        sel[{sel_size-1}:0]       |<br>"
    res += "  |         //_\\          |<br>"
    res += "  +-----------|------------+<br>              |<br>"
    lastLineSpacing = "--------------!"
    lastLine = sel + lastLineSpacing[sel_size:]
    res += lastLine + "</pre>"
    return res

# muxTrapDraw(sel_size)
#   NOT IMPLEMENTED YET - trapezoidal mux

# # Example usage
# # dec = decoderDraw(5, "01001")
# dec = decoderDraw(5, out_ind=4, show_ans=True)
# # enc = encoderDraw(16, "0010000000000000")
# enc = encoderDraw(16, o="0010", show_ans=True)
# # muxBox = muxBoxDraw(3, ins="00011001")
# muxBox = muxBoxDraw(3, sel="011", ins="00011001", o="", show_ans=True)
# #muxBox = muxBoxDraw(8, "10011100", "1011010101101000100101011011111000110101011001111011100010111000010011000010110111111011101001110000010000001000110110101101011101111100011000000111000100101100101101101100001101011000001001011010010100011111000100111111001001111011101010010100000001100001")
# with open("decoderInputs.html", "w") as file:
#     file.write(dec)
# with open("encoderInputs.html", "w") as file:
#     file.write(enc)
# with open("muxBoxInputs.html", "w") as file:
#     file.write(muxBox)