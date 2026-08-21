import os
import subprocess

def main():
    # A password whose SHA-256 hash starts with 0x00.
    # SHA-256("286") = 00328ce531f8680d21...
    null_byte_password = "286"

    # Launch the challenge binary with PATH set to include current directory
    # so system("cat /flag") runs our fake "cat" script.
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

    attempt = 1
    while True:
        # Read the first lines ("Password is..." and prompt)
        line = proc.stdout.readline().strip()
        if not line:
            break
        print(f"[Attempt {attempt}] Server: {line}")
        
        # Read the "Your guess: " prompt
        prompt = proc.stdout.read(len("Your guess: "))
        
        # Send the null-byte hash password
        proc.stdin.write(f"{null_byte_password}\n")
        proc.stdin.flush()

        # Read response
        response = proc.stdout.readline().strip()
        if "Wrong!" not in response:
            # We succeeded! Print the rest of the output (the flag)
            print(f"[+] Success! Response: {response}")
            while True:
                line = proc.stdout.readline()
                if not line:
                    break
                print(line.strip())
            break
        
        attempt += 1

if __name__ == "__main__":
    main()
