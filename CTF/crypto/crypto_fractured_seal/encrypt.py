from Crypto.PublicKey import RSA
from Crypto.Util.number import long_to_bytes, bytes_to_long, getPrime

p = getPrime(1024)
q = getPrime(1024)
n = p * q
e = 0x10001
d = pow(e, -1, (p-1)*(q-1))

m = bytes_to_long(open('flag.txt', 'rb').read())

open('seal.pem', 'wb').write(RSA.construct((n, e, d)).export_key())
open('flag.enc', 'wb').write(long_to_bytes(pow(m, e, n)))