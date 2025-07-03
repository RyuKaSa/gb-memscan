#!/usr/bin/env python3
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
RAW_DUMP = HERE / "memory_dump.json"
OUT_FILE = HERE / "decoded_memory.json"

def load_tbl(fname: str) -> dict[int, str]:
    """
    Load a JSON table whose keys may be hex‐prefixed (e.g. "0x4A") or decimal.
    int(k, 0) auto-detects the base from the string.
    """
    path = HERE / fname
    if not path.exists():
        return {}
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    # Parse keys in hex or decimal automatically
    return {int(k, 0): v for k, v in data.items()}

CHARSET = load_tbl("dataset/charset.json")
SPECIES = load_tbl("dataset/species.json")
MOVES   = load_tbl("dataset/moves.json")
TYPES   = load_tbl("dataset/types.json")
ITEMS   = load_tbl("dataset/items.json")

BADGE_NAMES = [
    "Boulder", "Cascade", "Thunder", "Rainbow",
    "Soul", "Marsh", "Volcano", "Earth"
]

def bcd3(b1: int, b2: int, b3: int) -> int:
    """3‐byte packed BCD → int (e.g. money)."""
    n = lambda x: (x >> 4) * 10 + (x & 0xF)
    return n(b1) * 10000 + n(b2) * 100 + n(b3)

def bcd2(b1: int, b2: int) -> int:
    """2‐byte packed BCD → int (e.g. casino chips)."""
    n = lambda x: (x >> 4) * 10 + (x & 0xF)
    return n(b1) * 100 + n(b2)

def decode_name(bytes_seq: list[int]) -> str:
    """Decode a sequence of bytes into a Pokémon name/string."""
    return "".join(CHARSET.get(b, "?") for b in bytes_seq).strip()

def decode_status(byte: int) -> list[str]:
    """Decode the status‐byte into human‐readable status conditions."""
    if byte == 0:
        return []
    cond = []
    if byte & 0x40: cond.append("PAR")
    if byte & 0x20: cond.append("FRZ")
    if byte & 0x10: cond.append("BRN")
    if byte & 0x08: cond.append("PSN")
    sleep = byte & 0x07
    if sleep:
        cond.append(f"SLP({sleep})")
    return cond

def lookup(table: dict[int, str], key: int) -> str:
    """Generic table lookup with fallback."""
    return table.get(key, f"Unknown({key})")

# Load the raw memory dump (list of [addr_hex, label, raw_value])
with open(RAW_DUMP, "r", encoding="utf-8") as f:
    dump = json.load(f)

# Build an address→(label, raw) map for multi‐byte fields
addr_map = {int(a, 16): (label, raw) for a, label, raw in dump}

money_raw   = [addr_map[x][1] for x in (0xD347, 0xD348, 0xD349)]
chips_raw   = [addr_map[x][1] for x in (0xD5A4, 0xD5A5)]
badge_byte  = addr_map[0xD356][1]

trainer_bytes = [addr_map[0xD158 + i][1] for i in range(5)]
rival_bytes   = [addr_map[0xD34A + i][1] for i in range(8)]

decoded_list = []

for addr_hex, label, raw in dump:
    human = None

    if label == "Money[1]":
        human = bcd3(*money_raw)
    elif label == "Casino Chips[1]":
        human = bcd2(*chips_raw)
    elif label == "Badges Bitfield":
        human = [BADGE_NAMES[i] for i in range(8) if (raw >> i) & 1]
    elif label.startswith("Trainer Name[1]"):
        human = decode_name(trainer_bytes)
    elif label.startswith("Rival Name[1]"):
        human = decode_name(rival_bytes)
    elif "Species" in label:
        human = lookup(SPECIES, raw)
    elif "Move" in label:
        human = lookup(MOVES, raw)
    elif "Type" in label:
        human = lookup(TYPES, raw)
    elif label.endswith("ID"):
        human = lookup(ITEMS, raw)
    elif label.endswith("Status"):
        human = decode_status(raw)

    # Fallback to raw if no decoding rule matched
    if human is None:
        human = raw

    decoded_list.append({
        "address": addr_hex,
        "label": label,
        "raw": raw,
        "decoded": human
    })

with open(OUT_FILE, "w", encoding="utf-8") as f:
    json.dump(decoded_list, f, indent=2, ensure_ascii=False)

print(f"Decoded dump written → {OUT_FILE}")
