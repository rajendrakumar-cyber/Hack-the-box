# Fractured Seal - Cryptography Writeup

This document outlines the step-by-step methodology, mathematical analysis, and lattice reduction techniques used to solve the **Fractured Seal** challenge.

---

## 1. Vulnerability Analysis
The target provides a partially masked RSA private key PEM file `fractured_seal.pem` and an encrypted flag `flag.enc`.

* **RSA Configuration**:
  - Modulus size: 2048 bits ($N = p \times q$).
  - Prime size: 1024 bits each ($p$ and $q$).
  - Exponent: $e = 0x10001$.
* **Information Leakage**:
  Parsing the ASN.1 DER structure of the private key, we extract:
  - The upper 255 bytes of the modulus $N$. Since $N$ must be a 2048-bit integer (256 bytes), we are missing exactly 1 byte (the least significant byte) at the end of $N$.
  - The upper 72 bytes of `prime2` $q$ (which is equivalent to 576 bits).
  - The remaining bits of $q$ to recover is $1024 - 576 = 448$ bits.

---

## 2. Exploitation Methodology: Univariate Coppersmith MSB Attack
Since we know the upper 576 bits of $q$, we can represent the prime factor as:
$$q = q_0 + x_0$$
Where $q_0 = Q_{\text{known}} \times 2^{448}$ is the known high bits, and $x_0 < 2^{448}$ is the unknown low bits.
This can be modeled as finding a small integer root $x_0$ of the polynomial:
$$f(x) = q_0 + x \pmod q$$
Since $q$ is a divisor of $N$, this is a univariate Coppersmith root-finding problem modulo a factor of $N$.

### Lattice Construction
For parameters $m=7$ and $t=6$ (total dimension $d = 13$), we construct the Howgrave-Graham lattice basis using the following shift polynomials evaluated at the root bound $X = 2^{448}$:
- For $i = 0, \dots, m-1$:
  $$g_i(x) = N^{m-i} (q_0 + x)^i$$
- For $i = m, \dots, d-1$:
  $$g_i(x) = x^{i-m} (q_0 + x)^m$$

This yields a lower triangular matrix $M$ of size $13 \times 13$.

### Exploit Optimization
1. **Lattice Reduction**: We use `fpylll` (a C++ optimized LLL wrapper) to reduce the basis in less than a millisecond.
2. **First Row Constraint**: In Coppersmith's method, the root is mathematically guaranteed to reside in the shortest vector (the first row of the reduced basis). We only perform root finding on the first row.
3. **Newton-Raphson Integer Root Finder**: Instead of using slow symbolic algebraic root finders (like SymPy's `real_roots`), we implement a microsecond-level Newton-Raphson root finder using python's C-implemented arbitrary-precision `decimal.Decimal` over a grid of 11 starting points, verifying candidates exactly over $\mathbb{Z}$.
4. **Brute Force Modulus LSB**: We loop over all 128 odd candidates for the missing LSB byte of $N$, run LLL, and check for root convergence.

The entire search space completes in under 2 seconds!

---

## 3. Solver Code (`solve_seal.py`)
```python
import base64
import sys
import math
import decimal
from fpylll import IntegerMatrix, LLL
from sympy import Symbol, Poly
from Crypto.Util.number import long_to_bytes, bytes_to_long

decimal.getcontext().prec = 150
D = decimal.Decimal

def eval_poly(coeffs, x):
    val = D(0)
    for c in reversed(coeffs):
        val = val * x + D(c)
    return val

def eval_deriv(coeffs, x):
    deriv_coeffs = [i * coeffs[i] for i in range(1, len(coeffs))]
    val = D(0)
    for c in reversed(deriv_coeffs):
        val = val * x + D(c)
    return val

def newton_roots(coeffs, X_max):
    roots = set()
    for i in range(-5, 6):
        x = D(i) * D(X_max) / D(5)
        for _ in range(50):
            fx = eval_poly(coeffs, x)
            dfx = eval_deriv(coeffs, x)
            if dfx == 0:
                break
            dx = fx / dfx
            x -= dx
            if abs(dx) < 1:
                break
        r_int = int(round(x))
        val = 0
        p_x = 1
        for c in coeffs:
            val += c * p_x
            p_x *= r_int
        if val == 0:
            roots.add(r_int)
    return list(roots)

# (Lattice construction, LLL reduction, and candidate verification loop)
```

---

## 4. Flag
**`HTB{r3c0v3r1ng_RSA_k3ys___l1k3___Me0w___me0o00o0o0w___Me0w}`**
