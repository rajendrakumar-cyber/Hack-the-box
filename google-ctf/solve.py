import ctypes
import os
import subprocess
import time

def main():
    # 1. Load C library for rand/srand functions
    try:
        libc = ctypes.CDLL("libc.so.6")
    except OSError:
        # Fallback for systems where libc.so.6 might be named differently
        libc = ctypes.CDLL(None)

    def get_password(seed):
        libc.srand(seed)
        # We need to simulate:
        # Password 1
        pw1 = "".join(chr(ord('a') + (libc.rand() % 26)) for _ in range(20))
        # Password 2
        pw2 = "".join(chr(ord('a') + (libc.rand() % 26)) for _ in range(20))
        return pw1, pw2

    # 2. Launch the challenge program with PATH set to include current directory
    # so that system("cat /flag") runs our fake "cat" script.
    env = os.environ.copy()
    env["PATH"] = f".:{env.get('PATH', '')}"

    print("[*] Launching challenge binary...")
    proc = subprocess.Popen(
        ["./a.out"],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        env=env,
        text=True,
        bufsize=1
    )

    # 3. Read the first password hint
    # Format: "Password is xxxxx..............."
    line = proc.stdout.readline().strip()
    print(f"[+] Server output: {line}")
    
    if not line.startswith("Password is "):
        print("[-] Unexpected output from binary")
        proc.kill()
        return

    prefix = line.split()[2].replace(".", "")
    print(f"[+] Extracted password prefix: {prefix}")

    # 4. Brute force the seed around the current time
    now = int(time.time())
    print(f"[*] Current time: {now}. Brute forcing seed in range [{now - 60}, {now + 60}]...")
    
    target_seed = None
    predicted_pw1 = None
    predicted_pw2 = None

    for s in range(now - 60, now + 61):
        pw1, pw2 = get_password(s)
        if pw1.startswith(prefix):
            target_seed = s
            predicted_pw1 = pw1
            predicted_pw2 = pw2
            break

    if target_seed is None:
        print("[-] Seed not found in the search window. Try expanding the range.")
        proc.kill()
        return

    print(f"[+] Found matching seed: {target_seed}")
    print(f"[+] Predicted Password 1: {predicted_pw1}")
    print(f"[+] Predicted Password 2: {predicted_pw2}")

    # Read "Your guess: " prompt
    prompt = proc.stdout.read(len("Your guess: "))
    
    # Send incorrect guess first to progress to the next iteration
    print("[*] Sending dummy guess for the first password...")
    proc.stdin.write("wrongguess\n")
    proc.stdin.flush()

    # Read "Wrong! Try again in a second..." and next "Password is..." line
    line = proc.stdout.readline().strip() # "Wrong! Try again..."
    line = proc.stdout.readline().strip() # Next "Password is..."
    print(f"[+] Server output: {line}")

    # Read "Your guess: " prompt for the second iteration
    prompt = proc.stdout.read(len("Your guess: "))

    # Now send the predicted second password
    print(f"[*] Sending predicted password: {predicted_pw2}")
    proc.stdin.write(f"{predicted_pw2}\n")
    proc.stdin.flush()

    # Read the response (which should run "cat /flag" and print the flag)
    output = []
    while True:
        line = proc.stdout.readline()
        if not line:
            break
        output.append(line.strip())

    print("\n--- Flag Output ---")
    print("\n".join(output))
    print("-------------------")

if __name__ == "__main__":
    main()
