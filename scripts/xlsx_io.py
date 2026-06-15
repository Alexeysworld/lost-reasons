#!/usr/bin/env python3
"""
xlsx_io.py — read an input lost-deals xlsx into JSON, and write a result xlsx
with the three added columns the analysis produces.

Read:
    python scripts/xlsx_io.py read  input.xlsx  out.json
Write:
    python scripts/xlsx_io.py write input.xlsx  classifications.json  result.xlsx

`classifications.json` is a list of objects keyed by deal id:
    { "<deal_id>": {
         "real_reason": "Конкурент",
         "detail":      "Остались на Retail CRM",
         "rationale":   "Коммент при проигрыше: ...; Note 14.04: ...",
         "confidence":  "high" | "medium" | "low"
      }, ... }

The result xlsx = all original columns + appended:
    "Реальная причина проигрыша (авто)"
    "Детализация (конкурент X / модуль Y)"
    "Обоснование"
    "Уверенность"
"""
import sys, json
import openpyxl
from openpyxl.styles import Font, Alignment, PatternFill

ID_HEADER = "Deal - ID"
ADDED = ["Реальная причина проигрыша (авто)",
         "Детализация (конкурент X / модуль Y)",
         "Обоснование",
         "Уверенность"]

def read(inp, outp):
    wb = openpyxl.load_workbook(inp, data_only=True)
    ws = wb.active
    hdr = [ws.cell(1, c).value for c in range(1, ws.max_column + 1)]
    rows = []
    for r in range(2, ws.max_row + 1):
        rows.append({hdr[c-1]: ws.cell(r, c).value for c in range(1, ws.max_column + 1)})
    json.dump({"headers": hdr, "rows": rows}, open(outp, "w"),
              ensure_ascii=False, indent=1)
    print(f"read {len(rows)} rows -> {outp}")

def write(inp, clsf_path, outp):
    cls = json.load(open(clsf_path))
    wb = openpyxl.load_workbook(inp)
    ws = wb.active
    hdr = [ws.cell(1, c).value for c in range(1, ws.max_column + 1)]
    id_col = hdr.index(ID_HEADER) + 1
    base = ws.max_column
    bold = Font(bold=True)
    fill = PatternFill("solid", fgColor="FFF2CC")
    for i, name in enumerate(ADDED):
        c = ws.cell(1, base + 1 + i, name)
        c.font = bold; c.fill = fill
    for r in range(2, ws.max_row + 1):
        did = ws.cell(r, id_col).value
        key = str(int(did)) if did is not None else None
        rec = cls.get(key, {})
        vals = [rec.get("real_reason", ""), rec.get("detail", ""),
                rec.get("rationale", ""), rec.get("confidence", "")]
        for i, v in enumerate(vals):
            cell = ws.cell(r, base + 1 + i, v)
            cell.alignment = Alignment(wrap_text=True, vertical="top")
    for i in range(len(ADDED)):
        ws.column_dimensions[ws.cell(1, base + 1 + i).column_letter].width = 38
    wb.save(outp)
    print(f"wrote {outp} (+{len(ADDED)} columns)")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(__doc__); sys.exit(1)
    if sys.argv[1] == "read":
        read(sys.argv[2], sys.argv[3])
    elif sys.argv[1] == "write":
        write(sys.argv[2], sys.argv[3], sys.argv[4])
    else:
        print(__doc__); sys.exit(1)
