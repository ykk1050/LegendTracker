import json, urllib.request, os
os.makedirs("out",exist_ok=True)
H={"User-Agent":"Mozilla/5.0 personal-apt-tracker","Referer":"https://hogangnono.com/apt/aNmbc"}
out={}
def get(u):
    try:
        with urllib.request.urlopen(urllib.request.Request("https://hogangnono.com"+u,headers=H),timeout=30) as r: return json.load(r)
    except Exception as e: return {"error":str(e)}
det=get("/api/v2/item-catalogs/18906563?tradeType=0&offset=0&limit=20")
out["detail"]=det
d=det.get("data",det)
items=d.get("items") or []
if items:
    iid=items[0].get("itemId")
    for p in [f"/api/v2/items/{iid}", f"/api/v2/item/{iid}", f"/api/v2/items/{iid}/detail", f"/api/v2/item-catalogs/items/{iid}"]:
        out[p]=get(p)
json.dump(out,open("out/item.json","w"),ensure_ascii=False,indent=1)
