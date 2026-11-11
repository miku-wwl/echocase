import sys,time,urllib.request,urllib.error
for url in sys.argv[1:]:
    for _ in range(90):
        try:
            if urllib.request.urlopen(url,timeout=3).status==200:break
        except (OSError,urllib.error.URLError):pass
        time.sleep(.5)
    else:raise SystemExit('HTTP readiness failed: '+url)
print('HTTP dependencies ready')
