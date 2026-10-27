# PS3 RGB-SCART DVD / Blu-ray Green Screen Fix

**v0.2.0 — Samsara support.** A VSH plugin that corrects known AVMULTI color
requests from the original PS3 disc player on **Evilnat 4.93 CEX / Cobra 8.5**.
For RGB-SCART displays with normal XMB/game colors but a green DVD/Blu-ray picture.

## Download

Use `dist/disc_rgb_three.sprx` in the source package or the standalone SPRX
in [Releases](https://github.com/74zw7bz777-bit/ps3-rgb-scart-disc-fix/releases). Read [installation and recovery](docs/INSTALL.md)
before enabling autoload. This modifies live VSH instructions and can freeze an
incompatible system; it is not a read-only tool. No flash modification is needed.

**Tested binary:** 4537 bytes. SHA-256:
`153fd84dacea486b078a74f584190c67b563e60b591cccf1ab758c73ecc2992e`

## Compatibility and evidence

- Target: PS3 Slim, Evilnat **4.93 CEX**, **Cobra 8.5**, RGB-SCART / AV Multi Out.
- New v0.2.0: Samsara Blu-ray visual test passed, followed by HDD autoload,
  restart verification and another successful playback report.
- Prior build: Zodiac DVD and Perfect Days Blu-ray, repeated playback, more than
  eleven minutes of Blu-ray followed by DVD without restarting, normal XMB return.
  MGS2 gameplay was also visually reported normal on the prior build.
- Those older tests are not a fresh regression run of every title on v0.2.0.
  No claim of all-disc, all-game, full-film endurance or other-firmware support.
- HDMI/component and other cable configurations are outside the tested scope.
  Disable before changing firmware or output configuration.

The exact-match filter recognizes **three complete 116-byte AV requests**:
known 576-line and 480-line applications, plus the Samsara 480-line variant.
Unrecognized requests pass through unchanged and may still produce green output.
It is not a disc/application detector; a matching game request can also match.

## How it works

Five guarded temporary VSH hooks observe the AV transaction path. For an exact
matching request targeting AVMULTI port `0x10`, two 32-bit fields are changed:

- Packet offset `0x30`: VIDEO_MODE output format `9 -> 0`.
- Packet offset `0x4C`: AV_VIDEO_CS color selection `0x00010001 -> 0`.

Copy-control/signaling bytes remain unchanged. Samsara's extra template differs
from the previous 480-line template at byte `0x72` (`0x04 -> 0x34`); the plugin
recognizes this variant but does not rewrite that signaling byte.
Firmware/Cobra and 25 anchors are checked before hook installation. Fault
conditions request rollback. This is a color-output correction, not disc
content decryption or a replacement firmware.

## Source and verification

Source, exact templates and bounded PPU instruction tests are included.
See [build instructions](docs/BUILD.md), [technical scope](docs/TECHNICAL.md),
[provenance](PROVENANCE.md) and [verification](VERIFICATION.json).
No Sony firmware/SDK, keys, private runtime logs, console identifiers or RAM dumps
are included. Only required short compatibility fingerprints/protocol templates
are present. Toolchain setup and scetool data are supplied separately.

Search terms: PS3 DVD green screen RGB SCART fix, Blu-ray green picture,
AV Multi Out, Evilnat 4.93 CEX, Cobra 8.5, Samsara, Perfect Days, Zodiac.
