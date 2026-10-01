# Reference: QK Alice Duo teardown (desk research)

*Researched 2026-09-29. No physical unit opened — everything here is from QK's Notion docs, retailer pages and reviews. Key sources: [QK user manual](https://qwertykeys.notion.site/QK-Alice-Duo-Wireless-PCB-Guide-1df3d0900942809fb668d1813ab8521f), [SemiPro review](https://semiprotechgear.com/qwertykeys-qk-alice-duo-review-time-to-split/), [alexotos review](https://www.alexotos.com/qk-alice-duo/), [Divinikey](https://divinikey.com/products/qk-alice-duo-keyboard), [QK extra parts](https://www.qwertykeys.com/products/qk-alice-duo-extra-parts-purchasing-alone).*

## What it actually is

- Split Alice, 68 keys ANSI, two independent halves + a wireless "pod". "Duo" = the two halves.
- Each half: CNC aluminum top + bottom, 188 x 118 mm, ~800-815 g, 7° typing angle, 19 mm front height, 1800 mAh battery, PCB-gasket mount, magnetic stainless weight.
- Tenting: dual metal hinge per half, 0° or 5°.
- Plates: FR4 (flex cuts), aluminum, PC. PCB: 1.2 mm flex-cut or 1.6 mm (1.2 mm may need stab shims).
- Launched April 2025, $289 MSRP, at least 9 pre-order batches (Batch 9 closed 30 Nov 2025).

## The "proprietary port"

- Each half connects to the pod by a **magnetic pogo-pin cable**, used for charging, wired mode and initial pairing.
- Only the pod has USB-C to the host. The pod is also the 2.4G dongle, status display and volume knob.
- The cable is polarity-sensitive, not keyed: QK's fix for a bad seat is "rotate the connector 180°".
- No pinout, pin count or part number is published anywhere. Unknown whether it carries USB D+/D-, UART or something custom.
- Spare PCBs "DO NOT include MCU" → MCU and radio probably live on a case-side daughterboard. Inference, not teardown.
- Reviewers call the cable finicky and wish it were USB-C. Spare cables still listed (~$12-20).

## Firmware and files

- Closed firmware, configured through QK's web configurator (cfg.qwertykeys.com). Not in upstream QMK.
- Update zips only: v1.0.6 on qwertykeys.com, older ones mirrored at [KBD-Type-S](https://github.com/KBD-Type-S/QK-Alice-Duo-Firmwares).
- No gerbers, schematics, CAD or DXFs published.

## "Discontinued" — unverified

Retailers show sold out / made to order, but no official end-of-production notice turned up, and QK still sells spare cables and PCBs. Worth one question on the QK Discord before assuming.

## Takeaways applied to Project Alice

- **Nothing to clone.** No files, closed protocol → our own PCB and firmware was always the only path. Confirms the ZMK + nRF52840 decision.
- **Keep the Duo's numbers as targets:** 7° angle (matches our open decision 6), ~800 g per half, 188 x 118 mm per half, 0°/5° tent.
- **Open decision 3 (inter-half link):** USB-C carrying serial has commercial precedent — splitkb Halcyon, Cyboard Imprint, open-source [YAEMK](https://karlk90.github.io/yaemk-split-kb/) all run full-duplex UART over the D+/D- pins. Catch for us: ZMK wired split is experimental and full-duplex UART only. Since BLE split is the primary link anyway, the wired link may be optional for rev 1.
- **Cross-plug risk:** an inter-half USB-C port looks identical to the host port. Vendors disagree on hot-plugging (splitkb: fine; Cyboard: unplug USB first). Mitigation is a design-review item in Phase 4.
- **The Duo's pogo cable is what we're avoiding.** Pogo/magnetic for the inter-half link reintroduces the exact pain point.

## USB-C rules worth pinning (Phase 4 checklist)

- 5.1 kΩ on CC1 and CC2 **separately** to GND. One shared resistor = C-to-C cables dead.
- A6/B6 → D+, A7/B7 → D-. SuperSpeed pins unconnected. 16-pin receptacle is enough.
- Parts: HRO TYPE-C-31-M-12 (LCSC C165948, ~$0.17), mid-mount C168688, USBLC6-2SC6 ESD (C7519).
- PTC + TVS on VBUS. Shield to ground via ferrite, one chassis tie. Solder the shield tabs well.
- Template: [Unified Daughterboard](https://github.com/Unified-Daughterboard/UDB-C-Legacy) protection pattern (same fallback as in `flurples-summit.md`).

## If we ever get a Duo in hand

Measure: cable pin count and polarity, levels on each pin, chip markings, Alice inner-column angle, case wall thickness, hinge geometry. Battery switch is under the Alt keys — off before probing.
