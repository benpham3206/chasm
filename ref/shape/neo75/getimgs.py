from pathlib import Path
import re,html,urllib.request
s=Path('ref/shape/neo75/page.html').read_text(encoding='utf8')
# all shopify images, use unique urls with best-res original size
pat=r'https?://[^" ]+?\.(?:jpg|jpeg|png|webp)(?:\?[^" ]*)?'
raw=re.findall(pat,s,re.I); urls=[]
for x in raw:
 x=html.unescape(x.replace('\\/','/')).replace('\\u0026','&').replace('&amp;','&')
 x=x.replace('_small.','_2048x.').replace('_800x.','_2048x.').replace('_600x.','_2048x.')
 if 'qwertykeys' in x and x not in urls: urls.append(x)
print('candidate',len(urls))
base=Path('ref/shape/neo75'); entries=[]
for i,u in enumerate(urls,1):
 try:
  with urllib.request.urlopen(urllib.request.Request(u,headers={'User-Agent':'Mozilla/5.0'}),timeout=20) as r:d=r.read(); final=r.geturl()
  p=base/f'{i:02}_{final.split("/")[-1].split("?")[0][:100]}';p.write_bytes(d);entries.append((p.name,final,len(d)))
 except Exception as e: print('fail',i,str(e)[:100])
print('saved',len(entries))
for x in entries: print(*x)
