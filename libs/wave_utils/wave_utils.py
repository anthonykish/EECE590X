import random
import urllib.parse
import wavedrom
from logic_utils.logic_utils import b_format, to_decimal

def make_random_signal(length = 20, num_toggles = None):

    """
    Makes a random wavedrom signal in dotted form

    length (int): length of the signal in ns
    num_toggles (int): by default will be a value between 2 and 5

    """

    signal = []

    if not num_toggles:
        num_toggles = random.choice([2,3,4,5])

    if num_toggles >= length:
        raise Exception("num_toggles must be less than length")

    # Pick random points for the signal to toggle
    toggle_pts = random.sample(range(1,length), num_toggles)

    signal_value = random.choice([0, 1])
    signal.append(signal_value)

    # Generate the signals
    for i in range(1, length):
        # If it's time to toggle, toggle the signal
        if i in toggle_pts:
            signal_value = 1 - signal_value
            # When toggling, put the 0 or 1 in the wavedrom signal
            signal.append(signal_value)
        # Otherwise put . in the wavedrom signal
        else:
            signal.append(".")

    # Turn list into string
    signal = [str(i) for i in signal]
    signal = "".join(signal)

    return signal

def make_clock(length, period=10, first_rising_edge=5):
    """
    Makes a wavedrom signal representing a clock
    length: length of the signal in ns
    period: clock period in ns, must be even, default 10
    first_rising_edge: position of first rising edge, default 5
    """

    if period % 2 != 0:
        raise Exception("Clock period must be even")

    signal = []
    signal_value = 0

    # (Dotless form)
    # Generate a longer clock signal so a portion of it can be taken later
    for i in range(length + period):
        # Toggle the signal on multiples of half the period
        if i % (period/2) == 0:
            signal_value = 1 - signal_value
        
        # Put the 0 or 1 in the list
        signal.append(signal_value)
    
    # Turn list into string
    signal = [str(i) for i in signal]
    signal = "".join(signal)

    # Find out which portion to take to align the first rising edge
    start = period - first_rising_edge
    end = start + length
    signal = signal[start:end]

    signal = to_dotted(signal)

    return signal

def make_pulses(length, on_min, on_max, off_min, off_max, initial = ""):
    
    """
    Makes a wavedrom signal with pulses that are on/off
    for a specified length.

    length: length of the whole signal
    on_min: minimum length of high sections
    on_max: maximum length of high sections
    off_min: minimum length of low sections
    off_max: maximum length of low sections
    initial: starting value, either "0" or "1"
    """

    signal = ""

    if initial:
        signal_value = initial
    else:
        signal_value = random.choice(["0", "1"])
    
    while len(signal) < length:
        # Add a number of chars in the appropriate range, then toggle
        if signal_value == "0":
            signal += ("0" * random.randint(off_min, off_max))
            signal_value = "1"
        else:
            signal += ("1" * random.randint(on_min, on_max))
            signal_value = "0"
        
    signal = signal[0:length]
    signal = to_dotted(signal)
    return signal
    

def to_dotless(dotted):

    """
    Turns a dotted signal (1..0..1.) into dotless (11100011)
    """
    
    dotless = ""
    signal_value = ""

    # Iterate through every character in the dotted signal
    for i in dotted:
        # Turn dots into 1 or 0 depending on what was last seen
        if i == ".":
            dotless += signal_value
        # Preserve 1s and 0s while noting what was last seen
        else:
            dotless += i
            signal_value = i

    return dotless

def to_dotted(dotless):
    """
    Turns a dotless signal (11100011) into dotted form (1..0..1.)
    """

    dotted = ""
    signal_value = ""

    for i in dotless:
        # If the character is a repeat, replace it with a dot
        if i == signal_value:
            dotted += "."
        # Otherwise preserve the 1 or 0 (or x) and update what was last seen
        else:
            dotted += i
            signal_value = i

    return dotted

# Legacy function names
def binary_to_wavedrom(binary):
    return to_dotted(binary)
def wavedrom_to_binary(wavedrom):
    return to_dotless(wavedrom)

def wavedrom_gate(gate, a, b="", delay=0):
    """
    Puts two wavedrom signals of same length through a logic gate
    a: first wavedrom dot format signal (1..0.1..)
    b: second wavedrom dot format signal if need be
    gate: can be "or", "and", "not", "xor", "xnor", "nand", "nor", or "buf"
    delay: delay in ns to shift output
    """
    
    length = len(a)
    gate = gate.lower()

    # Convert dotted signal to dotless format
    a = to_dotless(a)
    a = a.lower()

    # Do the same with b if specified
    if b:
        b = to_dotless(b)
        b = b.lower()

    out = ""

    # Apply bit logic individually to each bit in a and b
    for i in range(len(a)):

        
        a_bit = int(a[i]) if a[i].isdigit() else a[i]

        if b:
            b_bit = int(b[i]) if b[i].isdigit() else b[i]

        # Unknown going into a gate always outputs an unknown
        if a[i] == "x" or (b and b[i] == "x"):
            out_bit = "x"
        
        elif gate == "buf":
            out_bit = a_bit
        elif gate == "not":
            out_bit = ~a_bit
        elif gate == "or":
            out_bit = a_bit | b_bit
        elif gate == "and":
            out_bit = a_bit & b_bit
        elif gate == "xor":
            out_bit = a_bit ^ b_bit
        elif gate == "nor":
            out_bit = ~(a_bit | b_bit)
        elif gate == "nand":
            out_bit = ~(a_bit & b_bit)
        elif gate == "xnor":
            out_bit = ~(a_bit ^ b_bit)
        else:
            raise Exception("Invalid gate name")

        # Isolate LSB and avoid weird python integer jank
        if out_bit != "x":
            out_bit &= 1

        out += str(out_bit)

    # Apply gate delay and put x (unknown) at the beginning
    out = ("x" * delay) + out[0:(length - delay)]

    # Convert back to dotted format
    out = to_dotted(out)

    return out

def wavedrom_sr_latch(s, r, delay=0, initial_value = "x"):
    """
    Emulates an SR latch with WaveDrom signals
    s (str): set signal in wavedrom format
    r (str): reset signal in wavedrom format
    delay (int): delay in ns (assumes the latch as a whole has a delay)
    initial_value (str): "x" for unknown by default, can also be "0" or "1"
    """

    length = len(s)

    # Check S and R don't go low at the same time (undefined behavior)
    # Note that having them START both low is fine, that just results
    # in unknown output (x)
    for i in range(1, length):
        if s[i] == "0" and r[i] == "0":
            raise Exception("S and R can't go low at the same time")

    # THEN convert to dotless form
    s = to_dotless(s)
    r = to_dotless(r)

    out = ""

    signal_value = initial_value

    # Process using the SR latch logic
    for i in range(length):

        # Look for set
        if s[i] == "1":
            signal_value = "1"
        # Look for reset
        if r[i] == "1":
            signal_value = "0"
        # Else don't change output value

        # If set and reset are high at the same time, it resets
        
        out += signal_value
    
    # Apply gate delay and put x (unknown) at the beginning
    out = ("x" * delay) + out[0:(length - delay)]

    # Convert back to dotted format
    out = to_dotted(out)

    return out

def wavedrom_d_latch(d, e, delay=0, initial_value = "x"):
    """
    Emulates a D latch with WaveDrom signals
    D (str): data signal in dotted format
    E (str): enable signal in dotted format
    delay (int): delay in ns (assumes the latch as a whole has a delay)
    initial_value (str): "x" for unknown by default, can also be "0" or "1"
    """

    length = len(d)

    # Make sure a transition doesn't occur while D goes low
    for i in range(1, length):
        if e[i] == "0" and (d[i] == "0" or d[i] == "1"):
            raise Exception("E can't go low at the same time as a transition")

    # THEN convert to dotless form
    d = to_dotless(d)
    e = to_dotless(e)

    out = ""

    signal_value = initial_value

    # Process using the D latch logic
    for i in range(length):

        # Take current d value if e is high
        if e[i] == "1":
            signal_value = d[i]
        # Else don't change output value
        
        out += signal_value
    
    # Apply gate delay and put x (unknown) at the beginning
    out = ("x" * delay) + out[0:(length - delay)]

    # Convert back to dotted format
    out = to_dotted(out)

    return out

def wavedrom_d_flip_flop(clk, d, en="", s="", r="", setup_time=0, hold_time=0, delay=0, initial_value="x"):
    """
    Emulates a rising edge DFF with WaveDrom signals
    d (str): data signal in dotted format
    clk (str): clock signal in dotted format
    en (str): Optional enable, constant 1 if left blank
    s (str): optional set
    r (str): optional reset
    setup_time (int): optional setup time
    hold_time (int): optional hold time
    delay (int): delay in ns (assumes the flop as a whole has a delay)
    initial_value (str): "x" for unknown by default, can also be "0" or "1"
    """

    length = len(d)

    d = to_dotless(d)

    # If enable is not specified, assume a constant 1
    en = to_dotless(en) if en else "1" * length

    # If S and R are not specified, assume constant 0
    s = to_dotless(s) if s else "0" * length
    r = to_dotless(r) if r else "0" * length

    # Keep clk dotted so that we have the transitions

    signal_value = initial_value
    out = ""

    # Preserve the initial value for the first bit of the output
    out += signal_value

    for i in range(1, length):
        # Only change the value on rising edge of the clock
        if clk[i] == "1" and en[i] == "1":

            # pass the value of D right before the rise through
            signal_value = d[i-1]

            # Force to 1 or 0 if set or reset
            # the set/reset has to be high BEFORE the rising edge
            if s[i-1] == "1":
                signal_value = "1"
            if r[i-1] == "1":
                signal_value = "0"

            # Look for setup and hold time violations
            if setup_time > 0 or hold_time > 0:
                
                # If i=8, setup_time is 3, and hold_time is 2
                # Left bound would be 5 and right 10
                left_bound = max(i-setup_time, 0)
                right_bound = min(i+hold_time, length-1)

                # Scanning from 5 to 9
                # 5 to 7 is the setup time window, and 8-9 is the hold time window
                all_1s = "1" * (right_bound - left_bound)
                all_0s = "0" * (right_bound - left_bound)
                if d[left_bound:right_bound] != all_1s and d[left_bound:right_bound] != all_0s:
                    # Force output to x if changes exist here
                    signal_value = "x"
        
        # Otherwise keep the current signal value

        out += signal_value

        # Apply gate delay and put unknown/initial value at the beginning
    out = (initial_value * delay) + out[0:(length - delay)]

    # Convert back to dotted format
    out = to_dotted(out)

    return out

def make_wavedrom_link(title, sig_names, gen_sigs, fill_sig_names, link_text = "WaveDrom Link", use_dotless = True):

    """
    Generates wavedrom related question or answer link in HTML

    Args:
        title (str): String to label timing diagram like "Question 2"
        sig_names (list): List of input signal names like ["a", "b"]
        gen_sigs (list): List of generated signals corresponding to sig_names 
        (in dotted format)
        fill_sig_names (list): List of signal names to hold space for
        students to complete -> ["a'","b'","ab'","F"]
        link_text (str): text for the link to appear as
        use_dotless (bool): whether to use dotless form (11100111) instead of dotted (1..0.1..)
    """

    # Base wavedrom link, change this if need be
    base_link = "https://dougsummerville.github.io/wavedrom"

    if use_dotless:
        gen_sigs = [to_dotless(sig) for sig in gen_sigs]

    title_html = title.replace(' ','%20')
    
    lines_url = []
    for sig_name, sig in zip(sig_names, gen_sigs):
        line = f"{{name: \"{sig_name}\", wave: \"{sig}\"}},"
        lines_url.append(line)
    for sig_name in fill_sig_names:
        line = f"{{name: \"{sig_name}\", wave: ''}},"
        lines_url.append(line)

    url_gen = urllib.parse.quote("".join(lines_url))
    
    link = f"{base_link}/editor.html?%7B%20head%3A%7Btext%3A%27{title_html}%27%7D%2C%0Asignal%3A%0A%5B%0A{url_gen}%5D%2C%0A%20%20foot%3A%7Btick%3A0%7D%0A%7D"

    # Convert to HTML link and make it open in new tab
    link_html = f"<a href=\"{link}\" target=\"_blank\">{link_text}</a>"

    return link_html

def to_alternate(link):

    """Converts Watson Wiki WaveDrom Link to GitHub Link"""

    link = link.replace("watsonwiki.binghamton.edu", "dougsummerville.github.io")
    link = link.replace("</a>", " (Alternate)</a>")

    return link


def make_wavedrom_image(title, sig_names, gen_sigs, fill_sig_names=[], out_filename="image.svg"):
    """
    Generates wavedrom image of specified signals
    Args:
        title (str): String to label timing diagram like "Question 2"
        sig_names (list): List of input signal names like ["a", "b"]
        gen_sigs (list): List of generated signals corresponding to sig_names
        fill_sig_names (list): List of signal names to hold space for
        students to complete -> ["a'","b'","ab'","F"]. Empty if not specified
        out_filename (str): SVG output file
    """

    gen_sigs = [to_dotted(sig) for sig in gen_sigs]

    title_line = f"head:{{text:'{title}'}},"

    lines = []
    for sig_name, sig in zip(sig_names, gen_sigs):
        # Force sharp edges by replacing 1 and 0 with h and l
        sig = sig.replace("1", "h")
        sig = sig.replace("0", "l")
        
        line = f"{{name: \"{sig_name}\", wave: \"{sig}\"}},"
        lines.append(line)
    for sig_name in fill_sig_names:
        line = f"{{name: \"{sig_name}\", wave: ''}},"
        lines.append(line)

    signal_code = " ".join(lines)

    code = '{' + title_line + ' signal: [ ' + signal_code + '],  foot:{"tick":0},}'

    img = wavedrom.render(code)
    img.saveas(out_filename)
    

def to_regex(name, signal):
    """
    name: name of output signal like "f"
    signal: output wavedrom signal like "0...1..0."
    """

    dotless = to_dotless(signal)

    # Escape the silly dots
    dotted = signal.replace(".", "\\.")

    # Super-ultra-mega-monster regex, shoutout to the man himself Doug for this one
    regex_ans = f"""(?i:name\\s*:\\s*['"]{name}['"]\\s*,\\s*wave\\s*:\\s*['"](?:{dotted}|{dotless})['"])"""
    return regex_ans

def make_random_buses(length = 20, width = 8, min_duration = 4, max_duration = 6):
    
    """
    Makes a sequence of random buses for wavedrom

    length: duration of the signal
    width: bus width in bits
    min_duration: minimum duration at which each bus remains unchanged
    max_duration: maximum duration at which each bus remains unchanged

    returns:
    wave: wave string like "2..3..2.3..."
    data: array corresponding to each string
    IN THAT ORDER!
    """

    data = []
    wave = ""

    # Progressing between different elements is just done by switching between 2 and 3
    wave_value = "2"

    # keep track of how many spots in the wave have been filled
    tag = 0

    # Make the wave signal and the data array
    while tag < length:
        num = b_format(random.randint(0, (1<<width - 1)), width)
        duration = random.randrange(min_duration, max_duration+1)

        # add number to the data array
        data.append(num)
        # add the index and the appropriate number of . to the wave
        wave += wave_value + ("." * (duration - 1))

        tag += duration

        wave_value = "3" if wave_value == "2" else "2"

    wave = wave[0:length]

    return wave, data

def make_random_timing_of_buses(buses, length, min_duration = 4, max_duration = 6):

    """
    Makes random wave and data signals given an array of buses

    buses: the list of buses
    length: duration of the signal
    min_duration: minimum duration at which each bus remains unchanged
    max_duration: maximum duration at which each bus remains unchanged

    returns:
    wave: wave string like "2..3..2.3..."
    data: array with each string
    IN THAT ORDER!
    """

    # List of stuff to sample from
    bus_pool = buses.copy()

    wave = ""
    data = []

    # Progressing between different elements is just done by switching between 2 and 3
    wave_value = "2"

    tag = 0

    while tag < length:
        
        duration = random.randrange(min_duration, max_duration+1)

        # If already sampled all possible buses, refill the list
        if bus_pool == []:
            bus_pool = buses.copy()
        
        # Remove a random element from the list
        bus = bus_pool.pop(random.randrange(len(bus_pool)))

        data.append(bus)

        # add the index and the appropriate number of . to the wave
        wave += wave_value + ("." * (duration - 1))

        wave_value = "3" if wave_value == "2" else "2"

        tag += duration

    wave = wave[0:length]

    return wave, data

def wavedrom_alu(A, B, opcodes, opcodes_sorted, operations):

    """
    Does ALU operation on wavedrom bus signals

    A, B: Tuples of (wave, data) of A and B buses
    opcodes: Tuple of (wave, data) of opcodes
    opcodes_sorted: sorted list of opcodes
    operations: list of operations corresponding to each sorted opcode like "0" or "A + B"

    """

    A_wave, A_data = A
    B_wave, B_data = B
    op_wave, op_data = opcodes

    # Remove "F = " and spaces from operations if needed
    operations = [o.replace(" ", "") for o in operations]
    operations = [(o.split("=")[1] if "=" in o else o) for o in operations]

    length = len(A_wave)
    width = len(A_data[0])

    # Indices corresponding to the data arrays
    A_index, B_index, op_index = -1, -1, -1

    F_value = ""
    wave_value = "2"

    wave = ""
    data = []

    for i in range(length):

        # Move on to next element in data array if on a new element
        if A_wave[i] != ".":
            A_index += 1
        if B_wave[i] != ".":
            B_index += 1
        if op_wave[i] != ".":
            op_index += 1
        
        # Unpack the numbers and evaluate each time
        A = to_decimal(A_data[A_index])
        B = to_decimal(B_data[B_index])
        opcode = op_data[op_index]
        operation = operations[opcodes_sorted.index(opcode)]
        F = eval(operation)
        F = b_format(F, width)

        # If the value of F changed, add a new data array element
        if F != F_value:
            wave += wave_value
            data.append(F)

            wave_value = "3" if wave_value == "2" else "2"
        else:
            wave += "."

        F_value = F

    return wave, data

def wavedrom_mfr(clk, Q_start, A, opcodes, opcodes_sorted, operations):

    """
    Does MFR operations on wavedrom bus signals

    clk: wavedrom clock signal from make_clock()
    Q_start: initial MFR value
    A: tuple of MFR input as (wave, data)
    opcodes: Tuple of (wave, data) of opcodes
    opcodes_sorted: sorted list of opcodes
    operations: list of operations corresponding to each sorted opcode like "0" or "Q + A"

    """

    A_wave, A_data = A
    op_wave, op_data = opcodes

    # Remove "Q <- " and spaces from operations if needed
    operations = [o.replace(" ", "") for o in operations]
    operations = [(o.split("<-")[1] if "<-" in o else o) for o in operations]

    length = len(A_wave)
    width = len(A_data[0])

    # Indices for values in the data arrays
    A_index, op_index = -1, -1

    wave_value = "2"

    wave = wave_value
    Q_value = Q_start
    Q = Q_start
    data = [Q_value]

    for i in range(1, length):

        # Move on to next element in data array if on a new element 
        if A_wave[i - 1] != ".":
            A_index += 1
        if op_wave[i - 1] != ".":
            op_index += 1
        
        A = to_decimal(A_data[A_index])
        opcode = op_data[op_index]

        operation = operations[opcodes_sorted.index(opcode)]

        # Every rising edge, update Q based on opcode and A value
        if clk[i] == "1":
            Q = to_decimal(Q)
            Q = eval(operation)
            Q = b_format(Q, width)

        if Q != Q_value:
            wave += wave_value
            data.append(Q)

            wave_value = "3" if wave_value == "2" else "2"
        else:
            wave += "."

        Q_value = Q

    return wave, data

def make_wavedrom_image_with_buses(title, sig_names, buses, out_filename="image.svg"):
    """
    Generates wavedrom image with buses
    Args:
        title (str): String to label timing diagram like "Question 2"
        sig_names (list): List of input signal names like ["a", "b"]
        buses: list of tuples of wave and data for buses
        out_filename (str): SVG output file
    """

    title_line = f"head:{{text:'{title}'}},"

    lines = []
    for sig_name, bus in zip(sig_names, buses):

        # If it's a tuple, it's a bus
        if type(bus) is tuple:
            
            # Separate tuple into string and array
            wave = bus[0]
            data = bus[1]
            # Make data into a proper string
            data = [f'"{s}",' for s in data]
            data = " ".join(data)
            
            line = f"{{name: \"{sig_name}\", wave: \"{wave}\", data: [{data}]}},"
            lines.append(line)

        # Otherwise it's just a plain signal, so handle it
        # like in make_wavedrom_image()
        else:
            sig = bus
            # Force sharp edges by replacing 1 and 0 with h and l
            sig = sig.replace("1", "h")
            sig = sig.replace("0", "l")
            
            line = f"{{name: \"{sig_name}\", wave: \"{sig}\"}},"
            lines.append(line)

    signal_code = " ".join(lines)

    code = '{' + title_line + ' signal: [ ' + signal_code + '],  foot:{"tick":0},}'

    img = wavedrom.render(code)
    img.saveas(out_filename)



    

