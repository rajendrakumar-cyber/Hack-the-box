# Manual Exploit Guide: Guess Password (Easy)

This guide documents the step-by-step procedure to manually solve the Google CTF "Guess Password Easy" challenge using standard command-line tools without writing script code.

---

## The Concept

The program uses `srand(time(0))` to seed a weak Pseudorandom Number Generator (PRNG). 
1. Since the seed is Unix time in seconds, we can generate a lookup database of passwords for seeds around the current time.
2. The server leaks the first 5 characters of the password in the prompt.
3. We search our database for that 5-character prefix, find the exact matching seed, and retrieve the full password.
4. We submit the full password to instantly get the flag.

---

## Step-by-Step Manual Solve

### Step 1: Pre-generate Passwords
Compile and run the seed generator to create a database of candidate passwords around your current system time:
```bash
g++ main.cpp -o seed_gen
./seed_gen
```
This generates a local text database named `output.txt` containing possible passwords.

### Step 2: Establish Server Connection
In one terminal window, connect to the challenge server:
```bash
nc guess-password-easy.2025-bq.ctfcompetition.com 1337
```
**Example Server Output:**
```text
== proof-of-work: disabled ==
Password is xpjsu...............
Your guess:
```

### Step 3: Lookup Password
In a second terminal window, grep for the leaked 5-character prefix (`xpjsu`) in the generated `output.txt` file:
```bash
grep "Password 1 is: xpjsu" output.txt
```
**Example Search Result:**
```text
Seed 14: 1787244024 - Password 1 is: xpjsuretekbeexlsxgjv
```

### Step 4: Submit & Capture Flag
Return to your first terminal window and submit the full password (`xpjsuretekbeexlsxgjv`):
```text
Your guess: xpjsuretekbeexlsxgjv
CTF{Did_y0u_h4v3_4_gr347_7im3_l00king_f0r_7h3_s33d?}
```
You successfully solve the challenge on the first try!
