# Reference: flurples' Summit build process

*Source: [build video](https://youtu.be/qhuydgdiscI) (transcript pulled 2026-09-29) + [github.com/flurples/summit](https://github.com/flurples/summit) (GPL-3.0, has case/PCB/plate production files to study). Summit = gummy o-ring mount, MX-compatible, symmetric HHKB, transparent polycarbonate chassis.*

## His four phases (maps to our roadmap)

| # | Flurples' phase | What he does | Our equivalent |
|---|---|---|---|
| 1 | Planning | Core questions: layout? standard or custom? mounting style? manufacturing method? Study existing keyboards. | Phase 0 (this doc) |
| 2 | Modeling | KLE → ai03 plate generator → DXF → Fusion 360. Case and PCB designed around each other simultaneously. | Phases 1-2 |
| 3 | Making it work | Existing PCB vs handwire vs custom PCB. KiCad + community keyboard part libraries. JLCPCB for fab. | Phases 3-4 |
| 4 | Assembly | Firmware (QMK for his wired build), flash, verify, build. | Phases 5-6 |

## Concrete toolchain to copy

1. **keyboard-layout-editor.com (KLE)** — lay out the Alice geometry, get raw data.
2. **ai03 plate generator** — paste KLE raw data, outputs a DXF with proper key spacing. "90% of the plate work is already done" from this file.
3. **Fusion 360** — build the 3D case design around the DXF.
4. **KiCad** — PCB design; keyboard part libraries exist in the community, free and open source.
5. **JLCPCB** — his go-to fab; 2 layers is fine for most keyboard PCBs.

## Takeaways applied to Project Alice

- **Laser-cut the weight, don't CNC it.** Summit's brass/steel weights are laser-cut from 1.6mm sheet metal: "a fraction of the cost of CNC parts because they are two-dimensional." Directly applicable to our brass-vs-stainless decision. He did both an external weight (most of the bottom) and a smaller internal one.
- **Transparent case validates our direction.** He chose polycarbonate specifically for the transparent effect, and his philosophy is ours: "the best designs show thought and effort not only into the external appearance but also the internal workings." Our clear window + frosted body needs the same discipline: clean PCB, tidy batteries, engraved weight.
- **Unified daughterboard for USB-C.** Summit doesn't route USB-C on the main PCB; it uses a proven "unified daughterboard s1" with a molex cable. If our USB-C routing gets hairy, this is the fallback pattern.
- **Iterate, don't perfect.** "It's an unreal expectation to achieve perfection after just one or a handful of tries." Our Phase 7 rev B list is the same idea, formalized.

## ⚠️ Cautionary data point: the USB hub

On his other project (Framework 13 `campus` build), flurples writes: **"the usb hub was too complex and I wasn't able to get it working... I ended up simply bypassing the usb hub entirely."** He shipped the keyboard with the hub bypassed.

Implication for us: the hub is our highest-risk electrical item, higher than wireless. Mitigations, in order:
1. Prototype the hub chip on a breakout/dev board *before* it's on our PCB (Phase 3).
2. Keep the keyboard functional with the hub depopulated (design so it can be bypassed, like his).
3. Fallback: daughterboard pattern instead of hub-on-main-PCB.

Added to the risk register as item 11.
