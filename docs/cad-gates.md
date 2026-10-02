# Pre-CAD gates

*2026-10-01. What must be final before Blender (shape) and SolidWorks (engineering). Workflow: Blender shape → SolidWorks → Blender final.*

Rule: Blender exchanges **numbers** (`design.json`), never meshes; SolidWorks can't edit Blender geometry.

## Gate A — before Blender blockout

| # | Item | Status | Source / next step |
|---|---|---|---|
| A1 | Key set: Duo-style + right B, no left Fn = 68 | **Locked 2026-10-01** | `decisions/2026-10-01-layout.md` |
| A2 | Layout geometry (staggers, block placement) | Draft | `cad/layout/` — TeaQueen-derived Alice grid; validated vs its PCB (0 mm median) |
| A3 | Cluster angle: **8°** | **Locked 2026-10-01** | Paper test: 8° more comfortable than 12° |
| A4 | Keycap coverage (XRAY base + spacebar kits) | **Covered 2026-10-01** | Checklist below; 2nd B in base-kit R4 extras |
| A4b | Right bottom row: classic Alice `B N M ,` + `. /` | **Locked 2026-10-01** | Arrows 1u right; right key area 193.5 mm |
| A4c | Print scale | **Verified 2026-10-01** | 100 % print: 50 mm bar = 50 mm |
| A5 | Angle method: flat case + angled feet/weight | **Locked 2026-10-01** | `decisions/2026-10-01-angle-method.md`; consequence: front height > Duo 19 mm |
| A6 | Inter-half link: BLE only rev 1 | **Locked 2026-10-01** | `decisions/2026-10-01-inter-half-link.md` |
| A6b | Architecture: dongle hub (Duo-style), both halves BLE peripherals | **Locked 2026-10-01** | `decisions/2026-10-01-dongle-hub.md`; dongle = 3rd enclosure |
| A7 | Ports: 1 USB-C per half on the inner edge; dongle upstream + 2 down | **Locked 2026-10-01** (down count = lean) | Exact edge height after stack-up |
| A8 | OLED on the hub box; **knob on the right half, right of Backspace** (rev 2026-10-02, user); hub has no knob | **Locked** | Logo: gull C, polished stainless inlay, one wing per half at inner edge beside G / H; weights polished stainless |
| A9 | Tenting: flip-out hinged legs | **Locked 2026-10-01** | `decisions/2026-10-01-tenting.md`; hinge part → B3 |
| A9b | Finish: full frost, clear bottom over weights | **Working choice 2026-10-01** | `decisions/2026-10-01-case-finish.md`; lighting open |
| A10 | Stack-up heights | Draft below | Needs A11 parts |

## Gate B — before SolidWorks detail

| # | Item | Status | Next step |
|---|---|---|---|
| B1 | MCU: RF module (E73-2G4M08S1C / MDBT50Q), dongle + halves | **Locked 2026-10-01** | `decisions/2026-10-01-central-mcu.md` |
| B2 | LiPo cell (1000–1500 mAh) exact dims | Open | Pick vendor cell; typical 503450 / 603450 / 803450 |
| B3 | OLED module, EC11, USB-C receptacles, ball plungers, tent hinges | Open | Datasheet dims → `ref/` |
| B4 | Hot-swap vs solder | Open (BOM #2) | Socket adds height below PCB |
| B5 | Stabilizers: plate vs PCB (screw-in), 2u/2.25u/2.75u | Open | PP plate flex favours PCB screw-in |
| B6 | Mount: how PP plate + PCB float (gasket/o-ring/tray) | Open | Drives internal ledges |
| B7 | Case route: single CNC shell vs layered; vendor rules | Open | JLCCNC: inner radii ≥0.5–1 mm, walls ≥1.5–2 mm, no tapped acrylic |
| B8 | Fasteners: through-bolts into weight, insert type | Open | `references/acrylic-weights.md` |

Prototype plates (Phase 1) do **not** wait on any of this: 2D from the layout.

## Keycap coverage (A4)

Layout needs (Cherry profile; row sculpt matters):

| Size | Qty | Keys |
|---|---|---|
| 1u | 56 | alphas, numbers, 2nd B, macro ×4, arrows ×4, Win, … |
| 1.5u | 5 | Tab, Ctrl, \, Alt, Fn (right, ex-Alt) |
| 1.75u | 2 | Caps, R-Shift |
| 2u | 2 | Bksp, L-Space |
| 2.25u | 2 | L-Shift, Enter |
| 2.75u | 1 | R-Space |

Checked against the X-Ray base kit and spacebar kit renders (modmusings), 2026-10-01:

| Need | Kit source | Row |
|---|---|---|
| Bksp 2u | base, main | R1 |
| Tab 1.5u, \ 1.5u | base, main (+ spare \ and 1.5u ← in extras) | R2 |
| Caps 1.75u, Enter 2.25u | base, main (+ 6 × 1.75u, 1 × 2.25u enter extras) | R3 |
| L-Shift 2.25u | base, main | R4 |
| R-Shift 1.75u | base, extras (⇧ 1.75U) | R4 |
| Ctrl, Alt, Fn 1.5u | base, 1.5u bottom row ×4 + 1.5u extras ×4 | R4 |
| L-Space 2u, R-Space 2.75u | spacebar kit (2u, 2.25u, 2.75u, 3u ×2, 6u, 6.25u, 7u) | R4 |
| 1u ×56 | base alphas/numbers, arrows, novelty extras for macro ×4 | — |

All covered, including the 2nd **B** (base kit R4 extras).

## Stack-up draft (A10)

| Layer | mm | Source |
|---|---|---|
| Keycap (Cherry R4–R1) | 8.1–9.4 | profile charts |
| Switch above plate top | ~6.6 | MX body 11.6 − 5.0 below plate; verify Y2 datasheet |
| Plate (PP) | 1.5 (1.2 option) | MX standard 1.5 ±0.1 |
| Plate top → PCB top | 5.0 | MX standard |
| PCB | 1.6 (1.2 flex) | JLCPCB |
| Hot-swap socket below PCB | ~1.8 | verify Kailh CPG151101S11 datasheet |
| Foam slices | 1–3 each | Phase 2 test |
| Battery | 5–8 | cell choice (B2) |
| Weight | ~4 | `references/acrylic-weights.md` |
| Bottom acrylic | 3–4 | |

Rough flat-case thickness: ~22–26 mm before feet. Duo wedge: 19 front / 34 rear. Battery + weight can sit beside each other (stepped cavity) to cut height.
