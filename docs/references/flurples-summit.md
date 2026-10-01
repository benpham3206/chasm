# Ref: flurples — Summit

*2026-09-29. [Video](https://youtu.be/qhuydgdiscI) · [github.com/flurples/summit](https://github.com/flurples/summit) (GPL-3.0, case/PCB/plate files).*

Summit: gummy o-ring mount, MX, symmetric HHKB, transparent PC chassis.

## Phases

| # | His phase | Work | Ours |
|---|---|---|---|
| 1 | Planning | Layout, standard vs custom, mount, manufacturing; study existing boards | 0 |
| 2 | Modeling | KLE → ai03 plate gen → DXF → Fusion 360; case + PCB co-designed | 1-2 |
| 3 | Making it work | Existing PCB / handwire / custom; KiCad + community libs; JLCPCB | 3-4 |
| 4 | Assembly | QMK (wired), flash, verify, build | 5-6 |

## Toolchain

1. KLE → layout raw data
2. ai03 plate generator → DXF (~90% of plate work)
3. Fusion 360 → case around DXF
4. KiCad + community keyboard libs
5. JLCPCB, 2-layer

## Takeaways

- Weights: laser-cut 1.6 mm sheet brass/steel, not CNC → fraction of cost (2D). External (most of bottom) + small internal.
- Transparent case: PC for see-through; internals must be clean (PCB, batteries, engraved weight).
- USB-C: unified daughterboard s1 + Molex cable, not on main PCB → our fallback.
- Iterate; rev B list (Phase 7).

## ⚠ USB hub

- `campus` (Framework 13 build): hub didn't work → shipped bypassed
- Our hub risk > wireless risk

Mitigations:
1. Hub on breakout first (Phase 3)
2. Board works with hub depopulated/bypassed
3. Fallback: daughterboard pattern

→ Risk register #11.
