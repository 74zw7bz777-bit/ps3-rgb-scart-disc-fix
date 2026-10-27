#!/usr/bin/env python3
"""Execute assembled core in a deliberately bounded integer-PPU model.
Not a cache, scheduler, MMU or native loader proof. Unsupported ops fail closed.
"""
import sys,re,random,json,struct,hashlib
from pathlib import Path
P=Path(__file__).resolve().parent
from elftools.elf.elffile import ELFFile
from capstone import *
with (P/'linked.elf').open('rb') as f:
 e=ELFFile(f);sections={n:e.get_section_by_name(n) for n in ['.text','.data']};img={s['sh_addr']:s.data() for s in sections.values()};syms={s.name:s['st_value'] for s in e.get_section_by_name('.symtab').iter_symbols()}
 code={i.address:(i.mnemonic,i.op_str) for i in Cs(CS_ARCH_PPC,CS_MODE_64|CS_MODE_BIG_ENDIAN).disasm(sections['.text'].data(),sections['.text']['sh_addr'])}
LOG=syms['capture_log'];MASK=(1<<64)-1
def signed(v,b=64):v&=(1<<b)-1;return v-(1<<b) if v>>(b-1) else v
class CPU:
 def __init__(self,seed):
  rr=random.Random(seed);self.r=[rr.getrandbits(64) for _ in range(32)];self.r[1]=0x800000;self.r[3]=0x900000;self.r[22]=0x900000;self.r[23]=0x900004;self.r[28]=0x910000
  self.s={x:rr.getrandbits(32 if x in ['cr','xer'] else 64) for x in ['lr','ctr','cr','xer']};self.mem={};self.writes=[];self.failcas=False;self.disable_on_reserve=False
  for a,b in img.items():self.put(a,b)
  self.put(0x900004,bytes(range(256))*8);self.put(0x900804,(24).to_bytes(4,'big'));self.put(0x910000,bytes.fromhex('020500088400000100000003'))
  self.put(LOG+4,(1).to_bytes(4,'big'))
 def put(self,a,b):self.mem.update({a+i:v for i,v in enumerate(b)})
 def read(self,a,n):return int.from_bytes(bytes(self.mem[a+i] for i in range(n)),'big')
 def write(self,a,v,n):
  assert (0x800000-512<=a and a+n<=0x800000) or (LOG<=a and a+n<=LOG+61056),hex(a)
  self.writes.append((a,n));self.put(a,(v&((1<<(8*n))-1)).to_bytes(n,'big'))
 def run(self,entry,ret):
  pc=entry
  for step in range(20000):
   if pc==ret:return step
   m,o=code[pc];args=[a.strip() for a in o.split(',')];n=pc+4
   def reg(a):return int(a[1:])
   def rv(a):return self.r[reg(a)]
   def iv(a):return int(a,0)
   def dst(v):self.r[reg(args[0])]=v&MASK
   def ea(a):z=re.fullmatch(r'(-?(?:0x[0-9a-f]+|\d+))\(r(\d+)\)',a);return (int(z[1],0)+self.r[int(z[2])])&MASK
   if m in ['std','stw','stb','stdu']:
    a=ea(args[1]);self.write(a,rv(args[0]),{'std':8,'stdu':8,'stw':4,'stb':1}[m])
    if m=='stdu':self.r[int(args[1].split('(r')[1][:-1])]=a
   elif m in ['ld','lwz','lbz','lhz']:dst(self.read(ea(args[1]),{'ld':8,'lwz':4,'lbz':1,'lhz':2}[m]))
   elif m in ['mflr','mfctr','mfcr','mfxer']:dst(self.s[m[2:]])
   elif m in ['mtlr','mtctr','mtxer']:self.s[m[2:]]=rv(args[0])
   elif m=='mtcrf':assert iv(args[0])==255;self.s['cr']=rv(args[1])&0xffffffff
   elif m=='mr':dst(rv(args[1]))
   elif m=='li':dst(iv(args[1]))
   elif m=='lis':dst(iv(args[1])<<16)
   elif m=='addi':dst((0 if args[1]=='0' else rv(args[1]))+iv(args[2]))
   elif m=='add':dst(rv(args[1])+rv(args[2]))
   elif m=='ori':dst(rv(args[1])|iv(args[2]))
   elif m=='mulli':dst(signed(rv(args[1]))*iv(args[2]))
   elif m=='slwi':dst((rv(args[1])<<iv(args[2]))&0xffffffff)
   elif m=='extsw':dst(signed(rv(args[1]),32))
   elif m in ['cmpwi','cmpdi','cmplwi']:
    a=rv(args[0]);a=(a&0xffffffff) if m=='cmplwi' else signed(a,32 if m=='cmpwi' else 64);b=iv(args[1]);v=8 if a<b else 4 if a>b else 2
    self.s['cr']=(self.s['cr']&0xfffffff)|((v|((self.s['xer']>>31)&1))<<28)
   elif m in ['b','ba','bl']:
    if m=='bl':self.s['lr']=n
    n=iv(args[0])
   elif m=='blr':n=self.s['lr']
   elif m in ['beq','bne','bge','bgt','blt']:
    cr=self.s['cr']>>28;yes={'beq':bool(cr&2),'bne':not cr&2,'bge':not cr&8,'bgt':bool(cr&4),'blt':bool(cr&8)}[m]
    if yes:n=iv(args[0])
   elif m=='bdnz':
    self.s['ctr']=(self.s['ctr']-1)&MASK
    if self.s['ctr']:n=iv(args[0])
   elif m=='lwarx':
    if self.disable_on_reserve:self.put(LOG+4,bytes(4))
    dst(self.read(rv(args[2]),4))
   elif m=='stwcx.':
    if not self.failcas:self.write(rv(args[2]),rv(args[0]),4)
    self.s['cr']=(self.s['cr']&0xfffffff)|(((0 if self.failcas else 2)|((self.s['xer']>>31)&1))<<28)
   elif m in ['sync','isync','lwsync','nop']:pass
   else:raise AssertionError((hex(pc),m,o))
   pc=n
  raise AssertionError('step limit')
