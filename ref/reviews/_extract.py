import re, html, pathlib, json
p=pathlib.Path('ref/reviews/alexotos-evo75.en.vtt')
s=p.read_text(encoding='utf-8-sig')
lines=[]
for line in s.splitlines():
    line=line.strip()
    if not line or line=='WEBVTT' or line.startswith(('Kind:','Language:','NOTE')) or '-->' in line or re.fullmatch(r'\d+',line): continue
    line=re.sub(r'<[^>]*>','',line)
    line=html.unescape(line).strip()
    if line and (not lines or lines[-1]!=line): lines.append(line)
out=[]
for line in lines:
    if out and line.startswith(out[-1]):
        out[-1]=line
    elif out and out[-1].startswith(line):
        continue
    else: out.append(line)
pathlib.Path('ref/reviews/alexotos-evo75-transcript.txt').write_text(' '.join(out)+'\n',encoding='utf-8')
htmltext=pathlib.Path('ref/reviews/_neo75.html').read_text(encoding='utf-8')
# print image refs in date's article namespace
for m in re.finditer(r'https?://[^\"\']+?\.(?:webp|jpg|jpeg|png)',htmltext):
 u=m.group(0).replace('&amp;','&')
 if '/2025/12/' in u: print(u)
