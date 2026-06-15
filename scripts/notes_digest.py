#!/usr/bin/env python3
"""
notes_digest.py — turn a raw Pipedrive get_notes JSON dump into a compact,
signal-focused digest for loss-reason analysis.

Usage:
    python scripts/notes_digest.py data/notes/<deal_id>.json

Input: the JSON returned by MCP tool `mcp__pipedrive__get_notes` (object with
a "data" list, or a bare list of note objects).

It classifies each note, strips HTML, and surfaces the blocks that matter for
determining the REAL loss reason:
  - manager free-text comments (internal observations, often the honest reason)
  - the "Оценка встречи" note -> "Прогноз по сделке" / "Что тормозит" blocks
  - outbound follow-up emails that quote the client's own words
It hides noise (lead-capture autonotes, long meeting transcriptions).
"""
import sys, json, re, html

EVAL_MARKERS = ("Оценка встречи", "Прогноз по сделке", "Оценка по критериям")
TRANSCRIPT_MARKERS = ("Транскрипция", "[15:", "[09:", "UNKNOWN_SPEAKER")
AUTONOTE_MARKERS = ("Registered utm", "metrikaid", "googleClientId", "siteUrl:")

def strip(h):
    if not h:
        return ""
    h = re.sub(r'<br\s*/?>', '\n', h)
    h = re.sub(r'</(div|p|li|ul|ol|h\d|blockquote)>', '\n', h)
    h = re.sub(r'<li>', '- ', h)
    h = re.sub(r'<[^>]+>', '', h)
    h = html.unescape(h)
    h = re.sub(r'\n{3,}', '\n\n', h)
    return h.strip()

def classify(text):
    if any(m in text for m in AUTONOTE_MARKERS):
        return "autonote"
    if any(m in text for m in EVAL_MARKERS):
        return "eval"
    if any(m in text for m in TRANSCRIPT_MARKERS):
        return "transcript"
    return "comment"

def extract_eval_blocks(text):
    """Pull the decision-relevant tail of an 'Оценка встречи' note."""
    out = {}
    m = re.search(r'Статус сделки[:\s]*(.+)', text)
    if m: out["status"] = m.group(1).strip()[:300]
    m = re.search(r'Прогноз по сделке\s*(.+?)(?:Что помогает|Что тормозит|$)', text, re.S)
    if m: out["forecast"] = m.group(1).strip()[:500]
    m = re.search(r'Что тормозит[:\s]*(.+?)$', text, re.S)
    if m: out["blockers"] = m.group(1).strip()[:800]
    return out

def main(path):
    raw = json.load(open(path))
    notes = raw["data"] if isinstance(raw, dict) else raw
    notes = sorted(notes, key=lambda n: n.get("add_time", ""))
    print(f"# Deal notes digest  ({len(notes)} notes)\n")
    for n in notes:
        text = strip(n.get("content", ""))
        if not text:
            continue
        kind = classify(text)
        author = (n.get("user") or {}).get("name", "?")
        when = n.get("add_time", "")
        pinned = "📌" if n.get("pinned_to_deal_flag") else "  "
        if kind == "autonote":
            continue
        print(f"{pinned} [{when}] ({author}) <{kind}>")
        if kind == "eval":
            for k, v in extract_eval_blocks(text).items():
                print(f"    {k.upper()}: {v}")
        elif kind == "transcript":
            print(f"    (transcription, {len(text)} chars — skipped; read raw if needed)")
        else:
            print("    " + text.replace("\n", "\n    ")[:1200])
        print()

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(__doc__); sys.exit(1)
    main(sys.argv[1])
