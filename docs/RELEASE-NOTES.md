# PS3 RGB-SCART DVD & Blu-ray Color Fix

Corrects known AVMULTI color-mode requests so supported DVD and Blu-ray playback
through the original Sony player retains correct colors on an RGB-SCART display.
Supports known startup/subsequent mode changes, repeated playback and HDD autoload
on the tested configuration. See [test details](TESTING.md) for the films and build
history behind these observations.

## Current technical revision

The existing release tag remains `v0.2.0` to identify the unchanged tested binary.
Three exact 116-byte request templates are recognized. The third covers an
additional 480-line mode variant; the two existing RGB field edits are unchanged.
Copy-control/signaling fields are preserved. The binary and its SHA-256 have not
changed with this documentation update.

Firmware-specific experimental release: Evilnat 4.93 CEX / Cobra 8.5, PS3 Slim,
RGB-SCART. No universal compatibility or official affiliation is claimed.
