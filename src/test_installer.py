#!/usr/bin/env python3
"""Limited instruction replay of built code with mocked VSH/syscalls.
Not a PPU emulator certification or real AV test. Rejects unmodelled opcodes.
Checks failure gates, writes, exact call arguments, rollback and call count.
"""
from pathlib import Path
import re,struct,json
P=Path(__file__).resolve().parent
b=(P/'disc_rgb_three.prx').read_bytes();u64=lambda o:struct.unpack_from('>Q',b,o)[0];u16=lambda o:struct.unpack_from('>H',b,o)[0]
ph=[struct.unpack_from('>IIQQQQQQ',b,u64(32)+i*56) for i in range(u16(56))];loads=[x for x in ph if x[0]==1];db=loads[1][3]
ins={}
for line in (P/'disassembly.txt').read_text().splitlines():
 m=re.match(r'\s*([0-9a-f]+):\s+((?:[0-9a-f]{2} ){3}[0-9a-f]{2})\s+([\w.]+)\s*(.*)',line)
 if m:
  a=int(m[1],16)
  assert b[loads[0][2]+a:loads[0][2]+a+4]==bytes.fromhex(m[2])
  ins[a]=(m[3],m[4].split('<')[0].strip())
worker_entry=int(re.search(r'([0-9a-f]+) <worker_code>:',(P/'disassembly.txt').read_text())[1],16)
mask=(1<<64)-1
class Exit(Exception):pass
class Machine:
 def __init__(self,case):
  self.case=case;self.mem={};self.reg=[0]*32;self.pc=worker_entry;self.lr=0;self.ctr=0;self.cmp=0;self.calls=[];self.sleeps=0;self.gets=0;self.remote_reads=0;self.min_sp=0x1000000
  self.reg[1]=0x1000000;self.reg[2]=db
  for x in loads:self.raw(x[3],b[x[2]:x[2]+x[5]]+bytes(x[6]-x[5]))
  for a in json.loads((P/'anchors.json').read_text()):self.raw(int(a['address'],16),bytes.fromhex(a['bytes']))
  if case.startswith('anchor:'):
   a=json.loads((P/'anchors.json').read_text())[int(case.split(':')[1])];self.mem[int(a['address'],16)]^=1
  self.target_writes=[];self.cache=[];self.swap_attempts=0
  self.sites=[int(x['va'],16) for x in json.loads((P/'sites.json').read_text())['sites']]
  if case.startswith('delta:'):self.word(db+2048+8,(self.sites[0]+int(case.split(':')[1]))&0xffffffff)
  if case=='range':self.word(db+2048+8,0x10000000)
 def raw(self,a,v):
  for i,x in enumerate(v):self.mem[a+i]=x
 def word(self,a,v):self.raw(a,(v&0xffffffff).to_bytes(4,'big'))
 def read(self,a,n):return bytes(self.mem.get(a+i,0) for i in range(n))
 def private(self,a,n):assert db<=a and a+n<=db+loads[1][6] or 0x1000000-4096<=a and a+n<=0x1000000+64,hex(a)
 def write(self,a,n,v):self.private(a,n);self.raw(a,(v&((1<<(n*8))-1)).to_bytes(n,'big'))
 def syscall(self):
  r=self.reg;n=r[11];ret=0
  if n==1:ret=0x1000300
  elif n==41:raise Exit()
  elif n==141:
   self.sleeps+=1
   if self.sleeps==1201:self.word(db+508,1) # model external orderly module_stop request
   if self.case.startswith('fault:') and self.sleeps==1:
    log=int.from_bytes(self.read(db+616,4),'big');self.word(log+int(self.case.split(':')[1]),1)
   if self.case=='capacity' and self.sleeps==1:
    log=int.from_bytes(self.read(db+616,4),'big');self.word(log+20,1);self.word(log+4,0)
   if self.case=='stop' and self.sleeps==3:self.word(db+508,1)
   if self.case=='sleep_fail':ret=-1
   if self.case=='foreign' and self.sleeps==1:self.word(self.sites[2],0x60000001)
  elif n==351:
   assert r[3] in self.sites
   self.write(r[4],8,0x80000 if self.case=='readonly' else 0x40000)
   self.write(r[4]+8,8,0 if self.case=='noaccess' else 8)
   self.write(r[4]+16,8,0x100000000000)
   if self.case=='pagefail':ret=-1
  elif n==461:ret=123
  elif n==482:
   assert r[3]==123 and r[4]==0
   assert struct.unpack('>5Q',self.read(r[5],40))==(40,2,0,1,0)
   self.stop_phase=True;ret=0x80011136
  elif n==8:
   if r[3]==0x7001:self.write(r[4],2,0x840 if self.case=='cobra' else 0x850)
   else:
    assert r[3]==0x7777
    if r[4]==0x14:ret=0x492 if self.case=='firmware' else 0x493
    elif r[4]==0x13:
     self.private(r[5],10);self.raw(r[5],b'DEX COBRA\0' if self.case=='dex' else b'CEX COBRA\0')
    elif r[4]==0x31:
     self.remote_reads+=1;self.private(r[7],r[8]);self.raw(r[7],self.read(r[6],r[8]))
     if self.case=='mem_fail':ret=-1
    else:raise AssertionError(('ps3mapi',r[4]))
  else:raise AssertionError(('syscall',n))
  r[3]=ret&mask
 def external(self,target):
  r=self.reg;assert target==0x123450 and r[2]==0x123000
  assert r[3]==db+512 and r[5:9]==[0,1000,65536,1]
  assert int.from_bytes(self.read(r[4],4),'big')==worker_entry
  assert int.from_bytes(self.read(r[4]+4,4),'big')==db
  self.create_checked=True;r[3]=0 if self.case=='start_ok' else 0x80010004
 def run(self):
  try:
   for steps in range(50000):
    op,arg=ins[self.pc];parts=[x.strip() for x in arg.split(',')];nxt=self.pc+4;r=self.reg
    ix=lambda s:int(s[1:]);val=lambda s:r[ix(s)]
    if op in ('li','lis'):r[ix(parts[0])]=(int(parts[1])<<(16 if op=='lis' else 0))&mask
    elif op=='mr':r[ix(parts[0])]=val(parts[1])
    elif op in ('ori','oris'):r[ix(parts[0])]=(val(parts[1])|(int(parts[2])<<(16 if op=='oris' else 0)))&mask
    elif op in ('addi','addic.'):r[ix(parts[0])]=(val(parts[1])+int(parts[2]))&mask;self.cmp=(r[ix(parts[0])]>0) if op=='addic.' else self.cmp
    elif op=='add':r[ix(parts[0])]=(val(parts[1])+val(parts[2]))&mask
    elif op=='subf':r[ix(parts[0])]=(val(parts[2])-val(parts[1]))&mask
    elif op=='andi.':
     r[ix(parts[0])]=val(parts[1])&int(parts[2]);self.cmp=int(r[ix(parts[0])]!=0)
    elif op=='and':r[ix(parts[0])]=val(parts[1])&val(parts[2])
    elif op in ('cmpwi','cmpw','cmplwi','cmplw','cmpld','cmpd'):
     a=val(parts[0]);c=int(parts[1]) if op.endswith('i') else val(parts[1]);bits=64 if op in ('cmpld','cmpd') else 32;a&=(1<<bits)-1;c&=(1<<bits)-1
     if op.startswith('cmpw'):a=a-(1<<32) if a>>31 else a;c=c-(1<<32) if c>>31 else c
     self.cmp=(a>c)-(a<c)
    elif op in ('lwz','ld','lhz','lbz','std','stw','stdu'):
     m=re.fullmatch(r'(-?\d+)\(r(\d+)\)',parts[1]);base=int(m[2]);a=(r[base]+int(m[1]))&mask;n={'lwz':4,'ld':8,'lhz':2,'lbz':1,'std':8,'stw':4,'stdu':8}[op]
     if op.startswith('st'):self.write(a,n,val(parts[0]))
     else:r[ix(parts[0])]=int.from_bytes(self.read(a,n),'big')
     if op=='stdu':r[base]=a;self.min_sp=min(self.min_sp,a)
    elif op=='mflr':r[ix(parts[0])]=self.lr
    elif op=='mtlr':self.lr=val(parts[0])
    elif op=='mtctr':self.ctr=val(parts[0])
    elif op=='bctrl':self.lr=nxt;self.external(self.ctr)
    elif op=='blr':nxt=self.lr
    elif op in ('b','bl','beq','bne','blt','bgt','ble','bge','bdnz'):
     yes={'b':True,'bl':True,'beq':self.cmp==0,'bne':self.cmp!=0,'blt':self.cmp<0,'bgt':self.cmp>0,'ble':self.cmp<=0,'bge':self.cmp>=0}
     if op=='bdnz':self.ctr-=1;take=self.ctr!=0
     else:take=yes[op]
     if take:
      if op=='bl':self.lr=nxt
      nxt=int(parts[0],16)
    elif op=='sc':self.syscall()
    elif op=='lwarx':r[ix(parts[0])]=int.from_bytes(self.read(val(parts[2]),4),'big')
    elif op=='stwcx.':
     a=val(parts[2]);v=val(parts[0]);fail=False
     if a in self.sites:
      fail=self.case==('cas:'+str(self.sites.index(a))) and len(self.target_writes)==self.sites.index(a)
      if not fail:
       assert self.pc in [int(re.search(r'([0-9a-f]+) <swap_retry>:',(P/'disassembly.txt').read_text())[1],16)+12]
       self.target_writes.append((a,v));self.word(a,v)
     else:
      fail=self.case=='freeze_busy'
      if not fail:self.write(a,4,v)
     self.cmp=1 if fail else 0
    elif op in ('dcbst','icbi'):self.cache.append((op,val(parts[1])))
    elif op in ('hwsync','sync','isync','lwsync','nop'):pass
    else:raise AssertionError((hex(self.pc),op,arg))
    self.pc=nxt
   raise AssertionError('step limit')
  except Exit:pass
  status=int.from_bytes(self.read(db+20,4),'big');err=int.from_bytes(self.read(db+24,4),'big')
  return {'case':self.case,'status':hex(status),'error':hex(err),'target_writes':self.target_writes,'cache_ops':len(self.cache),'plugin_stack_bytes_excluding_VSH':0x1000000-self.min_sp,'steps':steps}

results=[]
cases=['fault:12','fault:88','fault:100','ok','capacity','firmware','cobra','dex','mem_fail','readonly','noaccess','pagefail','range','stop','sleep_fail','foreign','freeze_busy','delta:-5242880','delta:33554428','delta:33554432','delta:2']+['anchor:'+str(i) for i in range(25)]+['cas:'+str(i) for i in range(5)]
for case in cases:
 m=Machine(case);r=m.run();results.append(r)
 if case.startswith('delta:') and int(case.split(':')[1]) in (-5242880,33554428):
  d=int(case.split(':')[1]);assert m.target_writes[0][1]==0x48000000|(d&0x03fffffc) and r['status']=='0x6',r
 elif case=='ok':assert r['status']=='0x6' and len(m.target_writes)==10 and m.sleeps==1201 and int.from_bytes(m.read(db+624,4),'big')==0xffffffff,r
 elif case.startswith('fault:'):assert r['status']=='0x6' and len(m.target_writes)==10 and m.sleeps==1,r
 elif case=='capacity':assert r['status']=='0x6' and len(m.target_writes)==10 and m.sleeps==1,r
 elif case in ('stop','sleep_fail'):assert r['status']=='0x6' and len(m.target_writes)==10,r
 elif case=='foreign':assert r['error']=='0x7' and int.from_bytes(m.read(m.sites[2],4),'big')==0x60000001,r
 elif case=='freeze_busy':assert r['error']=='0x8',r
 elif case.startswith('cas:'):assert r['error']=='0x5' and len(m.target_writes)==2*int(case.split(':')[1]),r
 else:assert r['status']=='0xe0' and not m.target_writes,r
 assert len(m.cache)==2*len(m.target_writes),r
 if case!='foreign':
  for q in json.loads((P/'sites.json').read_text())['sites']:
   # corrupted guard fixtures remain corrupted, but installer never writes them.
   if not case.startswith('anchor:'):assert m.read(int(q['va'],16),4).hex()==q['original'],r
# Actual stop instructions must submit phase2 FAIL=1, never success/unload.
m=Machine('ok');m.pc=int(re.search(r'([0-9a-f]+) <stop_code>:',(P/'disassembly.txt').read_text())[1],16);m.run();assert m.stop_phase and not m.target_writes
results.append({'case':'stop_phase2_refusal','pass':True})
for case in ['start_ok','start_failed']:
 m=Machine(case)
 slot=int.from_bytes(m.read(db+532,4),'big');m.word(slot,0x123400);m.word(0x123400,0x123450);m.word(0x123404,0x123000)
 m.pc=int(re.search(r'([0-9a-f]+) <start_code>:',(P/'disassembly.txt').read_text())[1],16)
 m.run();assert m.create_checked and not m.target_writes
 assert int.from_bytes(m.read(db+500,4),'big')==(2 if case=='start_ok' else 0xe0)
 results.append({'case':case,'pass':True})
(P/'installer-tests.json').write_text(json.dumps({'result':'PASS','scope':'assembled instruction replay, syscall/cache/atomic effects modeled; not hardware validation','cases':results},indent=2))
print('PASS',len(results),'installer/stop instruction-replay cases')
