#!/usr/bin/env python3
"""Independent stdlib-only artifact audit. No original checker/imports, no network."""
import struct,json,hashlib,collections
from pathlib import Path
P=Path(__file__).resolve().parent;R=P.parents[1]
hashof=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
U16=lambda b,o:struct.unpack_from('>H',b,o)[0]
U32=lambda b,o:struct.unpack_from('>I',b,o)[0]
U64=lambda b,o:struct.unpack_from('>Q',b,o)[0]
def parse(path):
 b=path.read_bytes(); assert b[:8]==bytes.fromhex('7f454c4602020166')
 assert U16(b,16)==0xffa4 and U16(b,18)==21
 ph=[struct.unpack_from('>IIQQQQQQ',b,U64(b,32)+56*i) for i in range(U16(b,56))]
 loads=[x for x in ph if x[0]==1]
 def off(va):
  for x in loads:
   if x[3]<=va<x[3]+x[5]:return x[2]+va-x[3]
  raise ValueError(hex(va))
 mi=loads[0][4];toc,es,ee,ins,ine=struct.unpack_from('>5I',b,mi+32)
 def tab(lo,hi):
  res=[]
  while lo<hi:
   o=off(lo);sz=b[o];assert sz in (28,44)
   attr,nf,nv=struct.unpack_from('>HHH',b,o+4);name,nid,adr=struct.unpack_from('>III',b,o+16)
   res.append({'address':hex(lo),'size':sz,'attributes':hex(attr),'library':b[off(name):].split(b'\0')[0].decode() if name else None,'functions':nf,'variables':nv,'nids':[hex(U32(b,off(nid)+i*4)) for i in range(nf+nv)],'addresses':[hex(U32(b,off(adr)+i*4)) for i in range(nf+nv)]});lo+=sz
  assert lo==hi
  return res
 rel=[]
 for x in ph:
  assert x[2]+x[5]<=len(b)
  if x[0]==0x700000a4:
   assert x[5]%24==0
   rel += [struct.unpack_from('>QHBBIQ',b,o) for o in range(x[2],x[2]+x[5],24)]
 info={'path':str(path.relative_to(R)),'sha256':hashof(path),'elf_flags':hex(U32(b,48)),'shoff':U64(b,40),'shnum':U16(b,60),'segments':[{'type':hex(x[0]),'flags':hex(x[1]),'offset':hex(x[2]),'vaddr':hex(x[3]),'paddr':hex(x[4]),'filesz':x[5],'memsz':x[6],'align':x[7], 'PPU_permissions':x[1]&7,'SPU_permissions':(x[1]>>20)&7,'RSX_permissions':(x[1]>>24)&7} for x in ph],'module_name':b[mi+4:mi+32].split(b'\0')[0].decode(),'module_attributes':U16(b,mi),'module_version':list(b[mi+2:mi+4]),'module_info_offset':hex(mi),'toc':hex(toc),'exports':tab(es,ee),'imports':tab(ins,ine),'relocation_types':dict(collections.Counter(x[4] for x in rel))}
 return b,ph,rel,info
