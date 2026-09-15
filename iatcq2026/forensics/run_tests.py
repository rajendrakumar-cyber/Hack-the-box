import struct
import json
from datetime import datetime
from collections import defaultdict
from test_decoders import test_bitstream

PCAP_PATH = "Timeseries Trap/telemetry.pcap"

suspect_ids = {'PT-111', 'PT-110', 'FT-113', 'FT-110', 'PT-103', 'FT-107', 'FT-114'}

sensor_data = defaultdict(dict)
all_pkts = []

with open(PCAP_PATH, "rb") as f:
    f.read(24)
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
            sid = msg["id"]
            if sid in suspect_ids:
                dt = datetime.fromisoformat(msg["ts"].replace("Z", "+00:00"))
                offset = t_arrival - dt.timestamp()
                bit = 1 if offset > 0.035 else 0
                seq = msg["seq"]
                sensor_data[sid][seq] = (bit, t_arrival, dt.timestamp())
                all_pkts.append((t_arrival, dt.timestamp(), sid, seq, bit))
        except Exception:
            continue

print("=== PHASE 1: Individual Sensors ===")
active_ranges = {
    'PT-111': (869, 2387),
    'PT-110': (886, 2389),
    'FT-113': (2255, 4050),
    'FT-110': (3897, 4733),
    'PT-103': (4112, 4673),
    'FT-107': (4406, 5899),
    'FT-114': (4417, 6199)
}

sensor_bits = {}
for sid in suspect_ids:
    s_min, s_max = active_ranges[sid]
    bits = [sensor_data[sid].get(seq, (0,))[0] for seq in range(s_min, s_max + 1)]
    sensor_bits[sid] = bits
    test_bitstream(bits, f"Individual {sid}")

print("Phase 1 complete.")
