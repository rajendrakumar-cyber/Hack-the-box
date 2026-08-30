# False Witness - Cryptography Writeup

This document outlines the step-by-step methodology and cryptographic vulnerability analysis used to solve the **False Witness** challenge.

---

## 1. Vulnerability Analysis
The target server implements a signature/hashing verification oracle using a custom discrete logarithm setup.

* **Group Arithmetic**: The hashing function is defined as:
  $$H(x) = G^x \pmod P$$
  Where $P$ is a 256-bit prime:
  `P = 0xCD4A96D3B7FA7251A1BB765933FB676FCAE8C9026682E34F779122DFD66915BB`
* **Key bits oracle leakage**:
  The user is allowed to choose the generator $G$ ($1 < G < P$).
  The oracle behaves as follows for a requested bit offset $i$:
  - If `KEY_BITS[i] == 0`: Returns a random 256-bit number.
  - If `KEY_BITS[i] == 1`: Returns one of the two public key parameters $PK[i \bmod len(PK)][s]$.
    Where each public key parameter is computed as $H(s) = G^s \pmod P$.

---

## 2. Exploitation Concept: Backdoor Generator $G$
Since the client defines the generator $G$, we can choose $G$ to have a very small order modulo $P$.
By setting:
$$G = P - 1 \equiv -1 \pmod P$$

The hash output $H(s)$ is simplified:
$$H(s) = (-1)^s \pmod P = \begin{cases} 1 \pmod P & \text{if } s \text{ is even} \\ P - 1 \pmod P & \text{if } s \text{ is odd} \end{cases}$$

Thus:
* If `KEY_BITS[i] == 1`: The oracle is guaranteed to return either $1$ or $P - 1$.
* If `KEY_BITS[i] == 0`: The oracle returns a random 256-bit integer, which has a negligible probability ($\approx 2^{-255}$) of being $1$ or $P - 1$.

We can query the Oracle for all 256 indices $0 \le i < 256$ and check if the returned value is $1$ or $P - 1$ to reconstruct the entire 256-bit AES key.

---

## 3. Exploit Automation (`solve.py`)
We automated the exploit by querying all 256 bits, converting the recovered bits to bytes, and decrypting the flag ciphertext with AES-ECB:

```python
import sys
from pwn import *
from Crypto.Cipher import AES
from Crypto.Util.Padding import unpad

P = 0xCD4A96D3B7FA7251A1BB765933FB676FCAE8C9026682E34F779122DFD66915BB

def solve():
    io = remote('154.57.164.72', 30794)
    io.recvuntil(b"Here is something for you:\n")
    enc_flag = bytes.fromhex(io.recvline().strip().decode())
    
    G = P - 1
    io.sendlineafter(b"Before we start, give me the hashing generator: ", str(G).encode())
    
    key_bits = [0] * 256
    for i in range(256):
        io.sendlineafter(b"> ", b"1")
        io.sendlineafter(b"Enter offset: ", str(i).encode())
        io.recvuntil(b"Oracle result: ")
        res = int(io.recvline().strip().decode())
        
        if res == 1 or res == G:
            key_bits[i] = 1
        else:
            key_bits[i] = 0
            
    key_bytes = int("".join(map(str, key_bits)), 2).to_bytes(32, 'big')
    cipher = AES.new(key_bytes, AES.MODE_ECB)
    print("FLAG:", unpad(cipher.decrypt(enc_flag), 16).decode())
    io.close()

if __name__ == "__main__":
    solve()
```

---

## 4. Flag
**`HTB{___l34k1ng_b1ts_0n3_by_0n3___}`**
