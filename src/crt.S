/* Open PS3DK module-info fields, compact management export matching references. */
.section ".rodata.sceModuleInfo","a"
.align 2
.globl __sys_prx_module_info
__sys_prx_module_info:
.short 0
.byte 0,0
.space 28,0
.long .TOC.,__libentstart+4,__libentend,__libstubstart+4,__libstubend
.section ".lib.ent.top","a"
.long 0
.section ".lib.stub.top","a"
.long 0
.section ".rodata.sceExportNID","a"
.align 2
mgmt_nids: .long 0xBC9A0086,0xAB779874,0xD7F43016
.section ".rodata.sceExportAddr","a"
.align 2
mgmt_addrs: .long module_start,module_stop,__sys_prx_module_info
.section ".lib.ent","a"
.byte 0x1c,0
.short 0,0x8000,2,1,0
.long 0,0,mgmt_nids,mgmt_addrs
.globl module_start,module_stop
.set module_start,control_start
.set module_stop,control_stop
