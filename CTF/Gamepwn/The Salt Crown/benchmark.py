import time
from Cryptodome.Cipher import AES

key = b"\x00" * 32
block = b"\x00" * 16

t0 = time.time()
n = 100000

for _ in range(n):
    cipher = AES.new(key, AES.MODE_ECB)
    keystream = cipher.encrypt(block)

t1 = time.time()
ops = n / (t1 - t0)
print(f"AES operations per second: {ops:.2f}")
