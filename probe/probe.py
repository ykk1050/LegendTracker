import urllib.request, urllib.parse, json
q='''[out:json][timeout:60];
(way["building"](around:450,35.1363417,129.0811443);
 relation["building"](around:450,35.1363417,129.0811443););
out geom tags;'''
for ep in ["https://overpass-api.de/api/interpreter","https://overpass.kumi.systems/api/interpreter"]:
    try:
        req=urllib.request.Request(ep,data=urllib.parse.urlencode({"data":q}).encode(),headers={"User-Agent":"LegendTracker/1.0 (personal)"})
        with urllib.request.urlopen(req,timeout=90) as r: d=json.load(r)
        open("out/osm.json","w").write(json.dumps(d,ensure_ascii=False)); print(ep,"ok",len(d["elements"])); break
    except Exception as e: print(ep,"ERR",e)
