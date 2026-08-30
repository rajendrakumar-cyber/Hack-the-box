# Cryptography Notes: Byte-Level Affine Cipher

These notes explain the concepts behind the custom Affine Cipher challenge implemented in `chall.py`.

---

## 1. The Affine Cipher
An **Affine Cipher** is a monoalphabetic substitution cipher where each character's integer value is mapped to another integer using a linear mathematical function.

*   **Encryption Formula:**
    $$c = (a \cdot m + b) \bmod N$$
    In this challenge:
    - $a = 123$ (multiplier / scale factor)
    - $b = 18$ (offset / shift)
    - $N = 256$ (the modulus, representing all possible byte values)

*   **Decryption Formula:**
    To reverse the encryption function and solve for $m$:
    $$c \equiv a \cdot m + b \pmod N$$
    $$c - b \equiv a \cdot m \pmod N$$
    $$m \equiv a^{-1} \cdot (c - b) \pmod N$$
    where $a^{-1}$ is the **modular multiplicative inverse** of $a$ modulo $N$.

---

## 2. Byte-Level Modular Arithmetic (Modulo 256)
Computers store data in bytes. A single byte consists of 8 bits, meaning it can represent $2^8 = 256$ different integer values (ranging from `0` to `255`).

When performing mathematical operations on bytes, we work **modulo 256** (represented as `% 256` in code). This means all values wrap around:
*   $258 \bmod 256 = 2$
*   $-5 \bmod 256 = 251$

---

## 3. The Modular Multiplicative Inverse ($a^{-1}$)
In normal algebra, you divide to isolate variables. In modular arithmetic, division is not allowed because all values must remain integers. Instead of dividing by $a$, we multiply by its **modular multiplicative inverse**, written as $a^{-1}$.

The inverse $a^{-1}$ is an integer $x$ such that:
$$(a \cdot x) \bmod N = 1$$

This inverse only exists if $\gcd(a, N) = 1$ (they are coprime). Since $256$ is only divisible by $2$ and $123$ is odd, they are coprime.

### How to Calculate the Inverse on Paper (Extended Euclidean Algorithm)
To solve $(123 \cdot x) \bmod 256 = 1$:

1.  **Division steps (Euclidean Algorithm):**
    $$256 = 2 \cdot 123 + 10$$
    $$123 = 12 \cdot 10 + 3$$
    $$10 = 3 \cdot 3 + 1$$

2.  **Back-substitution:**
    $$1 = 10 - 3 \cdot 3$$
    Substitute $3 = 123 - 12 \cdot 10$:
    $$1 = 10 - 3 \cdot (123 - 12 \cdot 10) = 37 \cdot 10 - 3 \cdot 123$$
    Substitute $10 = 256 - 2 \cdot 123$:
    $$1 = 37 \cdot (256 - 2 \cdot 123) - 3 \cdot 123 = 37 \cdot 256 - 77 \cdot 123$$

3.  **Modulo reduction:**
    $$-77 \cdot 123 \equiv 1 \pmod{256}$$
    Add $256$ to get a positive remainder:
    $$-77 + 256 = 179$$

So, the modular inverse $123^{-1} \equiv 179 \pmod{256}$. Multiplying by $179$ is equivalent to dividing by $123$ modulo $256$.

---

## 4. Handling Negative Remainders in Code
If the ciphertext byte $c$ is smaller than 18 (e.g., `0a` is $10$ in decimal), we get a negative result:
$$10 - 18 = -8$$

*   **In Python / Perl:** Modulo natively wraps negative values correctly, so `(-8 * 179) % 256` gives `104` (ASCII character `'h'`).
*   **In C / Bash / Awk:** The `%` operator computes the remainder rather than the mathematical modulo. So, `-1432 % 256` results in `-152`. To fix this, you must add $256$ to wrap it back into a positive index:
    $$(((\text{value} \bmod 256) + 256) \bmod 256)$$
