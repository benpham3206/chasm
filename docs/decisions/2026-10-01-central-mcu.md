# Decision: MCU form factor

*2026-10-01. Locked: module (user: no strong preference, pick on looks).*

| | |
|---|---|
| Context | Hub needs MCU USB D+/D-. Roadmap §5 assumed modules don't break these out → bare nRF52840 |
| Finding | Board-style modules (nice!nano) don't; bare RF modules do: E73-2G4M08S1C has D+ / D- pins; Raytac MDBT50Q used the same way (mdbt-micro) |
| Options | Bare nRF52840 · RF module with USB pins |
| Choice | **RF module** (E73-2G4M08S1C or MDBT50Q) in the dongle; same module on both halves for one look |
| Why | Bare chip = own antenna matching + RF layout, verifiable only with RF gear. Module: pre-tuned antenna, fixed keepout. Looks: flat metal can on white PCB, visible through the clear bottom — cleaner than a plugged nice!nano daughterboard |
| Cost | Few $ more; ~13 × 18 mm footprint; halves need own USB-C + charger routing (no nice!nano shortcut) |
| Affects | Roadmap §5, BOM MCU lines, risk #7 (keepout now known), risk #11 (hub fallback no longer forces bare chip) |
