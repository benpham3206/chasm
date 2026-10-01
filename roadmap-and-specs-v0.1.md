# Project Alice — Roadmap & Specs v0.1

*Status: draft for review, 2026-09-29. The one-and-done custom split Alice keyboard, inspired by the QK Alice Duo (discontinued). Companion to the GitHub engineering journal.*

## 1. Design goals

- Feel: soft, flexy typing feel
- Sound: deep, muted, thocky (not clacky)
- Aesthetics: frosted acrylic, diffused LED glow, metal weight as a design piece
- Customizability: hot-swap switches, live remappable, open firmware
- Process: full engineering journal on GitHub, decisions logged as they're made

## 2. Locked decisions

| Area | Decision |
|---|---|
| Layout | Split Alice, 60% ergo, Duo-inspired |
| Switch | Keygeek Y2 linear, 48g actuation / 53g bottom-out, 5-pin PCB mount, factory lubed, UPE waffle stem, PA12 housings |
| Plate | Polypropylene (PP), soft with flex |
| Case | CNC acrylic, frosted with a clear polished window over the weight (locked 2026-09-29, matches XRAY transparent-tech theme) |
| Case opening | Ball catch mechanism (tool-free, no screws for opening) |
| Power | Battery powered, LiPo per half, USB-C |
| Hub | Wired USB-C hub on the central half |
| Display | Status display on the central half |
| Lighting | Diffused LED underglow through the frosted acrylic |
| PCB | White soldermask (visible through clear case, matches XRAY theme) |
| Knob | Yes, 1x rotary encoder on central half (position TBD in layout) |
| Tenting | Wanted (fixed legs vs adjustable hinges TBD) |
| Wrist rest | Wanted (design TBD) |
| Budget | $450-500 all-in self-build, validated end of Phase 3 |

## 3. Reference baseline: QK Alice Duo

Keep: split Alice layout, dual-mode wired/wireless concept, status display, soft mount philosophy, bottom weight.
Change: acrylic instead of aluminum, PP plate instead of alu/FR4/PC, our own hub + display implementation, our firmware stack, tenting wanted (Duo-style adjustable hinges vs fixed legs TBD), white PCB, added knob.

## 4. Open decisions (sign off before Phase 1)

1. **Firmware: ZMK on nRF52840 + ZMK Studio — LOCKED (Ben, 2026-09-29).** QMK/VIA rejected: no real wireless path. ZMK is wireless-native with BLE split as the well-trodden route, and ZMK Studio (zmk.studio) gives VIA-like live keymap editing over USB with changes persisted to flash. Trade-off: combos, sticky keys and advanced behaviors must be compiled into firmware, Studio's UI can't create them.
2. **Tenting: in scope (Ben, 2026-09-29).** Decide fixed-angle legs (recommended for rev 1: simpler, cheaper, fewer failure modes with the ball catch) vs Duo-style adjustable hinges.
3. **Wired inter-half link:** USB-C cable carrying serial vs pogo-pin/magnetic (Duo-style). Affects both PCBs, decide now.
4. **Hub downstream ports:** 2 accessory ports (recommended).
5. **Display:** OLED 128x64 with the content list in section 7 (recommended).
6. **Typing angle:** recommend 7° (typical custom range 5-8°; Summit used 7.5°). Lock in Phase 2 CAD.

## 5. System architecture

Central (right) half, wired mode:

```
Host USB-C (upstream)
  |
USB-C port (correct CC pull-downs, else C-to-C cables won't work)
  |
USB 2.0 hub chip --+-- MCU (nRF52840, USB device)
                   +-- downstream USB-C port 1 (accessories, 500mA max)
                   +-- downstream USB-C port 2 (accessories, 500mA max)

5V rail -- charger IC -- LiPo battery
5V rail -- 3.3V regulator -- MCU, OLED, LEDs
Battery -- 3.3V regulator (power path) -- MCU, OLED (LEDs restricted, see section 8)
```

Peripheral (left) half: MCU + battery + charger + USB-C (charging and flashing), no OLED.

**MCU form factor:** the hub's downstream port must reach the central MCU's USB D+/D-, which ready-made modules (nice!nano class) don't break out — so the central half likely needs a **bare nRF52840** on our PCB, while the hub-free peripheral half can use a nice!nano-style module. Verify in Phase 3.

Wireless mode: BLE split link, central pairs to host (multiple BLE profiles), peripheral pairs to central.

Architecture facts that drive the design:

- The hub is wired-mode only. On battery the hub chip is unpowered and the downstream ports are dead. By design, not a bug.
- Full-brightness LEDs are a wired-mode feature. On battery they stay off or heavily capped (section 8).
- Each half carries its own battery, charger IC, and USB-C port (both halves need flashing and charging).
- nRF52840 antenna keepout: no copper pour and no metal weight under the antenna area. This constrains weight placement in CAD.

## 6. Hub scope, expanded

What the hub is: a USB 2.0 hub chip on the central half that turns the keyboard into a mini dock. One cable to the PC; the keyboard shows up as a device and you gain spare ports for accessories.

- **Upstream:** 1x USB-C to the host. USB 2.0 data speeds, USB-C connector for modern cables. The port must have proper CC pull-down resistors or USB-C to USB-C cables silently won't work. Classic beginner trap, checklist item in Phase 4.
- **Downstream:** the keyboard's own MCU, plus 2x USB-C accessory ports (mouse dongle, flash drive, etc.), 500mA each.
- **Why USB 2.0 only:** a USB 3 hub means 5Gbps signal-integrity work. Not worth it on a first PCB. USB 2.0 covers keyboard, dongles, and flash drives fine.
- **Power:** the hub chip draws tens of mA from the host's 5V rail. Never from the battery.
- **Wired-mode only** (see section 5). When unplugged, the hub is inert.

## 7. Display spec

- **Location:** central half. **Tech:** OLED 128x64 (SSD1306 class), the standard DIY choice with ZMK support.
- **Power behavior:** ~15-25mA when lit, so firmware sleeps it after ~30s idle and wakes on keypress or layer change.
- **Content, ranked by usefulness:**
  1. Battery % for both halves (central shows the peripheral's too, via the BLE battery service)
  2. Connection status: USB vs BLE, and which BLE profile is active
  3. Active layer
  4. Caps lock
  5. Charging state (charging / full)
  6. Flavor: WPM, idle logo art
- **How battery % works:** yes, pull it from voltage. Battery voltage goes through a divider into the MCU's ADC, then a LiPo discharge-curve lookup turns voltage into %. Approximate (±5-10%), fine for a status screen. A dedicated fuel-gauge IC is the rev 2 upgrade if you ever care.
- **Out of scope for rev 1:** clock (no battery-backed RTC, time would reset), weather or host widgets (needs a companion app).

## 8. Power and battery constraints

All figures are first-order estimates to validate in Phase 2/3, not datasheet guarantees.

### 8a. Wireless-mode budget (per half)

| Subsystem | Draw |
|---|---|
| nRF52840, BLE connected, typing | 2-5 mA average |
| OLED lit | 15-25 mA (auto-sleep, section 7) |
| Underglow LEDs, 8 per half, moderate | 40-120 mA (policy: off or dim on battery) |
| Deep sleep | tens of uA |

Realistic average with the OLED sleeping and LEDs off on battery: ~3-5 mA per half.

### 8b. Battery sizing

Target: 2+ weeks of typical use (8h/day active, 16h sleep).

8h x 4mA + 16h x 0.05mA ≈ 33 mAh/day per half → 14 days ≈ 460 mAh. A 1000 mAh cell per half gives roughly 4 weeks with margin; 1500 mAh is generous. Recommendation: 1000-1500 mAh LiPo per half. The cell's physical dimensions must fit the case stack, which is a mechanical constraint to check in Phase 2.

### 8c. Wired-mode budget (5V rail, host-powered)

A standard upstream USB 2.0 port provides 500mA. Consumers on the 5V rail: hub chip (tens of mA) + MCU + OLED + LEDs (100mA+ when lit) + battery charging (settable, commonly up to 1A). Constraint: charge current + LEDs + hub must stay under what the upstream port provides. Levers: cap charge current at 500mA, or dim the LEDs while fast-charging. Pick the charge current in Phase 3, not during layout.

### 8d. Non-negotiable electrical rules

- USB-C CC pull-downs correct for C-to-C cables (section 6).
- Dedicated LiPo charger IC per half.
- Battery voltage divider into the ADC, scaled to the ADC's input range.
- Antenna keepout respected in copper and in weight placement (section 5).

## 9. Mechanical constraints

- **Case:** CNC frosted acrylic (bead-blasted or frosted stock). Frosted outer surfaces are what diffuse the LED underglow.
- **Candidate stack-up, top to bottom (validate in Phase 2):** frosted top → foam slice → PP plate → foam slice → PCB → foam slice → mid acrylic (battery + weight cavity) → brass/steel weight → bottom acrylic. Ball catch joins the top assembly to the mid layer.
- **Foam "slices":** full sheets kill flex. For the soft, flexy feel, use perimeter strips or selective cutouts, not full coverage. Phase 2 experiment: strips vs full vs none, logging feel and sound for each.
- **Ball catch:** source small spring ball plungers and prototype the catch alone first. Cast acrylic thickness varies ~±10%, so design the catch to be test-fit or adjustable, not dimensioned from theory.
- **Battery safety:** dedicated pocket with clearance, no sharp edges, no pressure from the weight. The metal weight must never touch the LiPo. Non-negotiable, verified in CAD.
- **Weight:** brass or stainless bottom weight, also the visual anchor (engraving candidate). Keep it clear of the antenna keepout.
- **LED diffusion:** side-view LEDs edge-light the frosted acrylic. Evenness is the hard part, so prototype with a test strip before finalizing count and placement. Decide the light-bleed policy: block light from the switch field with an opaque mid-layer, or embrace the glow (aesthetic call).
- **Split halves:** tenting wanted — design the tenting foot system together with the ball catch in Phase 2 (catch must work at the tenting angle). Wired inter-half link per open decision 3.

## 10. Feel and sound tuning plan

- The stack as specified (Y2 deep/thocky switch + soft PP plate + selective foam) is the soft/deep target. No flex cuts in the plate for rev 1; PP is already flexy, test before cutting.
- Phase 6 experiments: foam-form matrix (strips / full / none, times positions), plate screw tightness, weight on vs off. Record sound clips and feel notes in the journal for each combination.
- Keycaps are locked: PBTFans XRAY (clear/white translucent ABS, Cherry profile). Verify the spacebar kit covers the Alice split bottom row before ordering.

## 11. Firmware plan (pending open decision 1)

- Recommended: ZMK on nRF52840, BLE split, ZMK Studio enabled for live remapping.
- Display widgets for battery, layer, and connection status. OLED sleep policy in firmware.
- LED policy: wired = full effects, wireless = off or a low brightness cap.
- Power: battery ADC configuration, sleep timeouts, peripheral battery reporting over BLE.

## 12. Roadmap

| Phase | Work | Exit criteria |
|---|---|---|
| 0 | Requirements + decision log (this document) | All 5 open decisions signed off |
| 1 | Layout prototype: print at scale, hand-wire or dev-board matrix | Alice geometry validated by actual typing |
| 2 | Mechanical prototype: 3D print or stacked acrylic; ball catch tolerance test; foam-form and LED diffusion experiments | Stack-up, catch tolerance, foam form, LED placement decided |
| 3 | Electronics architecture: block diagram, validated power budget, part shortlist | Architecture review passed |
| 4 | Schematic + PCB rev A, conservative, with test points | Design review + DRC clean |
| 5 | Firmware bring-up | Both halves pair, type, display and battery % work |
| 6 | Assembly + tuning | Feel/sound experiment matrix logged |
| 7 | Rev B list + journal publish | Done done |

Working rule: one new hard thing per revision. Wireless is the new hard thing here; the mitigation is heavy prototyping in Phases 1 and 2 before any PCB is ordered.

## 13. Risk register (beginner traps, planned for now)

1. Missing USB-C CC resistors → C-to-C cables dead. Phase 4 review checklist.
2. LiPo contacting the metal weight → dedicated battery pocket, clearance verified in CAD.
3. Full foam sheets killing the flex → foam-form experiment in Phase 2.
4. LEDs on battery → firmware lighting policy, default off on battery.
5. Charge current + LEDs + hub exceeding 500mA upstream → set charge current in Phase 3.
6. Acrylic thickness variance vs ball catch → prototype the catch in isolation.
7. Antenna keepout violated by weight or copper → keepout drawn in Phase 2 CAD, checked in Phase 4.
8. Tenting + ball catch + split interaction → prototype the tenting feet together with the ball catch in Phase 2; fixed-angle legs recommended over adjustable hinges for rev 1.
9. Firmware stack decided late → decided in Phase 0 (now); it drives MCU choice.
10. Inter-half wired link undecided → decided in Phase 0; affects both PCBs.
11. USB hub too complex to bring up on rev A (flurples failed exactly this on his `campus` Framework build and shipped with the hub bypassed) → prototype the hub on a breakout board in Phase 3, design the PCB so the hub can be depopulated/bypassed, fallback is the proven unified-daughterboard pattern from his `summit`. Central MCU USB routing forces the bare-nRF52840 decision in section 5.

## 14. GitHub journal structure (proposed)

```
journal/          dated build log entries
docs/decisions/   one file per big decision: context, options, choice, why
hardware/         schematics, PCB, BOM
firmware/         ZMK config
cad/              case models, DXFs
media/            sound clips, photos
```

## 15. Open questions for Ben

1. ~~Firmware: ZMK + ZMK Studio?~~ LOCKED 2026-09-29.
2. Tenting: fixed-angle legs vs adjustable hinges?
3. Inter-half wired link: cable vs pogo/magnetic?
4. Hub: 2 downstream accessory ports OK?
5. Display content list and OLED 128x64 OK?
6. Typing angle: 7°?
7. Tenting: fixed-angle legs vs adjustable hinges?
8. Shop access: confirmed — SJSU Engineering Makerspace is open to engineering students for any project (not research-only), Mon-Fri 10 AM-4 PM via iSupport ticket. 4 soldering stations with fume extractors, 4x Bambu P1S + 1x X1C + 6x Voron 2.4 printers, 600W laser cutter up to 1/4" material via ticket. No CNC mill listed → CNC acrylic case must be outsourced (get quotes); stacked laser-cut acrylic is the in-house fallback. Soldering gear confirmed → hand-solder rev A viable, PCBA optional.
