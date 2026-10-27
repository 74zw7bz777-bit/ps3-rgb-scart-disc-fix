.macro imm reg,value
 lis \reg,(\value >> 16)
 ori \reg,\reg,(\value & 65535)
.endm
.macro status value
 li 0,\value
 stw 0,20(31)
 sync
.endm
.macro loadread address,dest,size=4
 imm 3,\address
 addi 4,31,\dest
 li 5,\size
 bl readmem
 cmpwi 3,0
 bne reject
.endm
.section ".opd","aw"
.align 2
.globl control_start,control_stop
control_start: .long start_code,.TOC.
control_stop: .long stop_code,.TOC.
worker_opd: .long worker_code,.TOC.
.text
.align 2
.globl start_code,stop_code
start_code:
 stdu 1,-128(1)
 mr 31,2
 li 0,1
 stw 0,500(31)
 addi 3,31,512
 lwz 4,528(31)
 li 5,0
 li 6,1000
 lis 7,1
 li 8,1
 lwz 9,540(31)
 lwz 12,532(31)
 lwz 12,0(12)
 lwz 0,0(12)
 std 2,40(1)
 lwz 2,4(12)
 mtctr 0
 bctrl
 ld 2,40(1)
 stw 3,504(31)
 cmpwi 3,0
 bne create_failed
 li 0,2
 stw 0,500(31)
 b bootstrap_exit
create_failed:
 li 0,0xe0
 stw 0,500(31)
bootstrap_exit:
 sync
 li 3,0
 li 11,41
 sc
 li 0,0xe1
 stw 0,500(31)
 b exit_failed
stop_code:
 mr 31,2
 li 0,1
 stw 0,508(31)
 sync
 /* Fail phase2 deliberately: mapped adapters MUST survive delayed callers.
  * Native state5 prevents regular unload, including Cobra's following unload. */
 lwz 3,536(31)
 li 11,461
 sc
 cmpwi 3,0
 ble stop_exit
 li 4,0
 addi 5,31,544
 li 11,482
 sc
 stw 3,592(31)
stop_exit:
 li 3,0
 li 11,41
 sc
exit_failed:
 imm 3,1000000
 li 11,141
 sc
 b exit_failed
worker_code:
 stdu 1,-256(1)
 mr 31,2
 status 1
 li 11,1
 sc
 stw 3,28(31)
 /* Firmware checks write results only to our own buffer. */
 li 3,0x7777
 li 4,0x14
 li 11,8
 sc
 cmpwi 3,0x493
 bne guard_error
 li 3,0x7777
 li 4,0x13
 addi 5,31,432
 li 11,8
 sc
 cmpwi 3,0
 bne reject
 lwz 9,432(31)
 imm 10,0x43455820
 cmpw 9,10
 bne guard_error
 lwz 9,436(31)
 imm 10,0x434f4252
 cmpw 9,10
 bne guard_error
 lhz 9,440(31)
 cmpwi 9,0x4100
 bne guard_error
 li 3,0x7001
 addi 4,31,448
 li 11,8
 sc
 cmpwi 3,0
 bne reject
 lhz 9,448(31)
 cmpwi 9,0x850
 bne guard_error
 addi 30,31,1024
 li 29,ANCHOR_COUNT
anchor_loop:
 lwz 3,0(30)
 addi 4,31,452
 li 5,16
 bl readmem
 cmpwi 3,0
 bne reject
 addi 3,30,4
 addi 4,31,452
 li 5,16
 bl equal
 cmpwi 3,0
 bne guard_error
 lwz 9,32(31)
 addi 9,9,1
 stw 9,32(31)
 addi 30,30,20
 addic. 29,29,-1
 bne anchor_loop
 status 2
 /* Preflight all five sites before publishing any branch. */
 addi 30,31,2048
 li 29,5
preflight:
 lwz 3,0(30)
 addi 4,31,640
 li 11,351
 sc
 cmpwi 3,0
 bne permission_error
 ld 9,640(31)
 imm 10,0x40000
 cmpd 9,10
 bne permission_error
 ld 9,648(31)
 andi. 9,9,8
 beq permission_error
 lwz 3,0(30)
 lwz 9,0(3)
 lwz 10,4(30)
 cmpw 9,10
 bne guard_error
 lwz 9,8(30)
 subf 10,3,9
 andi. 0,10,3
 bne range_error
 imm 11,0x02000000
 add 12,10,11
 cmpld 12,11
 /* signed range tested by unsigned (delta + 32MiB) < 64MiB */
 imm 11,0x04000000
 cmpld 12,11
 bge range_error
 imm 11,0x03fffffc
 and 10,10,11
 oris 10,10,0x4800
 stw 10,12(30)
 addi 30,30,24
 addic. 29,29,-1
 bne preflight
 lwz 0,508(31)
 cmpwi 0,0
 bne finish
 /* Fail-closed lifetime pin, even when first CAS fails. */
 li 0,1
 stw 0,608(31)
 sync
 status 3
 addi 30,31,2048
 li 29,5
install_loop:
 lwz 3,0(30)
 lwz 4,4(30)
 lwz 5,12(30)
 bl swap_instruction
 stw 3,20(30)
 cmpwi 3,0
 bne install_error
 li 0,1
 stw 0,16(30)
 addi 30,30,24
 addic. 29,29,-1
 bne install_loop
 /* All immutable adapters published before capture is enabled. */
 lwz 27,616(31)
 sync
 li 0,1
 stw 0,4(27)
 sync
 status 4
 li 28,-1
 stw 28,624(31)
observe_loop:
 lwz 0,12(27)
 cmpwi 0,0
 bne rollback
 lwz 0,88(27)
 cmpwi 0,0
 bne rollback
 lwz 0,100(27)
 cmpwi 0,0
 bne rollback
 lwz 0,20(27)
 cmpwi 0,0
 bne rollback
 lwz 0,508(31)
 cmpwi 0,0
 bne rollback
 imm 3,1000000
 bl usleep
 cmpwi 3,0
 bne sleep_error
 lwz 9,56(27)
 addi 9,9,1
 stw 9,56(27)
 b observe_loop
permission_error: li 0,2
 b failed
range_error: li 0,3
 b failed
guard_error: li 0,1
 b failed
reject: li 0,4
failed:
 stw 0,24(31)
 status 0xe0
 b finish
install_error:
 li 0,5
 stw 0,24(31)
 b rollback
sleep_error:
 li 0,6
 stw 0,24(31)
rollback:
 lwz 27,616(31)
 li 0,0
 stw 0,4(27)
 sync
 status 5
 addi 30,31,2144
 li 29,5
restore_loop:
 lwz 0,16(30)
 cmpwi 0,1
 bne next_restore
 lwz 3,0(30)
 lwz 4,12(30)
 lwz 5,4(30)
 bl swap_instruction
 stw 3,20(30)
 cmpwi 3,0
 bne restore_conflict
 li 0,0
 stw 0,16(30)
 b next_restore
restore_conflict:
 li 0,7
 stw 0,24(31)
next_restore:
 addi 30,30,-24
 addic. 29,29,-1
 bne restore_loop
 /* Drain private logger only; never wait for AV locks. Disabled late arrivals
  * recheck enabled after acquiring this lock, and cannot append records. */
 li 28,100
freeze_loop:
 addi 10,27,8
 lwarx 9,0,10
 cmpwi 9,0
 bne freeze_wait
 li 9,1
 stwcx. 9,0,10
 bne freeze_wait
 isync
 li 0,1
 stw 0,620(31)
 /* Keep lock closed permanently; no buffer reuse. */
 status 6
 b finish
freeze_wait:
 imm 3,10000
 bl usleep
 addic. 28,28,-1
 bne freeze_loop
 li 0,8
 stw 0,24(31)
 status 0xe1
finish:
 sync
 li 0,1
 stw 0,588(31)
 li 3,0
 li 11,41
 sc
 b exit_failed
/* Only writer of Sony memory. One aligned conditional word store.
 * r3=site,r4=expected,r5=replacement. Bounded retries, no blind overwrite. */
.globl swap_instruction
swap_instruction:
 li 8,16
 sync
swap_retry:
 lwarx 9,0,3
 cmpw 9,4
 bne swap_conflict
 stwcx. 5,0,3
 bne swap_again
 dcbst 0,3
 sync
 icbi 0,3
 sync
 isync
 lwz 9,0(3)
 cmpw 9,5
 bne swap_conflict
 li 3,0
 blr
swap_again:
 addic. 8,8,-1
 bne swap_retry
 li 3,2
 blr
swap_conflict:
 li 3,1
 blr
readmem:
 stw 3,600(31)
 stw 5,604(31)
 imm 10,0x10000
 cmplw 3,10
 blt read_bad
 cmpwi 5,0
 ble read_bad
 cmplwi 5,64
 bgt read_bad
 add 9,3,5
 imm 10,0x30000000
 cmpld 9,10
 bgt read_bad
 mr 8,5
 mr 7,4
 mr 6,3
 lwz 5,28(31)
 li 4,0x31
 li 3,0x7777
 li 11,8
 mflr 0
 stdu 1,-128(1)
 std 0,144(1)
 std 2,40(1)
 sc
 ld 2,40(1)
 ld 0,144(1)
 addi 1,1,128
 mtlr 0
 blr
read_bad:
 li 3,-103
 blr
/* Return zero on equal; reads only. */
equal:
 mtctr 5
1: lbz 9,0(3)
 lbz 10,0(4)
 cmpw 9,10
 bne 2f
 addi 3,3,1
 addi 4,4,1
 bdnz 1b
 li 3,0
 blr
2: li 3,1
 blr
usleep:
 mflr 0
 stdu 1,-128(1)
 std 0,144(1)
 std 2,40(1)
 li 11,141
 sc
 ld 2,40(1)
 ld 0,144(1)
 addi 1,1,128
 mtlr 0
 blr
