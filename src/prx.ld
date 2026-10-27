/* RX/RW PHDR separation follows PSL1GHT lv2.ld. PRX metadata/TOC section
 * placement follows pinned open PS3DK lv2-prx.ld. No process-only headers. */
OUTPUT_FORMAT("elf64-powerpc", "elf64-powerpc", "elf64-powerpc")
OUTPUT_ARCH(powerpc:common64)
PHDRS {
 text PT_LOAD FLAGS(0x00400005);
 data PT_LOAD FLAGS(0x00600006);
 rela 0x700000A4 FLAGS(0);
}
SECTIONS {
 . = 0;
 .rodata.sceModuleInfo : { KEEP(*(.rodata.sceModuleInfo)) } :text
 .text : ALIGN(16) { *(.text .text.*) } :text
 .rodata.sceExportNID : ALIGN(4) { *(.rodata.sceExportNID) } :text
 .rodata.sceExportAddr : ALIGN(4) { *(.rodata.sceExportAddr) } :text
 __libentstart = .;
 .lib.ent.top : { *(.lib.ent.top) } :text
 .lib.ent : { *(.lib.ent) } :text
 __libentend = .;
 __libstubstart = .;
 .lib.stub.top : { *(.lib.stub.top) } :text
 .lib.stub : { *(.lib.stub) } :text
 __libstubend = .;
 .rodata.sceFNID : ALIGN(4) { *(.rodata.sceFNID) } :text
 .rodata.sceResident : ALIGN(4) { *(.rodata.sceResident) } :text
 .rodata : { *(.rodata .rodata.*) } :text
 .rx_pad : { BYTE(0); . = ABSOLUTE(8192); } :text
 . = ALIGN(128);
 .data : { *(.data) } :data
 .data.sceFStub : ALIGN(4) { *(.data.sceFStub) } :data
 .opd : ALIGN(4) { KEEP(*(.opd)) } :data
 /* No GOT/TOC-relative data accesses: explicit mapped RW TOC anchor. */
 .TOC. = ADDR(.data);
 __lv2_got_start = .;
 .got : ALIGN(8) { *(.got .toc) } :data
 __lv2_toc_bias = __lv2_got_start + 0x8000 - .TOC.;
 .bss (NOLOAD) : ALIGN(8) { *(.bss .bss.*) *(COMMON) } :data
 /DISCARD/ : { *(.eh_frame) *(.comment) *(.note.GNU-stack) }
}
