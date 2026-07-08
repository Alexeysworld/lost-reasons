import json, sys
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager

cls=json.load(open("data/june_full_classifications.json"))
raw=json.load(open("data/deals_dump_june311549.json"))["data"]
SRC={56:"Холодные",58:"Горячие",63:"Ивент/контент",3977:"Ивент/контент"}
srcmap={}
for d in raw:
    sid=(d.get("custom_fields") or {}).get("af70f9391eeba6e8849e5de4bf671c05dfa80a33")
    srcmap[d["id"]]=SRC.get(sid,"Холодные")  # источник не указан -> Холодные

import collections
ct=collections.defaultdict(lambda: collections.Counter())
for k,v in cls.items():
    ct[v["real_reason"]][srcmap[int(k)]]+=1

order=["Холодные","Горячие","Ивент/контент"]
colors={"Холодные":"#aec5f2","Горячие":"#f2a6a6","Ивент/контент":"#f5e07a"}
# sort categories by total asc (barh bottom-up) so biggest on top
cats=sorted(ct.keys(), key=lambda c: sum(ct[c].values()))
labels={"Клиенту дорого, хотя база норм":"Клиенту дорого, хотя база норм",
        "Руководитель заблокировал решение":"Руководитель заблокировал решение"}

fig,ax=plt.subplots(figsize=(11,6.2))
y=range(len(cats))
left=[0]*len(cats)
for src in order:
    vals=[ct[c][src] for c in cats]
    ax.barh(list(y), vals, left=left, color=colors[src], label=src, edgecolor="white", height=0.62)
    for i,(v,l) in enumerate(zip(vals,left)):
        if v>0:
            ax.text(l+v/2, i, str(v), va="center", ha="center", fontsize=9,
                    color="#333" if src!="Не указан" else "#666")
    left=[l+v for l,v in zip(left,vals)]
# total at end
for i,c in enumerate(cats):
    t=sum(ct[c].values())
    ax.text(t+0.4, i, str(t), va="center", ha="left", fontsize=9, fontweight="bold", color="#222")

ax.set_yticks(list(y))
ax.set_yticklabels([labels.get(c,c) for c in cats], fontsize=10)
ax.set_xlim(0, max(sum(ct[c].values()) for c in cats)+2)
ax.set_title("Причины проигрыша сделок Midmarket в июне 2026", fontsize=13, pad=14, color="#333")
ax.spines[["top","right","left"]].set_visible(False)
ax.tick_params(left=False)
ax.set_axisbelow(True); ax.xaxis.grid(True, color="#eee")
ax.legend(loc="lower right", frameon=False, fontsize=9, ncol=1)
plt.tight_layout()
plt.savefig(sys.argv[1], dpi=150, bbox_inches="tight")
print("saved",sys.argv[1])
