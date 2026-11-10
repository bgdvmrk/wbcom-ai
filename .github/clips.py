#!/usr/bin/env python3
"""GitHub Action: новые ролики @communitywb из RSS → clips.json (страницы спикеров подгружают его сами).
Привязка: ссылка ai.wbcom.ru/s/<id> в описании → иначе полное имя спикера в названии или описании."""
import json, re, urllib.request
import xml.etree.ElementTree as ET

FEED = "https://www.youtube.com/feeds/videos.xml?channel_id=UCW3MI9q73ygLwcaAQ26YSug"
NS = {"a": "http://www.w3.org/2005/Atom", "yt": "http://www.youtube.com/xml/schemas/2015", "m": "http://search.yahoo.com/mrss/"}
norm = lambda x: re.sub(r"\s+", " ", x.replace("ё", "е").replace("Ё", "Е")).lower()

data = json.load(open("clips.json", encoding="utf-8"))
names, spk = data["names"], data["speakers"]
known = {c["yt"] for v in spk.values() for c in v}
req = urllib.request.Request(FEED, headers={"User-Agent": "wbcom-kb-clips"})
root = ET.fromstring(urllib.request.urlopen(req, timeout=60).read())
added = 0
for en in root.findall("a:entry", NS):
    vid = en.findtext("yt:videoId", namespaces=NS)
    if not vid or vid in known:
        continue
    title = en.findtext("a:title", namespaces=NS) or ""
    desc = en.findtext("m:group/m:description", namespaces=NS) or ""
    pub = (en.findtext("a:published", namespaces=NS) or "")[:10]
    sids = set(re.findall(r"ai\.wbcom\.ru/s/([a-z0-9-]+)", desc)) & set(names)
    if not sids:
        hay = norm(title + " " + desc)
        for sid, n in names.items():
            n = norm(re.sub(r"\(.*?\)", "", n)).strip()
            if len(n.split()) >= 2 and re.search(r"(?<!\w)" + re.escape(n) + r"(?!\w)", hay):
                sids.add(sid)
    for sid in sids:
        spk.setdefault(sid, []).insert(0, {"yt": vid, "title": title, "published": pub})
        added += 1
for v in spk.values():
    v.sort(key=lambda c: c["published"], reverse=True)
json.dump(data, open("clips.json", "w", encoding="utf-8"), ensure_ascii=False)
print("добавлено:", added)
