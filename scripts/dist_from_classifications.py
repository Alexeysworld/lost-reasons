#!/usr/bin/env python3
"""Свести распределение причин по classifications.json -> {total, counts} для дельты.
Usage: python scripts/dist_from_classifications.py classifications.json dist.json
Считает только определённые причины (без 'Не определено')."""
import sys, json, collections
cls=json.load(open(sys.argv[1]))
det=[v["real_reason"] for v in cls.values() if v.get("real_reason")!="Не определено"]
c=collections.Counter(det)
json.dump({"total":len(det),"counts":dict(c)}, open(sys.argv[2],"w"), ensure_ascii=False, indent=1)
print(f"{len(det)} deals -> {sys.argv[2]}")
