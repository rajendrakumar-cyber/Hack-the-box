from hashlib import sha256
from Crypto.Util.Padding import pad
from Crypto.Cipher import AES
import secrets

P = 0xCD4A96D3B7FA7251A1BB765933FB676FCAE8C9026682E34F779122DFD66915BB
FLAG = open("flag.txt", "rb").read().strip()
N = sha256().digest_size * 8

KEY = secrets.token_bytes(32)
KEY_BITS = list(map(int, f"{int.from_bytes(KEY):0256b}"))

def H(msg):
    return pow(G, msg, P)

class Oracle:
    def __init__(self):
        self.appeared = {}
    def oracle(self, i):
        if i in self.appeared:
            return self.appeared[i]
        else:
            ret = secrets.randbelow(2**N) if KEY_BITS[i] == 0 else PK[i % len(PK)][secrets.randbelow(2)]
            self.appeared[i] = ret
        return ret

def keygen():
    sk = [(secrets.randbelow(2**N), secrets.randbelow(2**N)) for _ in range(N)]
    pk = [(H(s[0]), H(s[1])) for s in sk]
    return sk, pk

print("Here is something for you:")
print(AES.new(KEY, AES.MODE_ECB).encrypt(pad(FLAG, 16)).hex())
while True:
    G = int(input("Before we start, give me the hashing generator: "))
    if 1 < G < P:
        break

SK, PK = keygen()
oracle = Oracle()
while True:
    print("1. Oracle")
    print("2. Exit")
    ch = input("> ")
    if ch == "1":
        offset_input = input("Enter offset: ")
        offset_input = offset_input.strip()
        if not offset_input:
            continue
        try:
            offset = int(offset_input)
        except ValueError:
            print("ERROR: Invalid offset input!")
            continue
        if 0 <= offset < len(KEY_BITS):
            print("Oracle result:", oracle.oracle(offset))
        else:
            print("ERROR: Invalid offset. Must be in range [0-{}]".format(len(KEY_BITS)-1))
    elif ch == "2":
        print("bye")
        break
    else:
        print("ERROR: Unknown command.")