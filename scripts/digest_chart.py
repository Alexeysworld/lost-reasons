#!/usr/bin/env python3
"""
Дайджест-график (вариант C): горизонтальный стек по источнику, скруглённые бары,
доля % и дельта к предыдущему месяцу в п.п.

Usage:
  python scripts/digest_chart.py <classifications.json> <deals_dump.json> \
         <prev_dist.json|-> "<Заголовок месяца>" <out.png>

- classifications.json: {deal_id: {real_reason, detail, rationale, confidence}}
- deals_dump.json: сырые сделки get_deals (для источника). Можно "-" — тогда всё Холодные.
- prev_dist.json: {total, counts} прошлого месяца (scripts/dist_from_classifications.py).
  "-" — дельта не показывается.
"""
import sys, json, collections
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt

clsf, dump, prev, title, out = sys.argv[1:6]
cls=json.load(open(clsf))
det={k:v for k,v in cls.items() if v["real_reason"]!="Не определено"}
N=len(det)
cat=collections.Counter(v["real_reason"] for v in det.values())

# источник -> корзина (пусто/прочее -> Холодные, правило заказчика)
SRC={56:"Холодные",58:"Горячие",63:"Ивент/контент",3977:"Ивент/контент"}
srcmap={}
if dump!="-":
    for d in json.load(open(dump))["data"]:
        sid=(d.get("custom_fields") or {}).get("af70f9391eeba6e8849e5de4bf671c05dfa80a33")
        srcmap[d["id"]]=SRC.get(sid,"Холодные")
ct=collections.defaultdict(lambda: collections.Counter())
for k,v in det.items(): ct[v["real_reason"]][srcmap.get(int(k),"Холодные")]+=1

prevd=None
if prev!="-":
    prevd=json.load(open(prev))

SHORT={"Клиенту дорого, хотя база норм":"Дорого (база норм)",
       "Руководитель заблокировал решение":"Руководитель заблокировал",
       "Клиент перестал отвечать":"Перестал отвечать",
       "Не заинтересовали гендира на первой встрече":"Не заинтересовали гендира"}
order=["Холодные","Горячие","Ивент/контент"]
COL={"Холодные":"#6f9be8","Горячие":"#ec9393","Ивент/контент":"#efc94c"}
cats=sorted(cat, key=lambda c: cat[c])   # asc -> biggest on top
LW=16

fig,ax=plt.subplots(figsize=(11.5, max(3.2, 0.62*len(cats)+1.6)))
for i,c in enumerate(cats):
    segs=[(s,ct[c][s]) for s in order if ct[c][s]>0] or [("Холодные",cat[c])]
    t=cat[c]
    ax.plot(0,i,marker="o",markersize=LW,color=COL[segs[0][0]],zorder=2,markeredgewidth=0)
    ax.plot(t,i,marker="o",markersize=LW,color=COL[segs[-1][0]],zorder=2,markeredgewidth=0)
    left=0
    for s,v in segs:
        ax.plot([left,left+v],[i,i],lw=LW,solid_capstyle="butt",color=COL[s],zorder=3)
        if v>=2: ax.text(left+v/2,i,str(v),va="center",ha="center",fontsize=9,color="white",fontweight="bold",zorder=4)
        left+=v
    jsh=round(100*t/N)
    ax.text(t+0.5,i,f"{t}",va="center",ha="left",fontsize=11,fontweight="bold",color="#222",zorder=4)
    ax.text(t+1.5,i,f"{jsh}%",va="center",ha="left",fontsize=9.5,color="#9a9a9a",zorder=4)
    if prevd:
        msh=round(100*prevd["counts"].get(c,0)/prevd["total"]) if prevd["total"] else 0
        d=jsh-msh
        dt,dc=(f"▲ +{d} п.п.","#c0392b") if d>0 else (f"▼ {d} п.п.","#27ae60") if d<0 else ("= 0 п.п.","#9a9a9a")
        ax.text(t+3.0,i,dt,va="center",ha="left",fontsize=9,color=dc,fontweight="bold",zorder=4)
# подписи источников над верхним баром
top=len(cats)-1; l=0
for s in order:
    v=ct[cats[top]][s]
    if v>0: ax.text(l+v/2,top+0.5,s,ha="center",va="bottom",fontsize=8.5,color=COL[s],fontweight="bold")
    l+=v
ax.set_yticks(range(len(cats))); ax.set_yticklabels([SHORT.get(c,c) for c in cats],fontsize=10.5,color="#333")
ax.set_ylim(-0.6,len(cats)-0.05); ax.set_xlim(-0.5, max(cat.values())+6); ax.set_xticks([]); ax.tick_params(left=False)
for s in ax.spines.values(): s.set_visible(False)
ax.set_title(title,fontsize=14,fontweight="bold",color="#222",loc="left",pad=26)
sub=f"{N} сделок · стек по источнику" + (" · ▲▼ п.п. к пред. месяцу" if prevd else "")
ax.annotate(sub,(0,1.03),xycoords="axes fraction",fontsize=9.5,color="#9a9a9a")
plt.tight_layout(); plt.savefig(out,dpi=150,bbox_inches="tight")
print("saved",out)
