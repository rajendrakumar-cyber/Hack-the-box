import socket
import time
import ctypes
import sys

# Load the standard C library for Linux PRNG emulation
try:
    libc = ctypes.CDLL("libc.so.6")
except OSError:
    try:
        libc = ctypes.CDLL(None)
    except Exception as e:
        print(f"[-] Error loading C library: {e}")
        print("[-] Ensure you are running this on a Linux system with standard glibc.")
        sys.exit(1)

# Ensure required symbols exist
try:
    _ = libc.rand
    _ = libc.srand
except AttributeError as e:
    print(f"[-] Standard C library functions not found: {e}")
    sys.exit(1)

HOST = "guess-password-easy.2025-bq.ctfcompetition.com"
PORT = 1337

def recv_until(s, suffix):
    """Helper to read from the socket until the suffix is received."""
    res = ""
    while not res.endswith(suffix):
        try:
            chunk = s.recv(1).decode()
        except socket.error as e:
            print(f"\n[-] Socket read error: {e}")
            break
        if not chunk:
            break
        res += chunk
    return res

def generate_password():
    """Replicates the server's 20-character password logic."""
    res = ""
    for _ in range(20):
        res += chr(ord('a') + (libc.rand() % 26))
    return res

def pwn():
    # 1. Establish initial connection
    print(f"[*] Connecting to {HOST}:{PORT}...")
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(10) # 10-second timeout for network operations
        s.connect((HOST, PORT))
    except Exception as e:
        print(f"[-] Connection failed: {e}")
        return
    
    # Snapshot the approximate current epoch time immediately on contact
    client_time = int(time.time())
    
    # 2. Read the server's welcome banner and hint
    data = recv_until(s, "Your guess: ")
    print(f"[Server Output]:\n{data}")
    
    # Extract the 5-character prefix (e.g., from "Password is ftbrh......")
    if "Password is " in data:
        hint = data.split("Password is ")[1][:5]
        print(f"[*] Extracted 5-char hint: '{hint}'")
    else:
        print("[-] Failed to parse password hint from server output.")
        s.close()
        return

    # 3. Synchronize Seed locally
    # Check a very wide window of 7200 seconds (2 hours) around client connection time
    # to account for any server-client clock differences.
    search_range = 7200
    print(f"[*] Brute-forcing timestamp (range: ±{search_range} seconds)...")
    matched_seed = None
    
    start_search = time.time()
    for offset in range(-search_range, search_range):
        test_seed = client_time + offset
        libc.srand(test_seed)
        
        # Check if this seed generates Password 1 matching our hint
        pass_1 = generate_password()
        if pass_1.startswith(hint):
            matched_seed = test_seed
            print(f"[+] Match found in {time.time() - start_search:.3f}s!")
            print(f"[+] Correct Server Seed: {matched_seed}")
            print(f"[+] Verified Password 1: {pass_1}")
            
            # The server loop automatically generates Password 2 for the next prompt
            pass_2 = generate_password()
            print(f"[+] Predicted Password 2: {pass_2}")
            break
            
    if not matched_seed:
        print("[-] Seed synchronization failed.")
        print(f"[-] System Time was: {client_time} ({time.ctime(client_time)})")
        print("[-] Please ensure your local clock is synchronized via NTP, or expand the search range further.")
        s.close()
        return

    # 4. Burn the current prompt (send a dummy guess to move to Password 2)
    print("[*] Sending dummy guess to advance server to iteration 2...")
    try:
        s.sendall(b"dummy_guess\n")
    except Exception as e:
        print(f"[-] Failed to send dummy guess: {e}")
        s.close()
        return
    
    # Receive the second prompt response
    data = recv_until(s, "Your guess: ")
    print(f"\n[Server Output 2]:\n{data}")
    
    # 5. Send the predicted Password 2 to capture the flag
    print(f"[*] Sending predicted solution: {pass_2}")
    try:
        s.sendall(f"{pass_2}\n".encode())
    except Exception as e:
        print(f"[-] Failed to send solution: {e}")
        s.close()
        return
    
    # Read the final payload flag response until EOF
    print("[*] Receiving flag...")
    final_response = ""
    while True:
        try:
            chunk = s.recv(1024).decode()
        except socket.error as e:
            print(f"[-] Socket read error during flag retrieval: {e}")
            break
        if not chunk:
            break
        final_response += chunk
    
    print(f"\n[Result]:\n{final_response}")
    s.close()

if __name__ == "__main__":
    pwn()
