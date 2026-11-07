import urllib.request, os
os.makedirs("out/plans",exist_ok=True)
U={"110C":"106777/20210508043412_HhPSidW14V465sMxuW","112D":"106778/20210508043413_FqetAugaHPZOnqhNEN","113A":"106775/20210508043411_phglGLrW6s02R7sop8","113B":"106776/20190725001654_H00bqankHRtj5Mu0WW"}
log=open("out/plans/log.txt","w")
for t,p in U.items():
    u="https://image.hogangnono.com/image/original/apt/aNmbc/"+p
    for name,h in [("noref",{"User-Agent":"Mozilla/5.0"}),("ref",{"User-Agent":"Mozilla/5.0","Referer":"https://hogangnono.com/"})]:
        try:
            with urllib.request.urlopen(urllib.request.Request(u,headers=h),timeout=30) as r:
                b=r.read(); log.write(f"{t} {name} {r.status} {r.headers.get('content-type')} {len(b)}\n")
                if name=="noref": open(f"out/plans/{t}.img","wb").write(b)
        except Exception as e: log.write(f"{t} {name} ERR {e}\n")
