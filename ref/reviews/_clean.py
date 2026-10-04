import pathlib,re,html
s=pathlib.Path('ref/reviews/alexotos-evo75.en.vtt').read_text(encoding='utf-8-sig')
blocks=[]
for b in s.split('\n\n'):
 lines=[x.strip() for x in b.splitlines() if x.strip() and '-->' not in x and not x.strip().isdigit() and not x.startswith(('WEBVTT','Kind:','Language:'))]
 if not lines: continue
 t=max((re.sub(r'<[^>]+>','',x) for x in lines),key=len)
 t=html.unescape(t).strip()
 if not t: continue
 if blocks and (t==blocks[-1] or t in blocks[-1]): continue
 if blocks and blocks[-1] in t: blocks[-1]=t
 else: blocks.append(t)
text=' '.join(blocks)
text=re.sub(r'\s+',' ',text)
pathlib.Path('ref/reviews/alexotos-evo75-transcript.txt').write_text(text+'\n',encoding='utf-8')
