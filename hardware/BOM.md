# Project Alice — Bill of Materials v0.1

*Generated 2026-09-29 from the locked decisions in `roadmap-and-specs-v0.1.md`. Status per line: **locked**, **proposed** (leaning, not signed off), **owned** (Ben already has it), or **TBD** (select in Phase 3). Quantities assume ~68 keys; finalize against the real layout in Phase 1. Budget target: **$450-500 all-in self-build** (Ben, 2026-09-29); validate with real quotes in Phase 3. Already owned: XRAY set + 50x Y2 (~$140-170 value) → the budget now covers everything else comfortably.*

## Switches, caps, stabilizers

| Qty | Part | Status | Notes |
|---|---|---|---|
| 80 | Keygeek Y2 linear, 48g/53g, 5-pin PCB mount | 50 owned | Buy one more ~35-pack after layout is final (68 keys + spares); factory lubed, UPE waffle stem, PA12 housing |
| 1 kit | PBTFans XRAY base kit, Cherry profile, clear/white ABS | owned | Designed by modmusings; double-shot; translucent tops |
| 1 kit | PBTFans XRAY spacebars kit | proposed | Verify Alice spacebar sizes (split bottom row) against kit contents before ordering |
| 70 | Kailh hot-swap sockets | proposed | Not yet confirmed; solder-only is the fallback |
| 8 sets | Stabilizers (2u) | TBD | Screw-in vs clip-in decided with plate design; count covers spacebars, shifts, enter, backspace |

## Plate and mounting

| Qty | Part | Status | Notes |
|---|---|---|---|
| 2 | PP (polypropylene) plate, custom cut, one per half | locked | Soft/flexy; no flex cuts in rev 1 |
| 1 sheet | Poron/EVA foam sheet | locked (form TBD) | Cut into selective perimeter strips, not full sheets; form decided by Phase 2 experiment |

## Case and mechanical

| Qty | Part | Status | Notes |
|---|---|---|---|
| 1 | CNC acrylic case set, frosted, 2 halves | locked | Clear polished window over the weight; bead-blasted or frosted stock |
| 2 | Bottom weight, brass or stainless, engraved | proposed | Brass vs stainless undecided; keep clear of nRF52840 antenna keepout; must never touch the LiPo |
| 8 | Spring ball plungers (ball catch) | locked | Tool-free opening; prototype the catch alone first, acrylic thickness varies ~±10% |
| 1 set | Screws/standoffs for weight + PCB mounting | TBD | Sized in Phase 2 CAD |

## Boards

| Qty | Part | Status | Notes |
|---|---|---|---|
| 2 | Custom PCB, central + peripheral, white soldermask | locked (color) | White matches XRAY theme, visible through clear case; fab JLCPCB 2-layer; get PCBA quote vs hand-solder in Phase 3 |

## Electronics — central half

| Qty | Part | Status | Notes |
|---|---|---|---|
| 1 | Bare nRF52840 on central PCB | proposed | Hub downstream must reach MCU USB D+/D-, which modules don't break out; ZMK locked |
| 1 | USB 2.0 hub controller IC | TBD | Phase 3 shortlist; wired-mode only, tens of mA from host 5V |
| 1 | OLED 128x64, SSD1306 class | proposed | Status display; ~15-25mA lit, firmware auto-sleeps after ~30s idle |
| 1 | Rotary encoder (EC11 class) + knob | locked | On central half, position TBD in layout; ZMK supports encoders |
| 3 | USB-C connectors, 16-pin mid-mount class | locked (count) | 1x upstream to host (CC pull-downs mandatory), 2x downstream accessory ports @ 500mA each |
| 1 | LiPo charger IC | locked (type TBD) | Dedicated charger per half; MCP73831 class shortlisted in Phase 3 |
| 1 | 3.3V regulator + power-path | TBD | Phase 3; wired rail must budget hub + MCU + OLED + LEDs + charging under upstream limit |
| ~16 | Side-view addressable LEDs (SK6812/WS2812B class) | proposed | ~8 per half; count/placement set by Phase 2 diffusion test strip; wired-mode full effects, off/dim on battery |
| 1 lot | Matrix diodes, resistors, capacitors, crystals | TBD | Per schematic in Phase 4; 1N4148-class diodes for the key matrix |

## Electronics — peripheral half

| Qty | Part | Status | Notes |
|---|---|---|---|
| 1 | nRF52840 module, nice!nano v2 class (~$25-30) | proposed | Peripheral half only — no hub there, so a module is fine |
| 1 | USB-C connector | locked | Charging + flashing only |
| 1 | LiPo charger IC | locked (type TBD) | Same as central |
| 1 | 3.3V regulator | TBD | Phase 3 |
| ~8 | Side-view addressable LEDs | proposed | Same policy as central |
| 1 lot | Matrix diodes, passives | TBD | Phase 4 |

## Power

| Qty | Part | Status | Notes |
|---|---|---|---|
| 2 | LiPo cell, 1000-1500mAh, one per half | locked (spec) | Exact dimensions must fit the case stack; dedicated pocket, clearance from weight, no sharp edges, no compression |
| 2 | LiPo protection (PCM) | locked | Usually integrated in the cell; verify when sourcing |
| 2 | Battery leads + JST connectors | TBD | Matched to charger IC / PCB footprint in Phase 4 |

## Explicitly deferred to rev 2

- Tenting hinges (flat bottoms for rev 1)
- Dedicated fuel-gauge IC (voltage-divider ADC is fine for rev 1)
- Per-key RGB shine-through (XRAY caps aren't designed for it; underglow only)
- Host widgets on the display: clock, weather (needs companion app + RTC)

## To resolve before ordering anything (Phase 0/1)

1. Firmware: ZMK vs QMK/VIA (drives MCU/module choice)
2. Hot-swap: yes or solder-only (affects PCB footprint)
3. Inter-half wired link: USB-C cable vs pogo/magnetic (affects both PCBs)
4. Brass vs stainless weight
5. Exact Alice layout (sets switch/socket/stab counts and spacebar sizes)
