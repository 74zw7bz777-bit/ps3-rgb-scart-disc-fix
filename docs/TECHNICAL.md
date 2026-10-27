# Technical scope

Hook sites and original words (Evilnat 4.93 CEX VSH):

| Address | Original | Purpose |
|---|---|---|
| 0x5DC1EC | 7C761B78 | transaction entry |
| 0x5DC300 | 80970800 | outgoing request |
| 0x5DC310 | 60000000 | send result |
| 0x5DC404 | 7F84E378 | reply |
| 0x5DC328 | 7FE307B4 | transaction completion |

Runtime segment addresses are discovered after load, never fixed. Hook branch
range/alignment and original words are checked. Installation/restoration uses
compare-and-swap and cache publication. Adapters retain the original instruction
and continuation, save/restore registers and return through the original path.
The worker sleeps between diagnostics; no network or filesystem I/O occurs in
hooks. The normal runtime contains no network/file logger.

Exact matching requires the complete packet bytes and AVMULTI 0x10. At packet
byte 0x30, a 32-bit 9 becomes 0. At byte 0x4C, 0x00010001 becomes 0. No other
packet words are changed. Input templates are in src/*.bin. No broad format or
policy-byte override. No timer expires the active correction session.

Private control data and a 61056-byte recording area reside in the module RW
segment. The log uses 190 records of 320 bytes plus a 128-byte header. It recycles
a completed 30-transaction block only when consistency conditions hold. Old
records are not a permanent audit history. Native block recycling and multi-day
operation remain unverified; bounded-model tests exercise 305 corrections over
three seeds. Critical loss/consistency conditions request worker rollback.

The guard covers firmware/Cobra and 25 anchors, not cable identity. A detected
fault may disable correction and restore hooks; returning green can therefore
be a deliberate fail-closed outcome. RAM writes consist of the five guarded
instruction sites, the two matched packet words and private stack/module data.
This plugin is NOT read-only, unlike earlier diagnostic prototypes.

Offline tests model a subset of PPU instructions. They do not prove scheduler,
cache, MMU, native loader or arbitrary concurrency behavior. Native visual checks
are separate evidence. The candidate includes synthetic tests, not private raw
captures, RAM dumps, conversation logs, console identifiers or Sony modules.
