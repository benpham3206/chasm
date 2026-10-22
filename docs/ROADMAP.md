# chasm roadmap v0.2

Supersedes v0.1. Research behind it: [`research/gate-b-report.md`](research/gate-b-report.md).

**Done means:** a working wireless split Alice (two halves + dongle hub) in the frosted acrylic case, typing well, within about $450–500, with the build journaled in this repo.

**Rules:** one new hard thing per rev (wireless). Nothing is sent or ordered until renders and CAD match and Ben signs off.

## Where we are (2026-10-22)
- Design decisions locked (`docs/decisions/`, `docs/cad-gates.md`).
- Layout generator and paper prints done; 8° chosen from a paper test.
- Render rev3 drafts done but rough (see report §1).
- Gate B parts still open; nothing physical built yet.

## Milestones

| # | Milestone | Done when | Est. |
|---|---|---|---|
| M1 | Render polish (rev4) | Ben signs off hero, macro and hub shots; design frozen (case/bezel proportions, legend scale, colours) | 1 wk |
| M2 | Parts locked (Gate B) | Every Gate B item decided with dims in `ref/`; BOM checked against budget | 1 wk, parallel with M1 |
| M3 | Typeable prototype | Laser-cut PP plate with gasket tabs, hand-wired to two nice!nano, ZMK split flashed, a week of daily typing confirms 68 keys and 8° | 2 wk |
| M4 | Mechanical prototype | Stacked laser-cut/printed acrylic; ball catch, U-frame tent + catch, foam, edge-light strip tested; stack-up locked | 2 wk |
| M5 | Electronics | Schematics for halves + dongle (USB-C CC pull-downs, antenna keep-out), PCB rev A DRC clean and ordered after approval | 2–3 wk |
| M6 | Firmware bring-up | Pairing, typing, OLED and battery % working | 1–2 wk |
| M7 | Case | Final CAD, renders updated to match, JLCCNC/PCBWay quotes, order after approval | 2–3 wk lead |
| M8 | Assembly and tuning | Sound and feel matrix logged | 1 wk |
| M9 | Write-up and rev B list | Journal published | 1 wk |

Earliest realistic finish: about mid-December if M1–M3 start now.

## Open questions for Ben
- Who re-renders rev4?
- Hot-swap (recommended) or soldered switches?
- Go-ahead for the ~$105 prototype parts.
