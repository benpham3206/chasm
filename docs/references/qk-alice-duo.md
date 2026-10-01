# Ref: QK Alice Duo

*2026-09-29. Desk research, no unit opened. [QK manual](https://qwertykeys.notion.site/QK-Alice-Duo-Wireless-PCB-Guide-1df3d0900942809fb668d1813ab8521f) · [SemiPro](https://semiprotechgear.com/qwertykeys-qk-alice-duo-review-time-to-split/) · [alexotos](https://www.alexotos.com/qk-alice-duo/) · [Divinikey](https://divinikey.com/products/qk-alice-duo-keyboard) · [QK parts](https://www.qwertykeys.com/products/qk-alice-duo-extra-parts-purchasing-alone)*

## Specs

| Item | Value |
|---|---|
| Layout | Split Alice, 68 keys ANSI |
| Parts | 2 halves + wireless pod |
| Half size | 188 x 118 mm |
| Half weight | ~800-815 g |
| Case | CNC alu top + bottom per half |
| Angle | 7° |
| Front height | 19 mm |
| Mount | PCB gasket |
| Weight | Stainless, magnetic |
| Tent | Dual hinge, 0° / 5° |
| Plates | FR4 (flex cut), alu, PC |
| PCB | 1.2 mm flex-cut (stab shims) / 1.6 mm |
| Battery | 1800 mAh / half |
| Price | $289 MSRP |
| Released | Apr 2025; ≥9 batches, #9 closed 2025-11-30 |

## Proprietary port

- Half ↔ pod: magnetic pogo-pin cable (charge, wired mode, pairing)
- Pod = only USB-C to host; also 2.4G dongle, display, volume knob
- Polarity-sensitive, not keyed (QK fix: rotate 180°)
- Pinout / pin count / part no.: unpublished
- Signals (USB D+/D- vs UART vs custom): unknown
- Spare PCBs ship without MCU → MCU likely on case-side daughterboard (inference)
- Reviews: cable finicky, want USB-C
- Spare cable: ~$12-20

## Firmware / files

- Closed; config via cfg.qwertykeys.com; not in QMK
- Zips only: v1.0.6 on qwertykeys.com; older at [KBD-Type-S](https://github.com/KBD-Type-S/QK-Alice-Duo-Firmwares)
- No gerbers, schematics, CAD, DXF

## Discontinued?

Unverified. Sold out / made to order; no EOL notice; spare cables + PCBs still listed.

## Takeaways

- Nothing to clone → own PCB + firmware (confirms ZMK + nRF52840)
- Targets: 7°, ~800 g/half, 188 x 118 mm/half, 0°/5° tent
- Open decision 3:
  - USB-C serial precedent: splitkb Halcyon, Cyboard Imprint, [YAEMK](https://karlk90.github.io/yaemk-split-kb/) — full-duplex UART on D+/D-
  - ZMK wired split: experimental, full-duplex UART only
  - BLE = primary link → wired link optional rev 1?
  - Pogo/magnetic = the Duo's pain point; avoid
- Cross-plug: inter-half port looks like host port; hot-plug disputed (splitkb OK, Cyboard unplug USB first) → Phase 4 review

## USB-C checklist (Phase 4)

- 5.1 kΩ CC1 → GND, 5.1 kΩ CC2 → GND, separate
- A6/B6 → D+, A7/B7 → D-; SS pins NC; 16-pin OK
- HRO TYPE-C-31-M-12 (LCSC C165948, ~$0.17); mid-mount C168688
- ESD: USBLC6-2SC6 (C7519)
- VBUS: PTC + TVS
- Shield → GND via ferrite, single chassis tie; solder shield tabs well
- Pattern: [Unified Daughterboard](https://github.com/Unified-Daughterboard/UDB-C-Legacy)

## Measure if a unit appears

- Cable pin count, polarity, levels per pin
- Chip markings
- Inner-column angle
- Wall thickness
- Hinge geometry
- Battery switch under Alt keys → off before probing
