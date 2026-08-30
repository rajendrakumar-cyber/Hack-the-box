# Ringtrue - Reverse Engineering Notes

These notes document the step-by-step reverse engineering process for the **Ringtrue** challenge, including analyzing the custom MLP neural network architecture and using matrix inversion to retrieve the input tones.

---

## Step 1: Initial Binary Analysis
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

## Step 2: Extracting Weights and Biases
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

## Step 3: Mapping the Neural Network Structure
Reversing the `dense` function in the assembly (`objdump -d -M intel ringtrue`):
```assembly
0000000000001309 <dense>:
...
    131b:	movsx  r8,BYTE PTR [r10+rax*1]
    1320:	imul   r8,QWORD PTR [rdx+rax*8]
    1325:	add    r9,r8
...
```
This shows the network uses standard matrix multiplication with integer scaling:
$$\text{output}[j] = \text{bias}[j] + \sum_{i=0}^7 \text{weights}[j][i] \times \text{input}[i]$$

The activation function (Leaky ReLU) uses a slope of `2` for negative values:
```assembly
    1ad0:	lea    rcx,[rax+rax*1]   # rcx = rax * 2
    1ad4:	test   rax,rax
    1ad7:	cmovs  rax,rcx           # if rax < 0, rax = rax * 2
```

Thus:
$$f(x) = \begin{cases} x & \text{if } x \ge 0 \\ 2x & \text{if } x < 0 \end{cases}$$

---

## Step 4: Mathematically Inverting the MLP
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

We wrote a NumPy solver script to compute these matrices. The exact solutions obtained were:
- **`I0`**: `[83, 97, 108, 116, 67, 114, 119, 110]`
- **ASCII equivalent**: `S a l t C r w n` (representing the signature tones).

---

## Step 5: attune & Flag retrieval
Providing the space-separated integers `83 97 108 116 67 114 119 110` at the prompt successfully unlocked the vault:

```text
  vault-seal: OPEN    RESONANCE [##############################] 100%

  +-- ash-vault - sealed vow ---------------------------------+
  |  HTB{h3y_s1gn3t_1_4m_y0ur_k1ng} 
```

**Flag**: `HTB{h3y_s1gn3t_1_4m_y0ur_k1ng}`
