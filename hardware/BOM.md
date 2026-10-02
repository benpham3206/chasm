# Project Alice — BOM v0.1

*2026-09-29, from `roadmap-and-specs-v0.1.md`. ~68 keys; finalize after Phase 1 layout. Budget $450-500 self-build; validate Phase 3.*

Status: **locked** · **proposed** · **owned** · **TBD** (Phase 3)

Owned: XRAY base kit + 50x Y2 (~$140-170).

## Switches, caps, stabilizers

| Qty | Part | Status | Notes |
|---|---|---|---|
| 80 | Keygeek Y2 linear, 48g/53g, 5-pin | 50 owned | Buy ~35-pack after layout; factory lubed, UPE waffle stem, PA12 |
| 1 kit | PBTFans XRAY base, Cherry, clear/white ABS | owned | modmusings design; double-shot |
| 1 kit | PBTFans XRAY spacebars | owned | 2u + 2.75u used; covers layout (2026-10-01) |
| 70 | Kailh hot-swap sockets | proposed | Fallback: solder-only |
| 8 sets | Stabilizers, 2u | TBD | Screw-in vs clip-in with plate design |

## Plate and mounting

| Qty | Part | Status | Notes |
|---|---|---|---|
| 2 | PP plate, one per half | locked | No flex cuts rev 1 |
| 1 sheet | Poron/EVA foam | locked (form TBD) | Perimeter strips; form per Phase 2 |

## Case and mechanical

| Qty | Part | Status | Notes |
|---|---|---|---|
| 1 | CNC acrylic case set, frosted, 2 halves | locked | Clear polished window over weight |
| 2 | Bottom weight, brass or stainless, engraved | proposed | Clear of antenna keepout; never touches LiPo |
| 8 | Spring ball plungers | locked | Prototype catch alone; acrylic ±10% |
| 1 set | Screws/standoffs, weight + PCB | TBD | Phase 2 CAD |

## Boards

| Qty | Part | Status | Notes |
|---|---|---|---|
| 2 | Custom PCB, central + peripheral, white mask | locked (color) | JLCPCB 2-layer; PCBA vs hand-solder Phase 3 |

## Electronics — central (→ dongle hub, 2026-10-01; own board + enclosure)

| Qty | Part | Status | Notes |
|---|---|---|---|
| 1 | nRF52840 RF module w/ USB pins (E73-2G4M08S1C / MDBT50Q) | locked | Was bare chip; RF modules do break out D+/D- (decision 2026-10-01) |
| 1 | USB 2.0 hub IC | TBD | Wired only, host 5V |
| 1 | OLED 128x64, SSD1306 | proposed | 15-25 mA lit, 30 s sleep |
| 1 | EC11 encoder + knob | locked | Position TBD (left macro column candidate → moves to a half) |
| 3 | USB-C, 16-pin mid-mount | locked (count) | 1 upstream (CC pull-downs), 2 downstream @ 500 mA |
| 1 | LiPo charger IC | locked (type TBD) | MCP73831 class |
| 1 | 3.3V reg + power path | TBD | Budget hub + MCU + OLED + LEDs + charge < upstream |
| ~8 | Side-view addressable LEDs, SK6812/WS2812B | proposed | Count per Phase 2 test strip; off/dim on battery |
| 1 lot | Diodes, R, C, crystals | TBD | Phase 4; 1N4148-class |

## Electronics — peripheral (×2 halves, 2026-10-01)

| Qty | Part | Status | Notes |
|---|---|---|---|
| 1 | nRF52840 RF module, same as dongle (looks; 2026-10-01) | proposed | nice!nano class still possible; RF module needs own charger + USB-C routing |
| 1 | USB-C | locked | Charge + flash |
| 1 | LiPo charger IC | locked (type TBD) | Same as central |
| 1 | 3.3V reg | TBD | Phase 3 |
| ~8 | Side-view addressable LEDs | proposed | Same policy |
| 1 lot | Diodes, passives | TBD | Phase 4 |

## Power

| Qty | Part | Status | Notes |
|---|---|---|---|
| 2 | LiPo, 1000-1500 mAh | locked (spec) | Fit stack; own pocket, no compression |
| 2 | LiPo PCM | locked | Usually in cell; verify |
| 2 | Leads + JST | TBD | Match footprint Phase 4 |

## Deferred to rev 2

- Tenting hinges (⚠ conflicts with roadmap §4: tenting in scope, legs vs hinges open)
- Fuel-gauge IC
- Per-key RGB (XRAY not shine-through)
- Display clock/weather

## Resolve before ordering

| # | Item | Status |
|---|---|---|
| 1 | Firmware | LOCKED: ZMK |
| 2 | Hot-swap vs solder-only | Open |
| 3 | Inter-half link: USB-C vs pogo | LOCKED: BLE only rev 1 |
| 4 | Brass vs stainless weight | Open |
| 5 | Exact Alice layout | Key set LOCKED (Duo-style 68); angle 8° vs 12° → Phase 1 (`cad/layout/`) |
