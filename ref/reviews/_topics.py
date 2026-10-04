import pathlib,re
s=pathlib.Path('ref/reviews/alexotos-evo75.en.vtt').read_text(encoding='utf-8-sig')
blocks=s.split('\n\n')
for b in blocks:
 lines=[x for x in b.splitlines() if x.strip() and '-->' not in x and not x.strip().isdigit() and not x.startswith(('WEBVTT','Kind:','Language:'))]
 t=' '.join(re.sub(r'<[^>]+>','',x) for x in lines).strip()
 if re.search(r'plate|gasket|mount|curve|side profile|height|foam|sound|feel|flex|case|Evo 75|Evo75',t,re.I):
  print(t[:650])
