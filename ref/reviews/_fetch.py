# Try python urllib direct and report response
import urllib.request
u='https://www.alexotos.com/wp-content/uploads/2025/12/neo75-neo98_4589.webp'
r=urllib.request.urlopen(urllib.request.Request(u,headers={'User-Agent':'Mozilla/5.0'}),timeout=20)
print(r.status,r.headers.get('Content-Type'),r.headers.get('Content-Length'))
open('ref/reviews/neo75-img/test.webp','wb').write(r.read())
