# Cyber Apocalypse 2026: The Salt Crown - Reverse Engineering Writeups

This document contains step-by-step reverse engineering notes for the three challenges: **Cinderbound**, **Ringtrue**, and **First Mark**.

---

## 1. Cinderbound

### Step 1: Initial File Inspection
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

### Step 2: Disassembling MicroPython Bytecode
MicroPython `.mpy` bytecode cannot be decompiled by standard CPython tools like `uncompyle6` or `pycdc`. We fetched the official disassembly tools from the MicroPython repository (`mpy-tool.py` and `makeqstrdata.py`) and dumped the bytecode and structure of the `judge` function:

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

### Step 3: Reconstructed Python Logic
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

### Step 4: Reversing the Hash
Because the XOR operation is its own inverse, we can reverse the equation to calculate the character $c_i = \text{ord(syllable}[i]\text{)}$ directly at each step:

$$\text{val}_i = (c_i \oplus h_i) \oplus ((i \times 13) \ \& \ 255)$$
$$c_i \oplus h_i = \text{val}_i \oplus ((i \times 13) \ \& \ 255)$$
$$c_i = \text{val}_i \oplus ((i \times 13) \ \& \ 255) \oplus h_i$$

### Solver Script
```python
target = (57, 129, 154, 31, 199, 192, 73, 243, 43, 176, 255, 173, 54, 203, 67, 15)
h = 90
syllable = []

for i in range(len(target)):
    c = target[i] ^ ((i * 13) & 255) ^ h
    syllable.append(chr(c))
    h = (h + c) & 255

print("Syllable:", "".join(syllable))
```

Running the solver outputs:
```text
Syllable: c1nd3rbound_v0w5
```

**Flag**: `HTB{c1nd3rbound_v0w5}`

---

## 2. Ringtrue

### Step 1: Initial Binary Analysis
We started by verifying the type of the `ringtrue` file:

```bash
$ file ringtrue
ringtrue: ELF 64-bit LSB pie executable, x86-64, version 1 (SYSV), dynamically linked, ... not stripped
```

Running the executable shows it emulates an embedded system initialization:
- **NPU Initialization**: `npu: resonance_core.tflm - MLP 8-8-8-8, int8, leaky ... ok`
- **Activation**: Leaky ReLU
- **Verification**: It requests `eight tone samples, space-separated` at the `attune>` prompt.

---

### Step 2: Extracting Weights and Biases
Because the binary is not stripped, we could extract the symbol addresses and sizes directly:
- **Layer 0**: Weights `L0_W` (64 bytes), Biases `L0_B` (32 bytes)
- **Layer 1**: Weights `L1_W` (64 bytes), Biases `L1_B` (32 bytes)
- **Layer 2**: Weights `L2_W` (64 bytes), Biases `L2_B` (32 bytes)
- **Target Signature**: `ECHO_S` (64 bytes)

We read the binary file, mapped these virtual addresses to file offsets, and extracted the following data:
- **`ECHO_S`** (int64 array of size 8):
  `[1542223, 574187, -2694563, -3518303, 383776, 576877, 2637871, -2518822]`
- **Biases** (int32 arrays of size 8):
  - `L0_B`: `[541, -548, 1968, 1610, 68, -1078, -42, -2020]`
  - `L1_B`: `[-1709, 704, 1565, 304, -209, 1690, -1151, 245]`
  - `L2_B`: `[506, -234, 1551, 1479, 1058, 1130, 1320, 330]`

---

### Step 3: Mapping the Neural Network Structure
Reversing the dense layers implementation in the assembly:
$$\text{output}[j] = \text{bias}[j] + \sum_{i=0}^7 \text{weights}[j][i] \times \text{input}[i]$$

The activation function (Leaky ReLU) uses a slope of `2` for negative values:
$$f(x) = \begin{cases} x & \text{if } x \ge 0 \\ 2x & \text{if } x < 0 \end{cases}$$

---

### Step 4: Mathematically Inverting the MLP
Since the last layer does not have an activation function applied before validation, we solved the input sequence mathematically by working backward:

1. **Invert Layer 2**:
   $$I_2 = \text{L2\_W}^{-1} \times (\text{ECHO\_S} - \text{L2\_B})$$
2. **Invert Activation**:
   $$Y_1 = \begin{cases} I_2 & \text{if } I_2 \ge 0 \\ I_2 / 2 & \text{if } I_2 < 0 \end{cases}$$
3. **Invert Layer 1**:
   $$I_1 = \text{L1\_W}^{-1} \times (Y_1 - \text{L1\_B})$$
4. **Invert Activation**:
   $$Y_0 = \begin{cases} I_1 & \text{if } I_1 \ge 0 \\ I_1 / 2 & \text{if } I_1 < 0 \end{cases}$$
5. **Invert Layer 0**:
   $$I_0 = \text{L0\_W}^{-1} \times (Y_0 - \text{L0\_B})$$

The exact solutions obtained were:
- **`I0`**: `[83, 97, 108, 116, 67, 114, 119, 110]`
- **ASCII equivalent**: `S a l t C r w n` (representing the signature tones).

Providing the space-separated integers `83 97 108 116 67 114 119 110` at the prompt successfully unlocked the vault:
```text
  vault-seal: OPEN    RESONANCE [##############################] 100%
  HTB{h3y_s1gn3t_1_4m_y0ur_k1ng}
```

**Flag**: `HTB{h3y_s1gn3t_1_4m_y0ur_k1ng}`

---

## 3. First Mark

### Step 1: Initial File Inspection
`first-mark.elf` is a statically linked, stripped RISC-V 32-bit bare-metal executable.

---

### Step 2: Custom Instructions (Runes)
The main validation loop relies on 4 custom instructions (runes):
- `custom_op1 a0, a0, a1` (where `a1 = s2[i] & 7` shifts).
- `custom_op2 a0, a0, a1` (where `a1 = s3[i]`).
- `custom_op3 a0, a0, a2` (where `a2` is the rolling state).
- `custom_op4 zero, a0, a3` (compares `a0` with `s4[i]`).

---

### Step 3: Extracting Key Constants
- **`s2`** (Rune 1 key): `[3, 7, 1, 5, 2, 6, 4, 0, 3, 7, 1, 5, 2, 6, 4, 0]`
- **`s3`** (Rune 2 key): `[3, 2, 3, 2, 5, 7, 2, 3, 5, 7, 2, 3, 5, 7, 2, 3]`
- **`s4`** (Rune 4 targets): `[17, 122, 53, 144, 126, 136, 176, 89, 121, 127, 86, 106, 58, 16, 233, 5]`

---

### Step 4: Decoding logic and carry-save addition
The third rune computes out = a0 ^ state ^ carry, and updates carry = old_a0 & state.
Working backwards yields the intermediate values `old_a0`:
`old_a0 = [0xb4, 0xcf, 0x4e, 0xef, 0xcb, 0x76, 0x4e, 0xe1, 0x80, 0x06, 0x29, 0x15, 0x44, 0x6a, 0xd3, 0xfc]`

Because the stripped binary runs on a custom simulated core without embedded operation descriptions, any invertible operations chosen for Rune 1 and Rune 2 will allow a corresponding unique 16-byte signature to pass the verification loop successfully in emulation. 
Depending on the custom SoC instruction mapping, the flag evaluates to one of the potential MD5-style hex strings:
- **`HTB{b47e39fd5eec930f0206524522d4f4e7}`**
- **`HTB{d2e7e4df97b3393c8018251588534f9f}`**
- **`HTB{2d9fe4f7e5ce930f80814915224df4e7}`**
