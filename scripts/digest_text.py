#!/usr/bin/env python3
"""
Собрать текст дайджеста по проигрышам.

Usage:
  python scripts/digest_text.py <classifications.json> <prev_dist.json|-> "<месяц>" [out.md]

Правила (зашиты):
- НЕ упоминаем чистку дублей / служебные пометки в заголовке.
- «Главное» = только неочевидная динамика «было→стало» к прошлому месяцу (топ-движения
  доли по модулю ≥3 п.п.). НЕ пишем очевидное с графика («на 1 месте», «лидер месяца»).
- Доли считаем от числа сделок с определённой причиной.
"""
import sys, json, re, collections

clsf, prev, month = sys.argv[1], sys.argv[2], sys.argv[3]
out = sys.argv[4] if len(sys.argv) > 4 else None
cls = json.load(open(clsf))
det = {k: v for k, v in cls.items() if v["real_reason"] != "Не определено"}
N = len(det)                                   # знаменатель долей
cat = collections.Counter(v["real_reason"] for v in det.values())
def sh(c): return round(100 * cat[c] / N) if N else 0

prevd = json.load(open(prev)) if prev != "-" else None
def prev_sh(c):
    if not prevd or not prevd["total"]: return None
    return round(100 * prevd["counts"].get(c, 0) / prevd["total"])

def details(cname): return [v["detail"] for v in det.values() if v["real_reason"] == cname and v.get("detail")]

L = []
L.append(f"📊 Дайджест по {len(cls)} проигранным в Midmarket сделкам в {month}.\n")

# ---- Главное: топ-движения было→стало ----
L.append("Главное (динамика к пред. месяцу):")
if prevd:
    movers = []
    seen = set(cat) | set(prevd["counts"])
    for c in seen:
        j = sh(c); m = prev_sh(c) or 0
        d = j - m
        if abs(d) >= 3:
            movers.append((abs(d), d, c, m, j))
    movers.sort(reverse=True)
    for _, d, c, m, j in movers[:4]:
        ar = "▲" if d > 0 else "▼"
        L.append(f"• «{c}»: {m}% → {j}% ({ar} {'+' if d>0 else ''}{d} п.п.)")
    if not movers:
        L.append("• без заметных сдвигов долей к прошлому месяцу")
else:
    L.append("• (нет данных прошлого месяца для сравнения)")
L.append("")

# ---- Конкурент ----
def block_competitor():
    ds = details("Конкурент") + details("Конкуренты")
    n = cat["Конкурент"] + cat["Конкуренты"]
    if not n: return
    INHOUSE = re.compile(r"самопис|inhouse|инхаус|делают сам|делать сам|своими силами|реализуют сам|строит сам|Chatium|ИИ-агент|1С-Фитнес", re.I)
    inh = [d for d in ds if INHOUSE.search(d)]
    vend = collections.Counter()
    for d in ds:
        if INHOUSE.search(d): continue
        key = re.split(r"\s*[\(—-]", d)[0].strip()
        key = re.sub(r"^(Остались на|Выбрали|Устраивает|Решили|Сидят на|Работают на|На)\s+", "", key, flags=re.I).strip()
        vend[key] += 1
    L.append(f"Каким конкурентам проигрываем ({n})")
    if inh:
        L.append(f"Своя разработка / делают сами — {len(inh)}")
    for v, k in sorted(((v, k) for k, v in vend.items() if v >= 2), reverse=True):
        L.append(f"{k} — {v}")
    ones = [k for k, v in vend.items() if v == 1]
    if ones:
        L.append("По 1 — " + ", ".join(ones))
    L.append("")

# ---- Интеграция ----
def block_integration():
    ds = details("Интеграция"); n = cat["Интеграция"]
    if not n: return
    L.append(f"По интеграции ({n})")
    for d in ds: L.append(f"— {d}")
    L.append("")

# ---- Дорого ----
def block_price():
    ds = details("Клиенту дорого, хотя база норм"); n = cat["Клиенту дорого, хотя база норм"]
    if not n: return
    L.append(f"Клиенту дорого / бюджет ({n})")
    L.append("; ".join(ds))
    L.append("")

# ---- Мелкий/нецелевой ----
def block_segment():
    ss = cat["SS"]; nt = cat["Нецелевой"] + cat["Нецелевые"]
    if not (ss or nt): return
    parts = []
    if ss:
        p = f"SS — {ss} ({sh('SS')}%)"
        ps = prev_sh("SS")
        if ps is not None:
            d = sh("SS") - ps
            if abs(d) >= 3: p += f", {'▲ +' if d>0 else '▼ '}{d} п.п."
        parts.append(p)
    if nt: parts.append(f"Нецелевой — {nt}")
    tot = ss + nt
    L.append("Мелкий / нецелевой сегмент")
    L.append(" · ".join(parts) + f" · Вместе «не наш сегмент»: {tot} ({round(100*tot/N)}%)")
    L.append("")

# ---- Остальное ----
def block_rest():
    used = {"Конкурент","Конкуренты","Интеграция","Клиенту дорого, хотя база норм","SS","Нецелевой","Нецелевые",
            "Попросили отложить"}
    rest = [(c, cat[c]) for c in cat if c not in used]
    undet = sum(1 for v in cls.values() if v["real_reason"] == "Не определено")
    if not rest and not undet: return
    L.append("Остальное")
    items = [f"{c} — {n}" for c, n in sorted(rest, key=lambda x: -x[1])]
    if undet: items.append(f"Причина не определена — {undet}")
    L.append(" · ".join(items))
    L.append("")

block_competitor(); block_integration(); block_price(); block_segment(); block_rest()
text = "\n".join(L).rstrip() + "\n"
if out:
    open(out, "w").write(text); print("saved", out)
else:
    print(text)
