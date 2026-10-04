$ErrorActionPreference='Stop'
$urls=@(
'https://www.alexotos.com/wp-content/uploads/2025/12/neo75-neo98_4589.webp',
'https://www.alexotos.com/wp-content/uploads/2025/12/neo75-neo98_4564.webp',
'https://www.alexotos.com/wp-content/uploads/2025/12/DSCF0536.webp',
'https://www.alexotos.com/wp-content/uploads/2025/12/DSCF0539.webp',
'https://www.alexotos.com/wp-content/uploads/2025/12/DSCF0540.webp',
'https://www.alexotos.com/wp-content/uploads/2025/12/DSCF0532.webp',
'https://www.alexotos.com/wp-content/uploads/2025/12/DSCF0549.webp',
'https://www.alexotos.com/wp-content/uploads/2025/12/DSCF0530.webp',
'https://www.alexotos.com/wp-content/uploads/2025/12/neo75-neo98_4574.webp',
'https://www.alexotos.com/wp-content/uploads/2025/12/neo75-neo98_4579.webp'
)
$i=1
foreach($u in $urls){$name=('{0:D2}_' -f $i)+([IO.Path]::GetFileName(([uri]$u).AbsolutePath)); try {Invoke-WebRequest -Uri $u -OutFile (Join-Path 'ref/reviews/neo75-img' $name) -UseBasicParsing; "$name`t$u"} catch {"FAILED $u : $_"}; $i++}
