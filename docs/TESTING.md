# Playback tests and evidence

The project has been tested with multiple films on DVD and Blu-ray, on a PS3 Slim
with Evilnat 4.93 CEX, Cobra 8.5 and RGB-SCART AV Multi Out.

| Test | Observed result | Build context |
|---|---|---|
| Zodiac — DVD | Correct colors; normal audio and XMB return | Earlier two-template build |
| Perfect Days — Blu-ray | Correct colors across two startup mode changes; repeated playback and an over-eleven-minute test followed by DVD without restarting | Earlier two-template build |
| Samsara — Blu-ray | Correct colors including its second startup mode change; temporary test and subsequent HDD autoload/restart/playback confirmation passed | Current three-template build |
| MGS2 — game | Normal in-game colors reported | Earlier build |

The current build preserves the two existing packet templates and adds a third
480-line variant. Those earlier title checks are not a fresh full regression of
every title on the current binary. Full-film endurance, arbitrary discs/games,
other consoles/firmware and other cable types are not certified.

Film names identify examples, not an allowlist. The plugin does not inspect film
titles: it matches exact AV request packets. An unfamiliar title may work if its
requests match; an unfamiliar request may remain green.

Native visual reports, native loader/guard checks and offline instruction-model
tests are separate evidence. The public source rebuild matches the tested
decrypted PRX byte-for-byte. No private raw captures are included.
