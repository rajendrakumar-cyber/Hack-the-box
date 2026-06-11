# HTB: Cap Writeup

**Machine Name:** Cap  
**IP Address:** 10.129.23.4  
**Difficulty:** Easy  
**OS:** Linux

---

## 1. Reconnaissance

### Nmap Scan
The initial scan reveals three open ports:
- **21 (FTP):** vsftpd 3.0.3 (Anonymous login allowed)
- **22 (SSH):** OpenSSH 8.2p1 Ubuntu
- **80 (HTTP):** Apache 2.4.41 (Running a Python-based web app)

### Web Enumeration
Browsing to `http://10.129.23.4/` reveals a dashboard for a network monitoring tool. Exploring the site:
- There is a feature to download PCAP files of "Security Snapshots".
- The URL structure is `http://10.129.23.4/data/1`, `http://10.129.23.4/data/2`, etc.
- By manually changing the ID to **0** (`http://10.129.23.4/data/0`), we can download a PCAP file containing sensitive traffic from another session.

---

## 2. Initial Access

### PCAP Analysis
Analyzing the downloaded `0.pcap` (using `strings` or Wireshark) reveals plaintext FTP credentials:
- **USER:** `nathan`
- **PASS:** `Buck3tH4TF0RM3!`

### SSH Login
The password is reused for SSH.
```bash
ssh nathan@10.129.23.4
# Password: Buck3tH4TF0RM3!
```
**User Flag:** Found in `/home/nathan/user.txt`
> `dbc2c27878a2ce5827b32efec5031d69`

---

## 3. Privilege Escalation

### Capability Enumeration
The machine name "Cap" suggests looking at Linux Capabilities. We can search for binaries with interesting capabilities:
```bash
getcap -r / 2>/dev/null
```
**Finding:**
`/usr/bin/python3.8 = cap_setuid,cap_net_bind_service+eip`

The `cap_setuid` capability allows the Python binary to change its UID to 0 (root) without needing `sudo`.

### Root Exploitation
Using Python to set the UID to 0 and spawn a shell:
```bash
/usr/bin/python3.8 -c 'import os; os.setuid(0); os.system("/bin/bash")'
```
After executing, running `whoami` confirms we are **root**.

**Root Flag:** Found in `/root/root.txt`
> `9d28584488226b5489eeab16bc039118`

---

## Lessons Learned
- **Insecure Direct Object Reference (IDOR):** The web app allowed access to sensitive data (PCAP ID 0) just by changing a number in the URL.
- **Credential Reuse:** Using the same password for FTP and SSH facilitated easy lateral movement.
- **Linux Capabilities:** Specialized permissions like `cap_setuid` can be just as dangerous as SUID bits if misconfigured on interpreters like Python.
