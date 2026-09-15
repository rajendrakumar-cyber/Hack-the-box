import struct
import json
from datetime import datetime
from collections import defaultdict
from Crypto.Cipher import AES, ARC4

PCAP_PATH = "Timeseries Trap/telemetry.pcap"
KEY = bytes.fromhex("f05d9b66d1877dffb5d46f9ea92669ef")

# 1. Parse PCAP and collect per-sensor timings
sensor_packets = defaultdict(list)
all_suspect_packets = []

suspect_ids = {'PT-111', 'PT-110', 'FT-113', 'FT-110', 'PT-103', 'FT-107', 'FT-114'}

with open(PCAP_PATH, "rb") as f:
    f.read(24)  # Global header
    while True:
        phdr = f.read(16)
        if not phdr:
            break
        sec, usec, caplen, origlen = struct.unpack("<IIII", phdr)
        t_arrival = sec + usec / 1e6
        raw_pkt = f.read(caplen)
        udp_payload = raw_pkt[42:]
        try:
            msg = json.loads(udp_payload.decode("utf-8"))
            dt = datetime.fromisoformat(msg["ts"].replace("Z", "+00:00"))
            offset = t_arrival - dt.timestamp()
            sid = msg["id"]
            seq = msg["seq"]
            bit = 1 if offset > 0.035 else 0
            if sid in suspect_ids:
                sensor_packets[sid].append((seq, offset, t_arrival, bit))
                all_suspect_packets.append((t_arrival, dt.timestamp(), sid, seq, bit, offset))
        except Exception:
            continue

print("Loaded suspect packets.")
