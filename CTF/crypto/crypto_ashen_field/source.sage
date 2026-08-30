import secrets, hashlib
from Crypto.Util.Padding import pad
from Crypto.Cipher import AES

FLAG = open("flag.txt", "rb").read()

q = 2

def keygen(n):
    K = GF(q)
    _vars = [f"x{i}" for i in range(1, n+1)]
    R = PolynomialRing(K, _vars, n)
    J = ideal([x^q-x for x in R.gens()])
    H = R.quotient_ring(J, _vars)

    S_B = random_vector(K, n)
    T_B = random_vector(K, n)
    while True:
        S_A, T_A = [matrix.random(K, n, n) for _ in range(2)]
        if not False in [S_A.is_singular(), T_A.is_singular()]:
            break

    S = (S_A, S_B)
    T = (T_A, T_B)

    Rv = vector(R, n, R.gens())
    Rv = S[0] * Rv + S[1]

    PRK.<x> = PolynomialRing(K)
    PRL.<t> = PolynomialRing(R)
    g = PRK.irreducible_element(n)
    g = PRL(g)
    I = PRL.ideal([g])
    Q = PRL.quotient_ring(I)
    
    F = PRL(Rv.list()[::-1])
    F = Q(F^(2*q)+F^q+1)

    PK = vector(R, n, F.list()[::-1])
    PK = T[0] * PK + T[1]

    return PK

def encrypt(P, PK):
    l = len(P.bits())
    msg = list(map(int, [0 for _ in range(N-l)] + P.bits()))
    return PK(msg).list()

N = 137
PK = keygen(N)

while True:
    KEY = Integer("".join(str(secrets.randbits(1)) for _ in range(N)), 2)
    if KEY.nbits() == N:
        break

encrypted_key = encrypt(KEY, PK)

AES_KEY = hashlib.sha256(str(KEY).encode()).digest()
cipher = AES.new(AES_KEY, AES.MODE_ECB)
enc_flag = cipher.encrypt(pad(FLAG, 16))

with open("output.txt", "w") as f:
    f.write(str(PK)+"\n")
    f.write(str(encrypted_key)+"\n")
    f.write(enc_flag.hex()+"\n")