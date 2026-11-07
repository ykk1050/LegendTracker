import json, re, urllib.request, os
H={"User-Agent":"Mozilla/5.0 (Windows NT 10.0; Win64; x64) personal-apt-tracker","Referer":"https://hogangnono.com/apt/aNmbc","Accept":"application/json, text/html, */*"}
os.makedirs("out",exist_ok=True)
def get(u):
    try:
        with urllib.request.urlopen(urllib.request.Request(u,headers=H),timeout=30) as r: return r.status, r.read()
    except Exception as e: return getattr(e,"code","ERR"), str(e).encode()
log=open("out/log.txt","w")
for path in ["/api/v2/apts/aNmbc","/api/v2/apts/aNmbc/areas","/api/v2/apts/aNmbc/floor-plans","/api/v2/apts/aNmbc/floorplans","/api/v2/apts/aNmbc/area-infos","/api/v2/apts/aNmbc/detail","/api/v2/apts/aNmbc/plans","/api/apt/aNmbc","/api/v2/apts/aNmbc/pyeongs","/api/v2/apts/aNmbc/area/9","/api/v2/apts/aNmbc/areas/9"]:
    st,b=get("https://hogangnono.com"+path); log.write(f"{st} {path} {len(b)}\n")
    open("out/"+path.strip("/").replace("/","_")+".txt","wb").write(b[:400000])
st,html=get("https://hogangnono.com/apt/aNmbc/0/9"); open("out/page.html","wb").write(html); log.write(f"page {st} {len(html)}\n")
js=set(re.findall(rb'src="([^"]+\.js)"',html)); log.write(repr(js)+"\n")
hits=[]
for j in js:
    u=j.decode(); u=u if u.startswith("http") else "https://hogangnono.com"+u
    st,b=get(u)
    for m in re.finditer(rb'.{0,120}(floor[-_]?plan|floorPlan|planImage|/plans?|unitPlan|areaImage|pyeongImage).{0,160}',b,re.I):
        hits.append(u+" :: "+m.group(0).decode("utf8","replace"))
open("out/jshits.txt","w").write("\n".join(hits[:400]))
