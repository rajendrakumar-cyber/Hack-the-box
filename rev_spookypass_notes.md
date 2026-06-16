# SpookyPass Writeup

**Challenge Name:** SpookyPass
**Difficulty:** Very Easy
**Category:** Reversing

## Challenge Description
All the coolest ghosts in town are going to a Haunted Houseparty - can you prove you deserve to get in?

## Solution
The challenge provides a binary named `pass`.

1. **Running the binary:**
   ```bash
   ./pass
   ```
   The binary asks for a password.

2. **Analyzing the binary:**
   Using the `strings` command reveals the password stored in cleartext:
   ```bash
   strings pass
   ```
   Found string: `s3cr3t_p455_f0r_gh05t5_4nd_gh0ul5`

3. **Obtaining the Flag:**
   Entering the password into the binary:
   ```bash
   Welcome to the SPOOKIEST party of the year.
   Before we let you in, you'll need to give us the password: s3cr3t_p455_f0r_gh05t5_4nd_gh0ul5
   Welcome inside!
   HTB{un0bfu5c4t3d_5tr1ng5}
   ```

**Flag:** `HTB{un0bfu5c4t3d_5tr1ng5}`
