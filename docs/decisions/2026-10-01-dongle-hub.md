# Decision: system architecture — dongle hub (Duo-style)

*2026-10-01. Locked (user).*

| | |
|---|---|
| Context | Roadmap §5 had hub + OLED inside the right half (central); left half → right half → PC (daisy chain). User expected the QK Alice Duo model |
| Options | Central half (roadmap v0.1) · separate dongle hub, both halves wireless to it |
| Choice | **Dongle hub**: own small enclosure, always plugged into the PC; ZMK central. Both halves = BLE peripherals, connected at the same time |
| Hub box holds | MCU (central), USB 2.0 hub, upstream USB-C, 2 downstream USB-C (#4, lean), OLED 128x64 |
| Halves hold | MCU (peripheral), LiPo, charger, 1 USB-C each (charge + flash), on the inner edge |
| Why | Matches Duo; OLED + hub on USB power (never dead on battery, no OLED sleep compromise); halves become identical-role peripherals → better battery life, simpler boards |
| Costs | 3rd board + 3rd enclosure (Blender/SolidWorks object); halves only type through the dongle (ZMK roles are compile-time; direct BLE to a phone/laptop = other firmware build) |
| Lighting | Halves are always on battery now → underglow on halves only when USB-C plugged, or very dim (decide with lighting) |
| Encoder | Rev 2026-10-02: on the right half, right of Backspace (case grows ~9 mm at the upper outer edge); hub has no knob. ZMK peripheral encoder support — verify Phase 3 |
| Affects | Roadmap §2, §5, §6, §7; BOM electronics; gates A7, A8; MCU decision (USB pins now needed in the dongle only) |
