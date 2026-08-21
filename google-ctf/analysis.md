# Vulnerability Analysis: Guess Password (Easy)

This document provides a detailed security analysis of the `guess_password_easy.c` code. It outlines **two distinct vulnerabilities** present in the implementation, explains how to exploit them manually and programmatically, and covers the core concepts behind them.

---

## 1. Code Overview & Identified Vulnerabilities

Looking at [`guess_password_easy.c`](file:///home/white/white/Music/google-ctf/guess_password_easy.c), the program does the following in an infinite loop:
1. Generates a random 20-character password using lowercase English letters.
2. Leaks the first 5 characters of the password to the user.
3. Prompts the user for a guess.
4. Computes the SHA-256 hashes of both the server password and the user's guess.
5. Compares the two hashes using `strncmp` up to `SHA256_DIGEST_LENGTH` (32 bytes).
6. If the hashes match, it prints the flag and exits.

There are two major vulnerabilities in this design:

### Vulnerability A: `strncmp` Null-Byte Truncation (Cryptographic Bypass)
* **Location:** [guess_password_easy.c:L40](file:///home/white/white/Music/google-ctf/guess_password_easy.c#L40)
* **The Code:** 
  ```cpp
  if (strncmp(serverPasswordHash, userPasswordHash, SHA256_DIGEST_LENGTH) == 0)
  ```
* **The Issue:** `strncmp` is designed for comparing **null-terminated C-style strings**, not raw binary buffers. It stops comparison as soon as it encounters a null byte (`0x00`) in either buffer. If the first byte of both hashes is `0x00`, `strncmp` sees a null byte at index `0` and immediately returns `0` (success), ignoring the remaining 31 bytes of the hashes.

### Vulnerability B: Weak Pseudorandom Number Generator (PRNG Prediction)
* **Location:** [guess_password_easy.c:L24](file:///home/white/white/Music/google-ctf/guess_password_easy.c#L24)
* **The Code:** 
  ```cpp
  srand(time(0));
  ```
* **The Issue:** The standard library `rand()` function is a pseudo-random number generator, meaning its output is fully deterministic if the seed is known. Seeding it with the current Unix time (`time(0)`) makes the seed highly predictable. Combined with the leak of the first 5 characters of each password, an attacker can synchronize their local PRNG and predict the rest of the password.

---

## 2. How to Solve It Manually & Remotely

### Method 1: The Null-Byte/`strncmp` Bypass (The Crypto Exploit)
Since we want both the server's hash and our hash to start with a null byte (`0x00`), we can pre-calculate a password that hashes to a value starting with `0x00`, and submit it repeatedly.

#### Step 1: Find a password that hashes to a null-byte prefix
We can run a simple Python script to find a string that yields a SHA-256 hash starting with a null byte (`0x00`):
```python
import hashlib
for i in range(1000):
    password = str(i)
    hash_bytes = hashlib.sha256(password.encode()).digest()
    if hash_bytes[0] == 0:
        print(f"Password: '{password}' -> Hash starts with 0x00")
        break
```
For example, the string `"286"` hashes to `00328ce5...`, which starts with a null byte (`00`).

#### Step 2: Spam the server with this password
1. Connect to the server.
2. Keep submitting `"286"` as your guess.
3. For each iteration, the server generates a new random password. Since the hash bytes are pseudorandom, the server password's hash has a $1/256$ probability of starting with `0x00`.
4. After approximately 256 attempts (on average), the server password's hash will start with `0x00`.
5. At that point, `strncmp` compares your hash (`00...`) and the server's hash (`00...`). It hits the null byte at the very beginning of both, stops comparison, returns `0`, and grants you the flag.

---

### Method 2: PRNG Seed Synchronization (The Prediction Exploit)
By using the 5-character leak and the fact that `srand(time(0))` is used, we can find the seed, predict the full password for the next loop iteration, and solve it instantly on the second try.

The automated remote solution script **[python.py](file:///home/white/white/Music/google-ctf/python.py)** does this:
1. Connects to `guess-password-easy.2025-bq.ctfcompetition.com:1337`.
2. Reads the initial connection block using `recv_until(s, "Your guess: ")` to handle TCP buffering safely.
3. Extracts the 5-character hint.
4. Performs a brute-force seed calculation over a range of $\pm 2$ hours (`range(-7200, 7200)`) around the current epoch timestamp using `ctypes` loading standard `libc.so.6`.
5. Locates the correct seed and predicts the subsequent password.
6. Submits the predicted password and retrieves the flag.

#### Captured Flag:
```text
CTF{Did_y0u_h4v3_4_gr347_7im3_l00king_f0r_7h3_s33d?}
```

---

## 3. Explanation of Core Concepts

### Concept A: C-Style String Comparisons vs. Binary Comparisons
In C/C++, strings and raw binary data are handled differently:

* **Strings (Null-Terminated):** In C, strings are sequences of characters ending with a null terminator (`'\0'` or `0x00`). Functions like `strcmp` and `strncmp` read characters sequentially until they reach either the maximum length (`n`) or a `0x00` byte, which signals the end of the string.
* **Binary Buffers:** Cryptographic digests (like SHA-256) are raw binary arrays of a fixed size. They are **not** null-terminated, and any byte within the digest—including the first one—can naturally be `0x00`.

Using string comparison functions like `strncmp` on cryptographic digests leads to **Null-Byte Injection / Truncation vulnerabilities**. 

> [!WARNING]
> To safely compare cryptographic hashes or binary buffers, you must use **`memcmp`** (which compares a strict number of bytes regardless of null terminators) or a constant-time memory comparison function to prevent timing attacks.
> 
> ```cpp
> // Secure comparison of binary hashes:
> if (memcmp(serverPasswordHash, userPasswordHash, SHA256_DIGEST_LENGTH) == 0) { ... }
> ```

---

### Concept B: Deterministic PRNGs and predictable seeds
A Pseudorandom Number Generator (PRNG) like `rand()` is not truly random; it uses a mathematical formula (such as a Linear Congruential Generator) to generate a sequence of numbers that *appear* random. 

* The sequence is completely determined by the initial value, called the **seed**.
* If two instances of a program are seeded with the same value via `srand(seed)`, they will produce the exact same sequence of numbers.
* Seeding with `time(0)` (current Unix time in seconds) is a common mistake. Since Unix time is public and easily guessable, anyone can determine the seed if they know approximately when the program started.

> [!IMPORTANT]
> For security-sensitive applications (such as password or token generation), you must use a **Cryptographically Secure Pseudorandom Number Generator (CSPRNG)**. On Linux, this is typically done by reading from `/dev/urandom` or using system APIs like `getrandom()`.
