# Installation and deactivation

These are manual instructions, not an automatic installer.
Only use the exact supported firmware and RGB-SCART configuration. Incompatible
runtime code or early boot failures may freeze the system. Back up the boot list
and have a recovery route before enabling autoload. No blanket recovery guarantee.

1. Verify the SPRX SHA-256 against README. Do not use a rebuilt binary as if it
   were the hardware-tested artifact.
2. With playback stopped, preserve the exact current `/dev_hdd0/boot_plugins.txt`
   bytes and store a backup locally and on the HDD. Preserve all other plugins.
3. Transfer the binary to `/dev_hdd0/plugins/disc_rgb_three_153fd84d.sprx` and
   retrieve it again to verify byte identity. Do not overwrite a different file.
4. For a first installation, append that exact path as a single line to the HDD boot list.
   When upgrading, REPLACE the previous RGB plugin line instead; never load both.
   Keep the old binary and the exact old boot list as rollback copies. Ensure a newline
   separates it from the previous entry. Do not add duplicates, comments or quotes.
   Cobra supports six plugin slots; allow for an integrated webMAN slot too.
5. Retrieve and verify the final boot list before restarting. A staged file is
   preferable, but FTP rename-over-existing may be unsupported; do not assume
   rename success and do not delete the live list blindly.
6. Restart normally and check XMB/controller before playing a disc. First test
   should be supervised. No second manual load of an autoloaded instance.

The pinned Cobra source checks `/dev_usb000/boot_plugins.txt` before the HDD
list, not in addition to it. An existing USB list can override the HDD config.
The USB override is source-backed; it was not tested as recovery on this setup.
Do not rely on an undocumented button combination or on network access surviving
a boot hang. The examined safe-mode code can rename flash stage2 files and is
not recommended here as a harmless plugin bypass.

## Disable

Remove ONLY `/dev_hdd0/plugins/disc_rgb_three_153fd84d.sprx` from the effective
boot list, preserving webMAN and all other entries. Read back and verify, then
restart normally. This prevents subsequent loading. A stale backup must not
replace newer unrelated boot-list changes.
Removing the entry does not terminate an already running instance. Normal reboot
is the recommended end of its lifetime. The SPRX file can remain harmlessly on HDD
without an autoload entry. Do not remove files belonging to other plugins.

## Advanced stop behavior

A regular Cobra stop request can cancel the worker, which restores five original
instructions and freezes recording. The module intentionally refuses hot unload
so late callers cannot execute freed code. Native observed return was
0xffffffff80011138 with verified phase=6/done=1 and all five original words.
That error code alone is NOT a successful-stop check. Never force-unload or repeat
stop requests blindly. Determine slot by exact name/path, not hard-coded slot 2.

Disable before firmware updates or changing output/cable configuration. This
release does not automatically adapt to other firmware versions.
