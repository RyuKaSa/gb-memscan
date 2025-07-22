# decoder.py
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
RAW_DUMP = HERE / "memory_dump.json"
CHARSET = {}
SPECIES = {}
MOVES = {}
TYPES = {}
ITEMS = {}

def _load_tbl(fname: str) -> dict[int, str]:
    path = HERE / fname
    if not path.exists():
        return {}
    with open(path, encoding="utf-8") as f:
        return {int(k, 0): v for k, v in json.load(f).items()}

def _init_tables():
    global CHARSET, SPECIES, MOVES, TYPES, ITEMS
    CHARSET = _load_tbl("dataset/charset.json")
    SPECIES = _load_tbl("dataset/species.json")
    MOVES   = _load_tbl("dataset/moves.json")
    TYPES   = _load_tbl("dataset/types.json")
    ITEMS   = _load_tbl("dataset/items.json")

def load_dump() -> list:
    _init_tables()
    with open(RAW_DUMP, encoding="utf-8") as f:
        return json.load(f)

def build_value_map(dump: list) -> dict[str, object]:
    addr_map = {int(addr, 16): (label, raw) for addr, label, raw in dump}
    values = {}

    def bcd3(b1, b2, b3): return ((b1 >> 4)*10 + (b1 & 0xF))*10000 + ((b2 >> 4)*10 + (b2 & 0xF))*100 + ((b3 >> 4)*10 + (b3 & 0xF))
    def bcd2(b1, b2): return ((b1 >> 4)*10 + (b1 & 0xF))*100 + ((b2 >> 4)*10 + (b2 & 0xF))

    def decode_name(seq): return "".join(CHARSET.get(b, "?") for b in seq if b != 0x50)
    def decode_status(byte):
        if byte == 0: return []
        cond = []
        if byte & 0x40: cond.append("PAR")
        if byte & 0x20: cond.append("FRZ")
        if byte & 0x10: cond.append("BRN")
        if byte & 0x08: cond.append("PSN")
        if (s := byte & 0x07): cond.append(f"SLP({s})")
        return cond
    def lookup(tbl, k): return tbl.get(k, f"Unknown({k})")

    BADGE_NAMES = ["Boulder","Cascade","Thunder","Rainbow","Soul","Marsh","Volcano","Earth"]

    money_raw     = [addr_map[x][1] for x in (0xD347, 0xD348, 0xD349)]
    chips_raw     = [addr_map[x][1] for x in (0xD5A4, 0xD5A5)]
    trainer_bytes = [addr_map[0xD158 + i][1] for i in range(5)]
    rival_bytes   = [addr_map[0xD34A + i][1] for i in range(8)]

    for _, label, raw in dump:
        decoded = None
        if label == "Money[1]":
            decoded = bcd3(*money_raw)
        elif label == "Casino Chips[1]":
            decoded = bcd2(*chips_raw)
        elif label == "Badges Bitfield":
            decoded = [BADGE_NAMES[i] for i in range(8) if (raw >> i) & 1]
        elif label.startswith("Trainer Name"):
            decoded = decode_name(trainer_bytes)
        elif label.startswith("Rival Name"):
            decoded = decode_name(rival_bytes)
        elif "Move" in label:
            decoded = lookup(MOVES, raw)
        elif "Type" in label:
            decoded = lookup(TYPES, raw)
        elif label.endswith("ID"):
            decoded = lookup(ITEMS, raw)
        elif label.endswith("Status"):
            decoded = decode_status(raw)
        elif label.startswith(("Fought ", "Defeated ", "Have ")) or label.endswith(" gone"):
            decoded = bool(raw)

        values[label] = decoded if decoded is not None and decoded != raw else raw

    return values

def generate_summary(values: dict) -> dict:
    party = []
    size  = values.get("Party Size", 0) or 0
    for i in range(1, size + 1):
        raw_id = values.get(f"PKM{i} Species", 0)
        lo     = values.get(f"PKM{i} HP lo", 0)
        hi     = values.get(f"PKM{i} HP hi", 0)
        hp_current = hi + (lo << 8)
        party.append({
            "species":    SPECIES.get(raw_id, f"Unknown({raw_id})"),
            "level":      values.get(f"PKM{i} Level"),
            "hp_current": hp_current,
            "status":     values.get(f"PKM{i} Status"),
            "types":      [values.get(f"PKM{i} Type1"), values.get(f"PKM{i} Type2")],
            "moves":      [values.get(f"PKM{i} Move{j}") for j in range(1, 5)],
            "pp":         [values.get(f"PKM{i} PP{j}") for j in range(1, 5)]
        })

    return {
        "trainer": {
            "name":       values.get("Trainer Name[1]"),
            "id_hi":      values.get("Player ID-hi"),
            "id_lo":      values.get("Player ID-lo"),
            "party_size": size
        },
        "money":        values.get("Money[1]"),
        "casino_chips": values.get("Casino Chips[1]"),
        "badges":       values.get("Badges Bitfield"),
        "map": {
            "number":        values.get("Current Map Number"),
            "tileset":       values.get("Map Tileset"),
            "width":         values.get("Map Width (blocks)"),
            "height":        values.get("Map Height (blocks)"),
            "player_x":      values.get("Player X-Position"),
            "player_y":      values.get("Player Y-Position"),
            "last_location": values.get("Last Map Location")
        },
        "game_options": {
            "value":       values.get("Game Options"),
            "audio_track": values.get("Audio Track"),
            "audio_bank":  values.get("Audio Bank")
        },
        "party": party,
        "bag": {
            values[f"Bag{i} ID"]: values[f"Bag{i} Qty"]
            for i in range(1, (values.get("Bag Count") or 0) + 1)
            if values.get(f"Bag{i} ID")
        },
        "pc": {
            values[f"PC{i} ID"]: values[f"PC{i} Qty"]
            for i in range(1, (values.get("PC Count") or 0) + 1)
            if values.get(f"PC{i} ID")
        },
        "flags": {
            lbl: bool(values[lbl])
            for lbl in values
            if lbl.startswith(("Fought ", "Defeated ", "Have ")) or lbl.endswith(" gone")
        }
    }

def generate_prose(save: dict) -> str:
    lines = []
    t = save["trainer"]
    m = save["map"]
    g = save["game_options"]

    lines.append(f"Trainer {t['name']} (ID: {t['id_hi']}.{t['id_lo']}), Party Size: {t['party_size']}")
    lines.append(f"Money: ₽{save['money']}, Casino Chips: {save['casino_chips']}")
    lines.append("Badges: " + ", ".join(save["badges"]))

    lines.append(f"Map: Number={m['number']}, Tileset={m['tileset']}, Size={m['width']}x{m['height']}, "
                 f"Player Position=({m['player_x']},{m['player_y']}), Last Location={m['last_location']}")

    lines.append(f"Game Options: Value={g['value']}, Audio Track={g['audio_track']}, Audio Bank={g['audio_bank']}")

    lines.append("Party:")
    for idx, p in enumerate(save["party"], 1):
        moves = [f"{m} (PP {pp})" for m, pp in zip(p["moves"], p["pp"])]
        types = "/".join(p["types"])
        status = ", ".join(p["status"]) if p["status"] else "None"
        lines.append(f" {idx}. {p['species']} - Level {p['level']}, HP {p['hp_current']}, "
                     f"Status: {status}, Types: {types}, Moves: {', '.join(moves)}")

    lines.append("Bag:")
    for item, count in save["bag"].items():
        lines.append(f" - {item}: {count}")

    lines.append("PC Storage:")
    for item, count in save["pc"].items():
        lines.append(f" - {item}: {count}")

    lines.append("Flags:")
    for k, v in save["flags"].items():
        lines.append(f" - {k}: {'Yes' if v else 'No'}")

    return "\n".join(lines)
