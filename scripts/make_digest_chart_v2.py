import json, collections
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patheffects as pe

# ---------- data ----------
cls=json.load(open("data/june_final_classifications.json"))
raw=json.load(open("data/deals_dump_june311549.json"))["data"]
may=json.load(open("data/may_canon_dist.json"))
SRC={56:"Холодные",58:"Горячие",63:"Ивент/контент",3977:"Ивент/контент"}
srcmap={d["id"]:SRC.get((d.get("custom_fields") or {}).get("af70f9391eeba6e8849e5de4bf671c05dfa80a33"),"Холодные") for d in raw}

det={k:v for k,v in cls.items() if v["real_reason"]!="Не определено"}
N=len(det)                                   # 60
cat=collections.Counter(v["real_reason"] for v in det.values())
ct=collections.defaultdict(lambda: collections.Counter())
for k,v in det.items(): ct[v["real_reason"]][srcmap[int(k)]]+=1

SHORT={"Клиенту дорого, хотя база норм":"Дорого (база норм)",
       "Руководитель заблокировал решение":"Руководитель заблокировал",
       "Не заинтересовали ЛВР":"Не заинтересовали ЛВР",
       "Клиент перестал отвечать":"Перестал отвечать"}
def lbl(c): return SHORT.get(c,c)

mtot=may["total"]; mc=may["counts"]
def delta_pp(c): return round(100*cat[c]/N) - round(100*mc.get(c,0)/mtot)

cats=sorted(cat, key=lambda c: cat[c])       # asc -> biggest on top in barh

# ============ VARIANT A: minimalist stacked by source ============
order=["Холодные","Горячие","Ивент/контент"]
COL={"Холодные":"#6f9be8","Горячие":"#ec9393","Ивент/контент":"#efc94c"}
fig,ax=plt.subplots(figsize=(10.5,6))
y=range(len(cats)); left=[0]*len(cats)
for si,src in enumerate(order):
    vals=[ct[c][src] for c in cats]
    ax.barh(list(y),vals,left=left,color=COL[src],height=0.6,zorder=3)
    for i,(v,l) in enumerate(zip(vals,left)):
        if v>=2: ax.text(l+v/2,i,str(v),va="center",ha="center",fontsize=9,color="white",fontweight="bold",zorder=4)
        # label source names on the top (largest) bar only
    left=[l+v for l,v in zip(left,vals)]
for i,c in enumerate(cats):
    t=cat[c]
    ax.text(t+0.35,i,f"{t}",va="center",ha="left",fontsize=11,fontweight="bold",color="#222")
    ax.text(t+1.15,i,f"{round(100*t/N)}%",va="center",ha="left",fontsize=9.5,color="#9a9a9a")
# direct source labels above the top bar
top=len(cats)-1; l=0
for src in order:
    v=ct[cats[top]][src]
    if v>0:
        ax.text(l+v/2, top+0.46, src, ha="center", va="bottom", fontsize=8.5, color=COL[src], fontweight="bold")
    l+=v
ax.set_yticks(list(y)); ax.set_yticklabels([lbl(c) for c in cats],fontsize=10.5,color="#333")
ax.set_xlim(0,17); ax.set_xticks([]); ax.tick_params(left=False)
for s in ax.spines.values(): s.set_visible(False)
ax.set_title("Причины проигрыша · Midmarket · июнь 2026",fontsize=14,fontweight="bold",color="#222",loc="left",pad=24)
ax.annotate("60 сделок · 7 дублей исключены · 1 на ручной проверке",(0,1.02),xycoords="axes fraction",fontsize=9.5,color="#9a9a9a")
plt.tight_layout(); plt.savefig("output/june_2026_chart_v2a.png",dpi=150,bbox_inches="tight"); plt.close()

# ============ VARIANT B: shares + delta vs May, muted tail ============
fig,ax=plt.subplots(figsize=(10.5,6))
top3=set(sorted(cat,key=lambda c:-cat[c])[:3])
for i,c in enumerate(cats):
    v=cat[c]; color="#3b6fd4" if c in top3 else "#c2cfe6"
    ax.plot([0,v],[i,i],lw=15,solid_capstyle="round",color=color,zorder=3)
    # count + %
    ax.text(v+0.35,i,f"{v}",va="center",ha="left",fontsize=11,fontweight="bold",color="#222")
    ax.text(v+1.15,i,f"{round(100*v/N)}%",va="center",ha="left",fontsize=9.5,color="#9a9a9a")
    # delta vs may
    d=delta_pp(c)
    if d>0: dt,dc=f"▲ +{d}","#c0392b"
    elif d<0: dt,dc=f"▼ {d}","#27ae60"
    else: dt,dc="= 0","#9a9a9a"
    ax.text(v+2.4,i,dt,va="center",ha="left",fontsize=9,color=dc,fontweight="bold")
ax.set_yticks(range(len(cats))); ax.set_yticklabels([lbl(c) for c in cats],fontsize=10.5,color="#333")
ax.set_xlim(0,18); ax.set_xticks([]); ax.tick_params(left=False)
for s in ax.spines.values(): s.set_visible(False)
ax.set_title("Причины проигрыша · Midmarket · июнь 2026",fontsize=14,fontweight="bold",color="#222",loc="left",pad=24)
ax.annotate("60 сделок · доля от всех · ▲▼ п.п. к маю",(0,1.02),xycoords="axes fraction",fontsize=9.5,color="#9a9a9a")
# insight annotation: not-our-segment
ss=cat["SS"]+cat["Нецелевой"]
ax.annotate(f"«Не наш сегмент» (SS + Нецелевой): {ss} · {round(100*ss/N)}%",
            (0,-0.06),xycoords="axes fraction",fontsize=9.5,color="#3b6fd4",fontweight="bold")
plt.tight_layout(); plt.savefig("output/june_2026_chart_v2b.png",dpi=150,bbox_inches="tight"); plt.close()
print("saved v2a and v2b")

# ============ VARIANT C: stacked-by-source + rounded ends + MoM delta ============
def variant_c():
    fig,ax=plt.subplots(figsize=(11.5,6))
    LW=16
    for i,c in enumerate(cats):
        segs=[(s,ct[c][s]) for s in order if ct[c][s]>0]
        t=cat[c]
        # rounded end caps (drawn first, behind): left=first seg color, right=last seg color
        ax.plot(0,i,marker="o",markersize=LW,color=COL[segs[0][0]],zorder=2,markeredgewidth=0)
        ax.plot(t,i,marker="o",markersize=LW,color=COL[segs[-1][0]],zorder=2,markeredgewidth=0)
        left=0
        for s,v in segs:
            ax.plot([left,left+v],[i,i],lw=LW,solid_capstyle="butt",color=COL[s],zorder=3)
            if v>=2: ax.text(left+v/2,i,str(v),va="center",ha="center",fontsize=9,color="white",fontweight="bold",zorder=4)
            left+=v
        # total + %
        ax.text(t+0.5,i,f"{t}",va="center",ha="left",fontsize=11,fontweight="bold",color="#222",zorder=4)
        ax.text(t+1.5,i,f"{round(100*t/N)}%",va="center",ha="left",fontsize=9.5,color="#9a9a9a",zorder=4)
        # delta
        d=delta_pp(c)
        if d>0: dt,dc=f"▲ +{d}","#c0392b"
        elif d<0: dt,dc=f"▼ {d}","#27ae60"
        else: dt,dc="= 0","#9a9a9a"
        ax.text(t+3.0,i,dt,va="center",ha="left",fontsize=9,color=dc,fontweight="bold",zorder=4)
    # inline source labels above top bar
    top=len(cats)-1; l=0
    for s in order:
        v=ct[cats[top]][s]
        if v>0: ax.text(l+v/2,top+0.5,s,ha="center",va="bottom",fontsize=8.5,color=COL[s],fontweight="bold")
        l+=v
    ax.set_yticks(range(len(cats))); ax.set_yticklabels([lbl(c) for c in cats],fontsize=10.5,color="#333")
    ax.set_ylim(-0.6,len(cats)-0.1); ax.set_xlim(-0.5,20); ax.set_xticks([]); ax.tick_params(left=False)
    for s in ax.spines.values(): s.set_visible(False)
    ax.set_title("Причины проигрыша · Midmarket · июнь 2026",fontsize=14,fontweight="bold",color="#222",loc="left",pad=26)
    ax.annotate("60 сделок · стек по источнику · ▲▼ п.п. к маю",(0,1.03),xycoords="axes fraction",fontsize=9.5,color="#9a9a9a")
    plt.tight_layout(); plt.savefig("output/june_2026_chart_v2c.png",dpi=150,bbox_inches="tight"); plt.close()
    print("saved v2c")
variant_c()
