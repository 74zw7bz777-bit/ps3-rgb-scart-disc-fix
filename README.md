# PS3 RGB-SCART DVD & Blu-ray Green Screen Fix

**Watch DVDs and Blu-rays with correct colors through the PS3's analog RGB-SCART output.**
This plugin corrects the known color-mode switches that make the picture turn green
when using Sony's original disc player with an RGB-SCART display.

Designed and tested for **Evilnat 4.93 CEX + Cobra 8.5** on a PS3 Slim using
**AV Multi Out with an RGB-SCART cable**. Multiple films have been tested across
DVD and Blu-ray during development, including playback mode changes and HDD autoload.
This is not a guarantee for every disc or firmware; see [test details](docs/TESTING.md).

## Is this the problem you have?

- The XMB and games have normal colors over RGB-SCART.
- Starting a DVD or Blu-ray makes the picture green or gives it a strong green tint.
- Audio and playback otherwise work normally.

The original player can select a YUV output mode that is unsuitable for the RGB-SCART
connection. This fix corrects recognized AV mode requests to RGB, including known
mode changes after playback starts. It runs with the original Sony player; no
replacement media player or flash patch is required.

## Download and install

**[Download the plugin](https://github.com/74zw7bz777-bit/ps3-rgb-scart-disc-fix/releases/tag/v0.2.0)**
then follow **[installation, upgrading and deactivation](docs/INSTALL.md)**.
Cobra can load it automatically at boot from the internal HDD. When upgrading,
replace the previous RGB plugin entry; never load two RGB-fix instances together.

The tested `disc_rgb_three.sprx` is 4537 bytes. SHA-256:
```text
153fd84dacea486b078a74f584190c67b563e60b591cccf1ab758c73ecc2992e
```

## Compatibility and limits

- Tested firmware: **Evilnat 4.93 CEX / Cobra 8.5**. Other firmware is unsupported.
- Tested connection: **RGB-SCART through AV Multi Out**. This is not a general
  HDMI, component/YPbPr, composite or S-Video fix.
- The plugin recognizes specific AV requests, not film titles. It supports three
  known request patterns; unknown patterns pass through and can still appear green.
- A matching request from a game can also match. There is no all-game certification.
- It modifies live VSH instructions. Firmware checks and rollback guards reduce
  risk but do not eliminate freezes. Keep a backup and a recovery route before
  enabling autoload. Disable before firmware updates or changing output hardware.

## Documentation and source

- [Installation and recovery](docs/INSTALL.md)
- [Tested films and hardware evidence](docs/TESTING.md)
- [Technical explanation and limitations](docs/TECHNICAL.md)
- [Build and verification](docs/BUILD.md), [verification report](VERIFICATION.json)
- [Release notes](docs/RELEASE-NOTES.md), [source provenance](PROVENANCE.md)

Source, exact templates and bounded PPU tests are included. No Sony firmware/SDK,
signing keys, private console logs or personal identifiers are distributed.
This is an independent project, not an official Sony, Evilnat or Cobra release.

## Deutsch

**PS3-DVDs und Blu-rays über RGB-SCART ohne Grünstich ansehen:** Der Fix korrigiert
bekannte Farbraum-Umschaltungen des originalen Players am analogen AV Multi Out.
Gedacht für Evilnat 4.93 CEX mit Cobra 8.5. Wenn XMB und Spiele normale Farben haben,
DVDs oder Blu-rays aber grün werden, ist dies das hier behandelte Problem.
Mehrere Filme auf DVD und Blu-ray wurden getestet; unbekannte Disc-Modusvarianten
und andere Firmwareversionen sind damit nicht automatisch abgedeckt.
