# Build and verification

The supplied `dist` artifact is immutable and hardware tested. Building writes
only inside `src`; it does not replace `dist`. No console connection is involved.

Prerequisites: Python 3.9+, make, GNU Binutils 2.42 patched for PS3 PPU, prx-gen
0.19.0 with the bundled patch, scetool 0.2.9, and test dependencies from
requirements-test.txt. No Sony SDK, C compiler or runtime library is linked.

Pinned sources:
- https://github.com/FirebirdTA01/PS3DK/tree/6bb838ddd788da1a78c6ee34f45000e3a5291edf
- https://github.com/naehrwert/scetool/tree/d78d8986c9ab831f084516f21ecdf87080ac7b78
- https://ftp.gnu.org/gnu/binutils/binutils-2.42.tar.xz

Use the three `patches/ppu/binutils-2.42` patches from pinned PS3DK to build
Binutils with target `powerpc64-ps3-elf`. Apply `toolchain/prx-gen.patch` from the
PS3DK root (`patch -p1 < ...`), then build tools/prx-gen with Cargo in release mode.
The patch is generated against the pinned source, including all local changes;
stock prx-gen output is not assumed equivalent. Honor upstream licenses when
building/distributing hosttools; none of those host binaries is bundled here.

Set absolute tool paths appropriate to YOUR machine:

```sh
export PPU_AS=/your/toolchain/bin/powerpc64-ps3-elf-as
export PPU_LD=/your/toolchain/bin/powerpc64-ps3-elf-ld
export PPU_OBJDUMP=/your/toolchain/bin/powerpc64-ps3-elf-objdump
export PRX_GEN=/your/tools/prx-gen
export SCETOOL=/your/tools/scetool
export SCETOOL_WORKDIR=/your/private/scetool-workdir
python3 -m pip install -r requirements-test.txt
make verify
```

SCETOOL_WORKDIR must have separately supplied usable scetool data. No keyset,
private keys, curve database or obtaining instructions are distributed. Full
container rebuilding therefore is NOT self-contained with this archive alone.
Do not place that directory inside a public repository.

Expected deterministic decrypted PRX hash:
`dd2ccbc9a0f75b24234bd8310fc7ecbc5aa5bc2ffead392a80313b689d2c0992`.
The build performs SPRX -> scetool -> ELF and requires byte-identical PRX data.
SELF encryption/signing may randomize the SPRX; a different signed container hash
is not itself a code change, nor does it confer hardware validation.

The public regression suite excludes private trace replays and substitutes
synthetic traces and the three-template Samsara regression. The actual source assembly, packet templates and
anchors remain unchanged. The structural audit exercises relocations at two
segment-base pairs and checks imports, exports, OPDs, store scope and continuations.
It does not claim an independent signature proof; scetool roundtrip and native
tested-artifact evidence are distinguished.
