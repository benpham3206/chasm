Add-Type -AssemblyName System.Drawing
$root = Split-Path -Parent $PSScriptRoot
$src = Join-Path $root 'renders/stills/v2/draft'
$out = Join-Path $root 'renders/review/v2_contact.jpg'
$names = @('01_hero','02_top','03_plinth','04_macro_legends','05_macro_detail','06_hub','06b_hub_ports','07_exploded')
$cellW = 360; $cellH = 450; $pad = 12; $labelH = 28; $cols = 3; $rows = 3
$bitmap = [System.Drawing.Bitmap]::new($cols*$cellW+($cols+1)*$pad,$rows*($cellH+$labelH)+($rows+1)*$pad)
$graphics = [System.Drawing.Graphics]::FromImage($bitmap)
$graphics.Clear([System.Drawing.Color]::FromArgb(24,24,26))
$graphics.InterpolationMode = [System.Drawing.Drawing2D.InterpolationMode]::HighQualityBicubic
$font = [System.Drawing.Font]::new('Segoe UI',12)
$brush = [System.Drawing.SolidBrush]::new([System.Drawing.Color]::FromArgb(220,220,220))
for ($i=0; $i -lt $names.Count; $i++) {
    $x = $pad+($i%$cols)*($cellW+$pad)
    $y = $pad+[math]::Floor($i/$cols)*($cellH+$labelH+$pad)
    $path = Join-Path $src ($names[$i]+'.png')
    if (Test-Path -LiteralPath $path) {
        $frame = [System.Drawing.Image]::FromFile($path)
        $graphics.DrawImage($frame,[int]$x,[int]$y,$cellW,$cellH)
        $frame.Dispose()
    }
    $graphics.DrawString($names[$i].Replace('_',' '),$font,$brush,[single]($x+4),[single]($y+$cellH+4))
}
$bitmap.Save($out,[System.Drawing.Imaging.ImageFormat]::Jpeg)
$graphics.Dispose(); $bitmap.Dispose(); $font.Dispose(); $brush.Dispose()
Write-Output "wrote $out"
