import json, urllib.request, sys
sys.path.insert(0,'.')
H={"User-Agent":"Mozilla/5.0 personal-apt-tracker","Referer":"https://hogangnono.com/apt/aNmbc"}
def get(u):
    with urllib.request.urlopen(urllib.request.Request("https://hogangnono.com"+u,headers=H),timeout=30) as r: return json.load(r)
out={}
s=get("/api/v2/item-catalogs/summaries?aptHash=aNmbc&isAptDetail=false&offset=0&limit=5")
hid=s["itemCatalogSummaries"][0]["areaHoId"]
out["summary0"]=s["itemCatalogSummaries"][0]
det=get(f"/api/v2/item-catalogs/{hid}?tradeType=0&offset=0&limit=20")
out["detail"]=det
iid=det["items"][0]["itemId"]
for p in [f"/api/v2/items/{iid}", f"/api/v2/item/{iid}", f"/api/v2/items/{iid}/detail"]:
    try: out[p]=get(p)
    except Exception as e: out[p]=str(e)
json.dump(out,open("out/item.json","w"),ensure_ascii=False,indent=1)
