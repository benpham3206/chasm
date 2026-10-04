import urllib.request,pathlib
urls=[
'https://www.alexotos.com/wp-content/uploads/2025/12/neo75-neo98_4589.webp',
'https://www.alexotos.com/wp-content/uploads/2025/12/neo75-neo98_4564.webp',
'https://www.alexotos.com/wp-content/uploads/2025/12/DSCF0536.webp',
'https://www.alexotos.com/wp-content/uploads/2025/12/DSCF0539.webp',
'https://www.alexotos.com/wp-content/uploads/2025/12/DSCF0540.webp',
'https://www.alexotos.com/wp-content/uploads/2025/12/DSCF0532.webp',
'https://www.alexotos.com/wp-content/uploads/2025/12/DSCF0549.webp',
'https://www.alexotos.com/wp-content/uploads/2025/12/DSCF0530.webp',
'https://www.alexotos.com/wp-content/uploads/2025/12/neo75-neo98_4574.webp',
'https://www.alexotos.com/wp-content/uploads/2025/12/neo75-neo98_4579.webp']
out=pathlib.Path('ref/reviews/neo75-img'); out.mkdir(exist_ok=True)
for i,u in enumerate(urls,1):
 p=out/f'{i:02d}_{u.rsplit("/",1)[-1]}'
 req=urllib.request.Request(u,headers={'User-Agent':'Mozilla/5.0'})
 with urllib.request.urlopen(req,timeout=30) as r: p.write_bytes(r.read())
 print(p.name,p.stat().st_size)
