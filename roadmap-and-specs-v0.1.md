# Project Alice — Roadmap & Specs v0.1

*Draft, 2026-09-29. One-and-done split Alice, inspired by QK Alice Duo.*

## 1. Design goals

| Area | Target |
|---|---|
| Feel | Soft, flexy |
| Sound | Deep, muted, thocky |
| Aesthetics | Frosted acrylic, diffused LED glow, metal weight as design piece |
| Customizability | Hot-swap, live remap, open firmware |
| Process | GitHub journal, decisions logged as made |

## 2. Locked decisions

| Area | Decision |
|---|---|
| Layout | Split Alice, 60% ergo, Duo-inspired |
| Switch | Keygeek Y2 linear, 48g/53g, 5-pin, factory lubed, UPE waffle stem, PA12 housing |
| Plate | PP, soft, flex |
| Case | CNC acrylic, frosted, clear polished window over weight (2026-09-29, XRAY theme) |
| Case opening | Ball catch, tool-free |
| Power | LiPo per half, USB-C |
| Hub | Wired USB-C hub, central half |
| Display | Status display, central half |
| Lighting | Diffused underglow through frosted acrylic |
| PCB | White soldermask |
| Knob | 1x encoder, central half, position TBD |
| Tenting | Wanted; legs vs hinges TBD |
| Wrist rest | Wanted; design TBD |
| Firmware | ZMK, nRF52840, ZMK Studio (2026-09-29) |
| Budget | $450-500 self-build; validate end of Phase 3 |

## 3. Baseline: QK Alice Duo

| Keep | Change |
|---|---|
| Split Alice | Acrylic, not aluminum |
| Dual-mode wired/wireless | PP plate, not alu/FR4/PC |
| Status display | Own hub + display |
| Soft mount | Own firmware stack |
| Bottom weight | White PCB, added knob |
| — | Tenting: hinges vs fixed legs TBD |

## 4. Open decisions (sign off before Phase 1)

| # | Decision | Options | Lean | Status |
|---|---|---|---|---|
| 1 | Firmware | ZMK + Studio / QMK + VIA | ZMK | LOCKED 2026-09-29 |
| 2 | Tenting | Fixed legs / Duo-style hinges | Fixed legs rev 1 | In scope 2026-09-29 |
| 3 | Wired inter-half link | USB-C serial / pogo-magnetic | — | Open; affects both PCBs |
| 4 | Hub downstream ports | — | 2 | Open |
| 5 | Display | OLED 128x64, content per §7 | Yes | Open |
| 6 | Typing angle | 5-8° | 7° (Summit 7.5°) | Lock in Phase 2 CAD |

ZMK notes:
- QMK/VIA rejected: no real wireless path
- BLE split = well-trodden
- Studio: live keymap over USB, persisted to flash
- Combos, sticky keys, advanced behaviors: compile-time only

## 5. System architecture

Central (right), wired mode:

```
Host USB-C (upstream)
  |
USB-C port (CC pull-downs required for C-to-C)
  |
USB 2.0 hub --+-- MCU (nRF52840, USB device)
              +-- downstream USB-C 1 (500mA max)
              +-- downstream USB-C 2 (500mA max)

5V -- charger IC -- LiPo
5V -- 3.3V reg -- MCU, OLED, LEDs
Battery -- 3.3V reg (power path) -- MCU, OLED (LEDs restricted, §8)
```

Peripheral (left): MCU + battery + charger + USB-C (charge, flash). No OLED.

Wireless: BLE split. Central ↔ host (multiple profiles). Peripheral ↔ central.

MCU form factor:
- Hub downstream must reach central MCU D+/D-
- Modules (nice!nano class) don't break those out
- Central: bare nRF52840 on PCB
- Peripheral: module OK
- Verify Phase 3

Constraints:
- Hub = wired only; dead on battery (by design)
- Full LED brightness = wired only (§8)
- Battery + charger + USB-C per half
- nRF52840 antenna keepout: no copper, no metal weight

## 6. Hub

| Item | Spec |
|---|---|
| Role | Mini dock, one cable to PC |
| Upstream | 1x USB-C, USB 2.0, CC pull-downs mandatory (Phase 4 checklist) |
| Downstream | MCU + 2x USB-C accessory, 500mA each |
| Speed | USB 2.0 only; USB 3 = 5 Gbps SI work, skip |
| Power | Host 5V, tens of mA, never battery |
| Mode | Wired only |

## 7. Display

| Item | Spec |
|---|---|
| Location | Central half |
| Tech | OLED 128x64, SSD1306 class, ZMK-supported |
| Power | ~15-25 mA lit; sleep after ~30 s idle, wake on key/layer |
| Battery % | Divider → ADC → LiPo curve lookup, ±5-10%; fuel gauge = rev 2 |

Content, ranked:
1. Battery % both halves (peripheral via BLE battery service)
2. Connection: USB / BLE + active profile
3. Active layer
4. Caps lock
5. Charging / full
6. WPM, idle logo

Out of scope rev 1: clock (no RTC), weather/host widgets (needs companion app).

## 8. Power

*First-order estimates; validate Phase 2/3.*

### 8a. Wireless budget, per half

| Subsystem | Draw |
|---|---|
| nRF52840, BLE, typing | 2-5 mA avg |
| OLED lit | 15-25 mA (auto-sleep) |
| Underglow, 8/half, moderate | 40-120 mA (off/dim on battery) |
| Deep sleep | tens of µA |

Realistic avg, OLED asleep, LEDs off: ~3-5 mA/half.

### 8b. Battery sizing

- Target: 2+ weeks, 8 h active / 16 h sleep
- 8 h × 4 mA + 16 h × 0.05 mA ≈ 33 mAh/day/half
- 14 days ≈ 460 mAh
- 1000 mAh ≈ 4 weeks; 1500 mAh = generous
- Pick: 1000-1500 mAh/half; cell dims must fit stack (Phase 2)

### 8c. Wired budget (host 5V)

- USB 2.0 upstream: 500 mA
- Loads: hub (tens of mA) + MCU + OLED + LEDs (100 mA+) + charging (up to ~1 A)
- Rule: charge + LEDs + hub < upstream limit
- Levers: cap charge at 500 mA; dim LEDs while fast-charging
- Set charge current Phase 3

### 8d. Electrical rules

- CC pull-downs correct (§6)
- Charger IC per half
- Battery divider → ADC, scaled to ADC range
- Antenna keepout in copper + weight (§5)

## 9. Mechanical

| Item | Spec |
|---|---|
| Case | CNC frosted acrylic (bead-blast or frosted stock); frost = diffusion |
| Foam | Perimeter strips / selective cutouts, not full sheets; Phase 2: strips vs full vs none |
| Ball catch | Small spring ball plungers; prototype alone; cast acrylic ±10% thickness → test-fit/adjustable |
| Battery | Own pocket, clearance, no sharp edges, no weight pressure; weight never touches LiPo (verify CAD) |
| Weight | Brass or stainless, bottom, visual anchor, engraving candidate; clear of antenna keepout |
| LEDs | Side-view, edge-light frosted acrylic; evenness = hard part, test strip first |
| Light bleed | Opaque mid-layer vs embrace glow — TBD |
| Tenting | Design feet + ball catch together, Phase 2; catch must work tented |
| Inter-half | Per open decision 3 |

Stack-up, top → bottom (validate Phase 2):

```
frosted top
foam slice
PP plate
foam slice
PCB
foam slice
mid acrylic (battery + weight cavity)
brass/steel weight
bottom acrylic
```

Ball catch: top assembly ↔ mid layer.

## 10. Feel and sound

- Y2 + PP + selective foam = soft/deep target
- No plate flex cuts rev 1; test PP first
- Phase 6 matrix: foam form (strips / full / none × position), plate screw torque, weight on/off
- Log sound clips + feel notes per combo
- Keycaps locked: PBTFans XRAY, clear/white translucent ABS, Cherry; verify spacebar kit covers Alice split bottom row

## 11. Firmware

- ZMK, nRF52840, BLE split, ZMK Studio
- Widgets: battery, layer, connection; OLED sleep policy
- LEDs: wired = full, wireless = off / low cap
- Power: battery ADC, sleep timeouts, peripheral battery over BLE

## 12. Roadmap

| Phase | Work | Exit |
|---|---|---|
| 0 | Requirements + decision log | All open decisions signed off |
| 1 | Layout prototype: print to scale, hand-wire / dev-board matrix | Alice geometry validated by typing |
| 2 | Mech prototype: print or stacked acrylic; ball catch; foam + LED tests | Stack-up, catch, foam, LEDs decided |
| 3 | Electronics: block diagram, power budget, part shortlist | Architecture review passed |
| 4 | Schematic + PCB rev A, test points | Review + DRC clean |
| 5 | Firmware bring-up | Pair, type, display, battery % |
| 6 | Assembly + tuning | Feel/sound matrix logged |
| 7 | Rev B list + journal publish | Done |

Rule: one new hard thing per rev. This rev: wireless. Mitigation: heavy Phase 1-2 prototyping before any PCB order.

## 13. Risk register

| # | Risk | Mitigation |
|---|---|---|
| 1 | Missing CC resistors → C-to-C dead | Phase 4 checklist |
| 2 | LiPo touches weight | Battery pocket, CAD clearance |
| 3 | Full foam kills flex | Phase 2 foam test |
| 4 | LEDs on battery | Firmware default off on battery |
| 5 | Charge + LEDs + hub > 500 mA | Set charge current Phase 3 |
| 6 | Acrylic thickness vs ball catch | Prototype catch alone |
| 7 | Weight/copper in antenna keepout | Keepout in Phase 2 CAD, check Phase 4 |
| 8 | Tenting × ball catch × split | Prototype together Phase 2; fixed legs rev 1 |
| 9 | Late firmware decision | Locked Phase 0 |
| 10 | Inter-half link undecided | Decide Phase 0; affects both PCBs |
| 11 | Hub won't bring up (flurples `campus`: shipped bypassed) | Breakout test Phase 3; depopulatable/bypassable layout; fallback unified daughterboard (`summit`). Forces bare central nRF52840 (§5) |

## 14. Repo structure (proposed)

```
journal/          dated build log
docs/decisions/   one file per decision: context, options, choice, why
hardware/         schematics, PCB, BOM
firmware/         ZMK config
cad/              case models, DXFs
media/            sound clips, photos
```

## 15. Open questions

| # | Question | Status |
|---|---|---|
| 1 | Firmware: ZMK + Studio? | LOCKED 2026-09-29 |
| 2 | Tenting: fixed legs vs hinges? | Open |
| 3 | Inter-half: cable vs pogo/magnetic? | Open |
| 4 | Hub: 2 downstream ports? | Open |
| 5 | Display: OLED 128x64 + content list? | Open |
| 6 | Typing angle 7°? | Open |
| 7 | Shop access | Confirmed |

Shop: SJSU Engineering Makerspace
- Any project, engineering students; Mon-Fri 10-4, iSupport ticket
- 4 soldering stations + fume extractors → hand-solder rev A viable, PCBA optional
- 4x Bambu P1S, 1x X1C, 6x Voron 2.4
- 600 W laser, ≤ 1/4", via ticket → stacked acrylic fallback in-house
- No CNC mill → outsource CNC case, get quotes
