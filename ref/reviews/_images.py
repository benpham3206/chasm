import re, pathlib, json, html
s=pathlib.Path('ref/reviews/_neo75.html').read_text(encoding='utf-8-sig')
seen=set()
for m in re.finditer(r"https?://[^\"' <>]+?\.(?:webp|jpg|jpeg|png)",s):
 u=html.unescape(m.group(0))
 if '/2025/12/' not in u or u in seen: continue
 seen.add(u)
 sn=s[max(0,m.start()-400):min(len(s),m.end()+250)]
 alts=re.findall(r'alt=[\"\']([^\"\']*)',sn)
 print(json.dumps({'url':u,'alts':alts[-4:]}))
