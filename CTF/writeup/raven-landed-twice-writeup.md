# HTB OSINT Challenge — "The Raven That Landed Twice" — Writeup

**Target:** `154.57.164.67:32234`
**Category:** OSINT / client-side data recon
**Stack:** React + Vite SPA (bolt.new-generated), nginx, `/api/check` (Oath
answer verification only — all "case data" lives client-side)

## Summary

The challenge presents itself as five separate in-universe tools — Aircraft
Registry, Movement Ledger, Courier Mail, Skyglass Browser, Oath Submission —
but they're all just UI sections of one single-page React app. There is no
real backend serving the case data; it's a bundled, minified JS file that
ships **all records to the client on page load**, including the "restricted"
ones. The task boils down to: find the JS bundle, grep it for the leaked
identifiers from the scenario text (Mode-S hex, callsign), and read off the
matching Movement Ledger record directly.

## Step-by-step

### 1. Recon the target
```bash
curl -s http://154.57.164.67:32234/
```
Reveals a Vite + React SPA shell (`<div id="root">`, `/assets/index-*.js`).
Testing other in-universe paths (`/registry`, `/mail`, `/browser`, `/oath`)
all return the identical HTML shell — confirms client-side routing, so the
real content lives in the JS bundle, not in distinct server routes.

### 2. Check the one non-SPA path
```bash
curl -sv http://154.57.164.67:32234/api 2>&1 | grep -i location
```
```
Location: http://154.57.164.67/api/
```
This is nginx forwarding to a backend — but turned out to be a dead end for
case data; it only backs a single endpoint:
```
POST /api/check   { "question": ..., "answer": ... }
```
This is the **Oath Submission** answer-verification endpoint, not a data
source. All the actual investigative content is client-side.

### 3. Pull down the JS bundle and grep for scenario keywords
```bash
curl -s http://154.57.164.67:32234/assets/index-dOxwAnh8.js -o app.js
grep -aioE '(registry|ledger|courier|skyglass|mail|oath|movement)[a-zA-Z0-9_-]*' app.js | sort -u
```
Confirms all five "apps" (registry, ledger, mail, skyglass, oath) are
literal identifiers/labels inside the same bundle — not separate services.

### 4. Search directly for the leaked identifiers from the scenario text
The scenario itself hands you the two identifiers to pivot on: Mode-S hex
`43E91C` and callsign `VLR602`. Search the bundle for them directly along
with related field names:
```bash
python3 - <<'EOF'
data = open('app.js', 'rb').read()
for kw in [b'mail-001', b'modeSHex', b'callsign', b'movementId', b'43E91C', b'VLR602']:
    idx = data.find(kw)
    if idx != -1:
        print(f"--- {kw.decode()} @ {idx} ---")
        print(data[max(0,idx-200):idx+800].decode(errors='replace'))
        print()
EOF
```

This dumped the full Movement Ledger array embedded in the bundle,
including the exact record matching both leaked identifiers:

```json
{
  "movementId": "CSE-2026-0718-0091",
  "callsign": "VLR602",
  "registration": "2-RUNE",
  "modeS": "43E91C",
  "departureAerodrome": "Suncourt Field",
  "departureCode": "SCF",
  "offBlock": "2026-07-17 23:58 UTC",
  "arrivalAerodrome": "Crownspire Executive Field",
  "arrivalCode": "CSE",
  "landing": "2026-07-18 00:47 UTC",
  "onBlock": "2026-07-18 00:51 UTC",
  "parkingStand": "4B",
  "flightType": "Non-scheduled private",
  "handler": "Crownspire Crown Aviation Services",
  "passengerManifest": "Restricted — Court Courtesy Order CCO-2026-0441"
}
```

This single record is the "raven that landed twice": the same aircraft
appears under its **callsign** (`VLR602`, used in the air / dispatch slip)
and its **registration** (`2-RUNE`, used on the ground / airside ledger) —
tying both leaked technical identifiers to one aircraft and exposing the
registration behind the operator.

### 5. Build the flag from the required format
Given format:
```
HTB{REGISTRATION_FROM_DEPARTURE_AERODROME_TO_PARKING_STAND}
```
Example:
```
HTB{G-NTWK_FROM_BRINDLE_MOOR_TO_7C}
```
Mapped from the recovered record (uppercased, spaces → underscores):
- Registration: `2-RUNE`
- Departure aerodrome: `Suncourt Field` → `SUNCOURT_FIELD`
- Parking stand: `4B`

```
HTB{2-RUNE_FROM_SUNCOURT_FIELD_TO_4B}
```

### 6. Confirm via the in-app Oath Submission flow before treating as final
The scenario explicitly instructs confirming findings through the Oath app
(backed by `POST /api/check`) before submitting — done via the UI, which
validated the answer as correct.

## Flag
```
HTB{2-RUNE_FROM_SUNCOURT_FIELD_TO_4B}
```

## Takeaways / patterns to remember

- **For "multi-app" OSINT/web scenarios that resolve to one SPA:** don't
  waste time treating in-universe tool names (Registry/Ledger/Mail/etc.) as
  separate services to enumerate — check first whether they're just
  client-side routes in a single bundle. A quick `curl` diff of a few
  "different" paths returning identical HTML is the tell.
- **Always pull and grep the JS bundle early** for React/Vite SPA
  challenges — bolt.new / AI-scaffolded apps frequently ship all "backend"
  data as a hardcoded array directly in the client bundle rather than
  behind a real API, especially in CTF/demo contexts. This makes
  `curl the bundle + grep for scenario keywords` a very high-value first
  move, often before even opening a browser.
- **Use the scenario's own leaked details as your grep seeds.** The
  narrative handed us `43E91C` and `VLR602` directly — searching the
  bundle for those exact strings immediately located the one authoritative
  record, skipping any need to browse the UI manually or guess where data
  might live.
- **Python byte-offset slicing beats fragile regex on minified JS.** When
  `grep -oE` returns truncated or empty matches on a single-line minified
  bundle, dropping to Python (`data.find(keyword)` + slicing a window
  around the match) reliably recovers full context regardless of how the
  JSON is formatted or nested.
