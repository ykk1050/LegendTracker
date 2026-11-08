import urllib.request, json, re, os
os.makedirs("out/nv",exist_ok=True)
UA="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0 Safari/537.36"
def get(u,ref="https://fin.land.naver.com/complexes/109359",extra=None):
    h={"User-Agent":UA,"Referer":ref,"Accept":"application/json, text/plain, */*","Accept-Language":"ko-KR,ko;q=0.9"}
    if extra: h.update(extra)
    try:
        with urllib.request.urlopen(urllib.request.Request(u,headers=h),timeout=30) as r: return r.status,r.read()
    except Exception as e: return getattr(e,"code","ERR"),(getattr(e,"read",lambda:b"")() or str(e).encode())
log=open("out/nv/log.txt","w")
st,html=get("https://fin.land.naver.com/complexes/109359?tab=complex-info&transactionPyeongTypeNumber=6")
open("out/nv/page.html","wb").write(html); log.write(f"page {st} {len(html)}\n")
cands=["https://fin.land.naver.com/front-api/v1/complex?complexNumber=109359",
"https://fin.land.naver.com/front-api/v1/complex/pyeongList?complexNumber=109359",
"https://fin.land.naver.com/front-api/v1/complex/pyeong?complexNumber=109359&pyeongTypeNumber=6",
"https://fin.land.naver.com/front-api/v1/complex/pyeongTypes?complexNumber=109359",
"https://fin.land.naver.com/front-api/v1/complex/floorPlan?complexNumber=109359&pyeongTypeNumber=6",
"https://new.land.naver.com/api/complexes/109359?sameAddressGroup=false"]
for u in cands:
    st,b=get(u); log.write(f"{st} {u} {len(b)} {b[:200]!r}\n")
    open("out/nv/"+re.sub(r'\W+','_',u.split('naver.com/')[1])[:80]+".txt","wb").write(b[:300000])
js=set(re.findall(rb'(?:src|href)="([^"]+\.js)"',html)); log.write(repr(list(js))[:3000]+"\n")
hits=set()
for j in js:
    u=j.decode(); u=u if u.startswith("http") else "https://fin.land.naver.com"+u
    st,b=get(u)
    for m in re.finditer(rb'["`](/front-api/v1/[A-Za-z0-9/_\-]+)',b): hits.add(m.group(1).decode())
open("out/nv/endpoints.txt","w").write("\n".join(sorted(hits)))
