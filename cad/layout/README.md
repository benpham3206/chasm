# Layout

Duo-style split Alice + right B, no left Fn, 68 keys. Source of truth for plate, PCB and case.

```
python cad/layout/build_layout.py --angle 8     # or 12
python cad/layout/check_layout.py 8 12          # overlaps, tight gaps, KLE round-trip
```

| Output (`out/`) | Use |
|---|---|
| `keys_<a>.json` | CAD input: per key `x_mm, y_mm` (per half, y up, origin = key-area centre), `rot_deg`, `w_u`, `stab` |
| `kle_<a>.json` | Paste into keyboard-layout-editor.com raw data; ai03 plate generator; kbplacer |
| `preview_<a>.png` | Review |
| `print_<a>.pdf` | 1:1 paper test, page 1 = L, page 2 = R, US Letter landscape (fits A4). Print at "Actual size", check 50 mm bar |

Key area at 8°: L 172 × 107 mm, R 194 × 108 mm (arrows 1u right for the right B). Duo case 188 × 118 mm per half.

## Geometry provenance

| Item | Source |
|---|---|
| Row staggers, block placement | TeaQueen PCB (MIT, github.com/gregandcin/teaqueen); 12° output matches its footprints, median 0.000 mm |
| Key set | QK Alice Duo plate photo (qwertykeys.com extra parts): macro column, arrows, split space |
| 8° | Measured on that photo: outer vs inner block cutouts (L 1.5° vs −6.3°, R 0° vs 8.1°) |
| 12° | TGR Alice / TeaQueen / OpenErgo |

## Phase 1 test (A3)

1. Print `print_8.pdf` and `print_12.pdf` at "Actual size" (not "Fit"); verify the 50 mm bar.
2. Tape halves to desk at a comfortable split; place owned XRAY caps on the outlines.
3. Type real text on the paper (or 3D-print a plate from `keys_*.json` + Y2 switches).
4. Log in journal: reach to B/6/Y/N, thumb on both spaces, arrows, macro column.
5. Lock angle → `docs/decisions/`. **Done 2026-10-01: 8°.**
