"""Exact third-template regression using the assembled bounded PPU model."""
from pathlib import Path
import json,itertools,struct
from analyze import analyze
P=Path(__file__).resolve().parent
ns={'__file__':str(P/'test_reuse.py')};exec((P/'test_reuse.py').read_text().split('count=0')[0],ns)
RGB,LOG,A,B,fixed=[ns[x] for x in ('RGB','LOG','A','B','fixed')];C=(P/'samsara-480.bin').read_bytes();cases=0
assert [i for i,(x,y) in enumerate(zip(B,C)) if x!=y]==[114]
for seed in range(3):
 for order in itertools.permutations((A,B,C)):
  c=RGB(seed)
  for b in order:
   c.tx(b);assert c.packet()==fixed(b);assert c.packet()[100:]==b[100:];c.complete()
  assert c.read(LOG+80,4)==1 and c.read(LOG+84,4)==2 and c.read(LOG+88,4)==0
  c.put(LOG+4,bytes(4));c.put(LOG+8,(1).to_bytes(4,'big'))
  report=analyze(c.bytes(LOG,61056));assert report['total_corrections']==3
  assert {t['template'] for t in report['transactions']}=={1,2,3};cases+=1
# Every other signaling-byte value rejected; no broad mask of CGMS.
for byte in range(256):
 c=RGB(4);v=bytearray(C);v[114]=byte;c.tx(v)
 if byte in (4,52):assert c.packet()==fixed(v) and len(c.stores())==2
 else:assert c.packet()==v and not c.stores() and c.read(LOG+16,4)==0
 cases+=1
# Every single-bit change of the complete new packet must be rejected.
for i in range(116):
 for bit in range(8):
  c=RGB(5);v=bytearray(C);v[i]^=1<<bit;c.tx(v)
  assert not c.stores() and c.packet()==v and c.read(LOG+16,4)==0,(i,bit);cases+=1
# Fault/gate/capacity cases on the NEW template.
for mode in ('disabled','busy','cas','race','loss','fault','capacity','counter'):
 c=RGB(6)
 if mode in ('disabled','busy','loss','fault','capacity','counter'):
  off,val={'disabled':(4,0),'busy':(8,1),'loss':(12,1),'fault':(88,1),'capacity':(16,185),'counter':(64,0xfffffffe)}[mode];c.put(LOG+off,val.to_bytes(4,'big'))
 if mode=='cas':c.failcas=True
 if mode=='race':c.disable_on_reserve=True
 c.tx(C);assert c.packet()==C and not c.stores();cases+=1
for fault in ('send','reply','final'):
 c=RGB(7);c.tx(C);c.complete(send=fault=='send',reply=fault=='reply',final=fault=='final')
 assert c.read(LOG+88,4)==1;n=len(c.stores());c.tx(C);assert len(c.stores())==n and c.packet()==C;cases+=1
# Recheck payload after the relevance prefilter but before protected match.
class Changed(RGB):
 def read(self,a,n):
  value=super().read(a,n)
  if getattr(self,'mutate',False) and a==LOG+8 and n==4:
   self.mutate=False;v=bytearray(self.packet());v[115]^=1;self.put(0x900004,v)
  return value
c=Changed(8);c.mutate=True;c.tx(C);assert not c.stores() and c.read(LOG+16,4)==0;cases+=1
# 305 mixed corrections exercise log recycling, retaining true template IDs.
c=RGB(9)
for i in range(305):
 b=(C,A,B)[i%3];c.tx(b);assert c.packet()==fixed(b);c.complete();assert c.read(LOG+88,4)==0;cases+=1
c.put(LOG+4,bytes(4));c.put(LOG+8,(1).to_bytes(4,'big'));assert analyze(c.bytes(LOG,61056))['total_corrections']==305
report={'passed':cases,'failed':0,'new_template':'exact Samsara second mode, byte114=0x34','accepted_480_byte114_values':[4,52],'signaling_preserved':True,'new_AV_store_sites':0,'native_execution':False}
(P/'samsara-tests.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
