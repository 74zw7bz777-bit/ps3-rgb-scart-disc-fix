# Source provenance and license limitations

This is a source-available experimental release. No blanket license grant is
asserted over third-party-derived material. Original source and technical work
are published for inspection; upstream notices are retained under `licenses/`.

The module CRT and linker script derive their approach from PS3DK runtime and
PSL1GHT layouts. The pinned PS3DK license explicitly covers tools and other listed
areas but does not clearly enumerate runtime/. Coverage of these two runtime
files remains unresolved. This release does not claim that ambiguity is resolved,
and does not apply a blanket MIT license to them or the derived binary.

PS3DK prx-gen modifications are supplied as a patch with its upstream notices.
GNU Binutils, scetool, Capstone and pyelftools are external build/test dependencies;
no hosttool binaries or signing data are bundled. Short firmware compatibility
fingerprints and protocol constants are included, not Sony system modules or SDKs.
