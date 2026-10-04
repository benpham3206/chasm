from pathlib import Path
import re
p=Path('ref/reviews/alexotos-evo75.en.vtt')
s=p.read_text(encoding='utf-8-sig')
# Remove VTT header, timestamps and markup; select the longest rolling-caption variant per cue.
blocks=[]
for b in re.split(r'\n\s*\n',s):
 lines=[x.strip() for x in b.splitlines() if x.strip() and '-->' not in x and not x.strip().isdigit() and not x.startswith(('WEBVTT','Kind:','Language:'))]
 if lines:
  t=max(lines,key=len)
  t=re.sub(r'<[^>]+>','',t).strip()
  if blocks and blocks[-1] in t: blocks[-1]=t
  elif not blocks or t not in blocks[-1]: blocks.append(t)
text=' '.join(blocks)
Path('ref/reviews/alexotos-evo75-transcript.txt').write_text(text+'\n',encoding='utf-8')
