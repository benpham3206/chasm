# Decision: inter-half link (open decision #3)

*2026-10-01. Locked for rev 1.*

| | |
|---|---|
| Options | BLE only · USB-C wired split (full-duplex UART) · pogo/magnetic |
| Choice | **BLE only** |
| Why | ZMK wired split = early-adopter feature; pogo = Duo's main complaint; fewer case openings, no cross-plug risk |
| Consequence | Each half: own USB-C (charge + flash). No inter-half port in case |
| Revisit | Rev B, if wired mode for the peripheral is wanted |
