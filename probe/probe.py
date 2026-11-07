import urllib.request
u="https://image.hogangnono.com/image/original/apt/aNmbc/106777/20210508043412_HhPSidW14V465sMxuW"
for q in ["","?s=1000x750&t=inside&q=85","?s=1000x750&t=outside&q=85","?s=720x180&t=outside&q=100","?w=1000"]:
    try:
        with urllib.request.urlopen(urllib.request.Request(u+q,headers={"User-Agent":"Mozilla/5.0"}),timeout=30) as r:
            b=r.read(); print(repr(q), r.status, r.headers.get("content-type"), len(b), r.headers.get("access-control-allow-origin"))
    except Exception as e: print(q,"ERR",e)
