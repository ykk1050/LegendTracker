import urllib.request, os
os.makedirs("out/plans2",exist_ok=True)
U={"58":"","74":"258649/20260210163906_HOAR6NZkoApKJDeikd","83A":"106771/20210508043408_Q1D6vQgAWqU7CANtxe","84C":"106773/20210508043410_RMIhAfRUU9yFLnIW36","84B":"106772/20210508043409_AtfHSszRojL8wETE7u","85D":"106774/20210508043411_tEVfDiwtyTq2FNviYH","130B":"106779/20210508043414_7YZUwk6ZiQxUMuqT1h","153A":"106780/20210508043415_jbdzzgxUcbyT2y3SkY","154B":"106781/20210508043416_QXwcsO0GpOhBA5Jz2l"}
for t,p in U.items():
    if not p: continue
    u="https://image.hogangnono.com/image/original/apt/aNmbc/"+p+"?s=720x180&t=outside&q=100"
    try:
        with urllib.request.urlopen(urllib.request.Request(u,headers={"User-Agent":"Mozilla/5.0"}),timeout=30) as r:
            open(f"out/plans2/{t}.jpg","wb").write(r.read()); print(t,"ok")
    except Exception as e: print(t,"ERR",e)
