# Cinderbound - Reverse Engineering Notes

These notes outline the step-by-step reverse engineering process for the **Cinderbound** challenge, from file inspection through bytecode disassembly to the final mathematical solving.

---

## Step 1: Initial File Inspection
We started by checking the type of the provided file `cinderbound.mpy`:

```bash
$ file cinderbound.mpy
cinderbound.mpy: data
```

Examining the file header using a hex dump:
```hex
00000000  4d 06 00 1f 08 01 18 6a  75 64 67 65 5f 73 72 63  |M......judge_src|
```
- `4d` ('M') is the magic prefix indicating a MicroPython compiled file.
- `06` indicates MicroPython v6 ABI bytecode (used in MicroPython v1.19 through v1.22+).

---

## Step 2: Disassembling MicroPython Bytecode
MicroPython `.mpy` bytecode cannot be decompiled by standard CPython tools like `uncompyle6` or `pycdc`. We fetched the official disassembly tools from the MicroPython repository:

1. **`mpy-tool.py`**: The low-level inspection utility.
2. **`makeqstrdata.py`**: A helper script required to parse the interned strings (Qstrs).

Running `mpy-tool.py -d cinderbound.mpy` dumped the raw bytecode and structure of the `judge` function:

```python
source_file: judge_src.py
qstr_table[8]:
    judge_src.py
    <module>
    judge
    append
    syllable
    len
    ord
    list
obj_table: [(57, 129, 154, 31, 199, 192, 73, 243, 43, 176, 255, 173, 54, 203, 67, 15)]
```

---

## Step 3: Bytecode Disassembly & Mapping
Below is the trace of the `judge` function bytecode, mapped line-by-line to Python instructions.

### Variable Bindings
- `FAST[0]`: `syllable` (input argument)
- `FAST[1]`: `target` tuple `(57, 129, 154, ...)`
- `FAST[2]`: `h` (rolling hash state, initially `90`)
- `FAST[3]`: `out_list` (output builder list, initially `[]`)
- `FAST[4]`: `i` (loop index)
- `FAST[5]`: `val` (temporary value)

### Bytecode Stream Analysis
```assembly
# Setup targets and variables
23:00       LOAD_CONST_OBJ 0      # Pushes target tuple
c1          STORE_FAST 1          # target = tuple
22:80:5a    LOAD_CONST_SMALL_INT  # Pushes 90
c2          STORE_FAST 2          # h = 90
2b:00       BUILD_LIST 0          # Pushes []
c3          STORE_FAST 3          # out_list = []

# Loop Initialization
12:05       LOAD_GLOBAL len
b0          LOAD_FAST 0           # syllable
34:01       CALL_FUNCTION 1       # len(syllable)
80          LOAD_CONST_SMALL_INT  # 0
42:6b       JUMP 43               # Jump to condition check

# Loop Body (Offset 57)
57          DUP_TOP
c4          STORE_FAST 4          # i = current index
12:06       LOAD_GLOBAL ord
b0          LOAD_FAST 0
b4          LOAD_FAST 4
55          LOAD_SUBSCR           # syllable[i]
34:01       CALL_FUNCTION 1       # ord(syllable[i])
b2          LOAD_FAST 2           # h
ee          BINARY_OP 23 __xor__  # ord(syllable[i]) ^ h
b4          LOAD_FAST 4           # i
8d          LOAD_CONST_SMALL_INT  # 13
f4          BINARY_OP 29 __mul__  # i * 13
22:81:7f    LOAD_CONST_SMALL_INT  # 255
ef          BINARY_OP 24 __and__  # (i * 13) & 255
ee          BINARY_OP 23 __xor__  # (ord(syllable[i]) ^ h) ^ ((i * 13) & 255)
c5          STORE_FAST 5          # val = result

# Hash Update
b2          LOAD_FAST 2           # h
12:06       LOAD_GLOBAL ord
b0          LOAD_FAST 0
b4          LOAD_FAST 4
55          LOAD_SUBSCR           # syllable[i]
34:01       CALL_FUNCTION 1       # ord(syllable[i])
f2          BINARY_OP 27 __add__  # h + ord(syllable[i])
22:81:7f    LOAD_CONST_SMALL_INT  # 255
ef          BINARY_OP 24 __and__  # (h + ord(syllable[i])) & 255
c2          STORE_FAST 2          # h = new hash state

# Append to List
b3          LOAD_FAST 3           # out_list
14:03       LOAD_METHOD append
b5          LOAD_FAST 5           # val
36:01       CALL_METHOD 1
59          POP_TOP

# Increment loop counter
81          LOAD_CONST_SMALL_INT  # 1
e5          BINARY_OP 14 __iadd__  # i += 1

# Loop Condition Check
58          DUP_TOP_TWO
5a          ROT_TWO
d7          BINARY_OP 0 __lt__    # i < len(syllable)
43:10       POP_JUMP_IF_TRUE -48  # Jump back to Offset 57 if True

# Return evaluation
59          POP_TOP
59          POP_TOP
b3          LOAD_FAST 3
12:07       LOAD_GLOBAL list
b1          LOAD_FAST 1
34:01       CALL_FUNCTION 1
d9          BINARY_OP 2 __eq__    # return out_list == list(target)
63          RETURN_VALUE
```

---

## Step 4: Reconstructed Python Logic
Based on the bytecode layout, the python equivalent of the `judge` function is:

```python
def judge(syllable):
    target = (57, 129, 154, 31, 199, 192, 73, 243, 43, 176, 255, 173, 54, 203, 67, 15)
    h = 90
    out_list = []
    
    for i in range(len(syllable)):
        val = (ord(syllable[i]) ^ h) ^ ((i * 13) & 255)
        h = (h + ord(syllable[i])) & 255
        out_list.append(val)
        
    return out_list == list(target)
```

---

## Step 5: Solving / Reversing the Hash
Because the XOR operation is its own inverse, we can reverse the equation to calculate the character $c_i = \text{ord(syllable}[i]\text{)}$ directly at each step:

$$\text{val}_i = (c_i \oplus h_i) \oplus ((i \times 13) \ \& \ 255)$$
$$c_i \oplus h_i = \text{val}_i \oplus ((i \times 13) \ \& \ 255)$$
$$c_i = \text{val}_i \oplus ((i \times 13) \ \& \ 255) \oplus h_i$$

### Solver Script
We write a python solver script using this mathematical inversion:

```python
target = (57, 129, 154, 31, 199, 192, 73, 243, 43, 176, 255, 173, 54, 203, 67, 15)
h = 90
syllable = []

for i in range(len(target)):
    # Reversing XOR to get character value
    c = target[i] ^ ((i * 13) & 255) ^ h
    syllable.append(chr(c))
    
    # Keep track of rolling hash update
    h = (h + c) & 255

print("Syllable:", "".join(syllable))
```

Running the solver outputs:
```bash
Syllable: c1nd3rbound_v0w5
```

---

## Step 6: Flag
Wrapping the decoded string in the standard `HTB` flag wrapper:
**`HTB{c1nd3rbound_v0w5}`**
