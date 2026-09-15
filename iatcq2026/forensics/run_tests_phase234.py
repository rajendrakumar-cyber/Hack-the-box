import struct
import json
from datetime import datetime
from collections import defaultdict
from test_decoders import test_bitstream, check_content, pack_bits, test_all_ciphers

PCAP_PATH = "Timeseries Trap/telemetry.pcap"
suspect_ids = {'PT-111', 'PT-110', 'FT-113', 'FT-110', 'PT-103', 'FT-107', 'FT-114'}

active_ranges = {
    'PT-111': (869, 2387),
    'PT-110': (886, 2389),
    'FT-113': (2255, 4050),
    'FT-110': (3897, 4733),
    'PT-103': (4112, 4673),
    'FT-107': (4406, 5899),
    'FT-114': (4417, 6199)
}

sensor_data = defaultdict(dict)
all_active_pkts = []
all_pkts_during_window = []

# Window when modulation was happening: seq 869 to 6199
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
            seq = msg["seq"]
            dt = datetime.fromisoformat(msg["ts"].replace("Z", "+00:00"))
            offset = t_arrival - dt.timestamp()
            bit = 1 if offset > 0.035 else 0
            if sid in suspect_ids:
                s_min, s_max = active_ranges[sid]
                if s_min <= seq <= s_max:
                    all_active_pkts.append((t_arrival, dt.timestamp(), sid, seq, bit))
                sensor_data[sid][seq] = bit
        except Exception:
            continue

print("=== TEST A: Chronological by Arrival Time ===")
all_active_pkts.sort(key=lambda x: x[0])
bits_chron_arr = [p[4] for p in all_active_pkts]
print(f"Total bits: {len(bits_chron_arr)}")
test_bitstream(bits_chron_arr, "Chronological Arrival")

print("=== TEST B: Chronological by Nominal Timestamp (dt) ===")
all_active_pkts.sort(key=lambda x: x[1])
bits_chron_dt = [p[4] for p in all_active_pkts]
test_bitstream(bits_chron_dt, "Chronological Nominal TS")

print("=== TEST C: Concatenated in Time Order ===")
# Sensor start order: PT-111, PT-110, FT-113, FT-110, PT-103, FT-107, FT-114
time_order = ['PT-111', 'PT-110', 'FT-113', 'FT-110', 'PT-103', 'FT-107', 'FT-114']
concat_time_bits = []
for sid in time_order:
    s_min, s_max = active_ranges[sid]
    concat_time_bits.extend([sensor_data[sid].get(s, 0) for s in range(s_min, s_max + 1)])
test_bitstream(concat_time_bits, "Concat Time Order")

print("=== TEST D: Concatenated in Registration Order ===")
# Registration order of suspects: PT-110, FT-113, FT-114, PT-111, PT-103, FT-110, FT-107
reg_order = ['PT-110', 'FT-113', 'FT-114', 'PT-111', 'PT-103', 'FT-110', 'FT-107']
concat_reg_bits = []
for sid in reg_order:
    s_min, s_max = active_ranges[sid]
    concat_reg_bits.extend([sensor_data[sid].get(s, 0) for s in range(s_min, s_max + 1)])
test_bitstream(concat_reg_bits, "Concat Reg Order")

print("=== TEST E: Sensor Pairs Interleaved ===")
# Pair 1: PT-111 & PT-110 (common range: 886 to 2387)
p1_b111 = [sensor_data['PT-111'].get(s, 0) for s in range(886, 2388)]
p1_b110 = [sensor_data['PT-110'].get(s, 0) for s in range(886, 2388)]
interleaved_p1 = []
for b1, b0 in zip(p1_b111, p1_b110):
    interleaved_p1.extend([b1, b0])
test_bitstream(interleaved_p1, "Pair1 (111,110) Interleaved")

interleaved_p1_rev = []
for b1, b0 in zip(p1_b110, p1_b111):
    interleaved_p1_rev.extend([b1, b0])
test_bitstream(interleaved_p1_rev, "Pair1 (110,111) Interleaved")

# Pair 2: FT-110 & PT-103 (common range: 4112 to 4673)
p2_b110 = [sensor_data['FT-110'].get(s, 0) for s in range(4112, 4674)]
p2_b103 = [sensor_data['PT-103'].get(s, 0) for s in range(4112, 4674)]
interleaved_p2 = []
for b1, b0 in zip(p2_b110, p2_b103):
    interleaved_p2.extend([b1, b0])
test_bitstream(interleaved_p2, "Pair2 (110,103) Interleaved")

# Pair 3: FT-107 & FT-114 (common range: 4417 to 5899)
p3_b107 = [sensor_data['FT-107'].get(s, 0) for s in range(4417, 5900)]
p3_b114 = [sensor_data['FT-114'].get(s, 0) for s in range(4417, 5900)]
interleaved_p3 = []
for b1, b0 in zip(p3_b107, p3_b114):
    interleaved_p3.extend([b1, b0])
test_bitstream(interleaved_p3, "Pair3 (107,114) Interleaved")

print("All tests finished.")
