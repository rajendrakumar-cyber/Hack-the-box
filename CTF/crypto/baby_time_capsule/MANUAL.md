# Manual Solve Guide - Baby Time Capsule

This guide outlines how to solve the challenge manually using a Python interactive shell and standard terminal tools.

## Prerequisites
Ensure you have `pycryptodome` installed to decode the recovered integer into the flag string:
```bash
pip install pycryptodome
```

---

## Step 1: Gather 5 Ciphertexts and Moduli
Because the exponent $e = 5$, you need at least **5 independent ciphertexts** to perform Håstad's Broadcast Attack.

1. Connect to the challenge instance using `netcat`:
   ```bash
   nc 154.57.164.67 31247
   ```
2. Type `y` and press Enter **5 times** to request 5 time capsules.
3. Save the 5 JSON responses. Each response contains:
   - `time_capsule` (the ciphertext in hex)
   - `pubkey` (a list containing the modulus $N$ in hex, and the exponent $e = 5$ in hex)

---

## Step 2: Open Python and Solve
Start your Python interpreter:
```bash
python3
```

Paste the following script template, replacing the placeholder strings with the hex values you gathered from the server:

```python
from Crypto.Util.number import long_to_bytes

# 1. Input the values you gathered (replace with your hex values)
c_hex = [
    "CIPHERTEXT_1_HEX",
    "CIPHERTEXT_2_HEX",
    "CIPHERTEXT_3_HEX",
    "CIPHERTEXT_4_HEX",
    "CIPHERTEXT_5_HEX"
]

n_hex = [
    "MODULUS_1_HEX",
    "MODULUS_2_HEX",
    "MODULUS_3_HEX",
    "MODULUS_4_HEX",
    "MODULUS_5_HEX"
]

# Convert hex to integers
c = [int(x, 16) for x in c_hex]
n = [int(x, 16) for x in n_hex]

# 2. Chinese Remainder Theorem (CRT) calculation
def solve_crt(remainders, moduli):
    total_modulus = 1
    for m in moduli:
        total_modulus *= m
    
    result = 0
    for r, m in zip(remainders, moduli):
        M = total_modulus // m
        y = pow(M, -1, m)
        result += r * M * y
    return result % total_modulus

c_combined = solve_crt(c, n)

# 3. Calculate the integer 5th root using binary search
def nth_root(val, k):
    low = 0
    high = val
    while low <= high:
        mid = (low + high) // 2
        mid_k = mid ** k
        if mid_k == val:
            return mid
        elif mid_k < val:
            low = mid + 1
        else:
            high = mid - 1
    return high

m = nth_root(c_combined, 5)

# 4. Print the flag
print(long_to_bytes(m).decode())
```

---

## Why this works (The Math)
Since the flag is encrypted using the same exponent $e = 5$ under different moduli $N_i$:
$$C_i \equiv M^5 \pmod{N_i}$$

Using the Chinese Remainder Theorem, we can construct a combined ciphertext $C_{\text{combined}}$ such that:
$$C_{\text{combined}} \equiv M^5 \pmod{N_1 N_2 N_3 N_4 N_5}$$

Because the message $M$ is smaller than each modulus $N_i$, the value $M^5$ is mathematically strictly less than the product $N_1 N_2 N_3 N_4 N_5$. 

This means that:
$$C_{\text{combined}} = M^5$$

without any modular reduction having occurred. Hence, taking the normal integer 5th root of $C_{\text{combined}}$ yields the exact flag.
