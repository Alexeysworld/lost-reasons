#!/usr/bin/env python3
"""
deals_to_input.py — convert a Pipedrive get_deals dump (pulled by the agent via
MCP with a filter) into the input JSON the rest of the pipeline expects, so we
DON'T need a manually exported xlsx.

Usage:
    python scripts/deals_to_input.py deals_dump.json data/input.json

`deals_dump.json` = a JSON array of deal objects, OR an object {"data":[...]},
OR several get_deals pages concatenated as a JSON array of such objects.
Each deal must look like a get_deals item (top-level fields + custom_fields map).
"""
import sys, json

# custom_fields code -> output column name (see docs/pipedrive_reference.md)
CF = {
    "96ebda3be9b5a94e1290d7b970d46f99c5204176": "Deal - Коммент при проигрыше Midmarket",
    "f49270833b9e1bf32bb8c93c646cef95919f6156": "Deal - Конкурент: что используют сейчас / какого конкурента выбрали?",
    "6115f35a4f1b6589e0d6ae7fd59e70b3fe66527c": "Deal - Цели клиента из первой встречи",
    "8db38b8f9384d4c59d93059c9584c469ee0b05e6": "Deal - Сильные стороны текущего стека",
    "c587a6ed9abe2da427f39a0b01f64ded31f51011": "Deal - Слабые стороны текущего стека",
}
HEADERS = ["Deal - ID", "Ссылка", "Deal - Title", "Deal - Причина проигрыша",
           "Реальная причина", "Конкурент / Интеграция",
           "Deal - Коммент при проигрыше Midmarket", "Deal - Stage", "Deal - Status",
           "Deal - Конкурент: что используют сейчас / какого конкурента выбрали?",
           "Deal - Цели клиента из первой встречи",
           "Deal - Сильные стороны текущего стека", "Deal - Слабые стороны текущего стека",
           "Deal - lost_time"]

def iter_deals(raw):
    if isinstance(raw, dict):
        raw = [raw]
    for chunk in raw:
        data = chunk["data"] if isinstance(chunk, dict) and "data" in chunk else (
            [chunk] if isinstance(chunk, dict) and "id" in chunk else chunk)
        for d in data:
            yield d

def main(inp, outp):
    raw = json.load(open(inp))
    rows, seen = [], set()
    for d in iter_deals(raw):
        did = d.get("id")
        if did in seen:
            continue
        seen.add(did)
        cf = d.get("custom_fields") or {}
        row = {h: None for h in HEADERS}
        row["Deal - ID"] = did
        row["Ссылка"] = f"https://mindbox.pipedrive.com/deal/{did}"
        row["Deal - Title"] = d.get("title")
        row["Deal - Причина проигрыша"] = d.get("lost_reason")
        row["Deal - Stage"] = d.get("stage_id")
        row["Deal - Status"] = d.get("status")
        row["Deal - lost_time"] = d.get("lost_time")
        for code, col in CF.items():
            row[col] = cf.get(code)
        rows.append(row)
    json.dump({"headers": HEADERS, "rows": rows}, open(outp, "w"),
              ensure_ascii=False, indent=1)
    print(f"converted {len(rows)} deals -> {outp}")

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print(__doc__); sys.exit(1)
    main(sys.argv[1], sys.argv[2])
