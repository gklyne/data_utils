dist = 1600
times = (
[ (7, 47)
, (8, 18)
, (14, 14)
, (7, 15)
, (8, 51)
, (3, 40)
])

secs = sum([time[1] for time in times])
mins, secs = (secs // 60, secs % 60)
mins = sum([time[0] for time in times], start=mins)

print(f"time: {mins:d}:{secs:02d}")

pace = (mins*60+secs)*100//dist

print(f"pace: {pace:d}/100m")
