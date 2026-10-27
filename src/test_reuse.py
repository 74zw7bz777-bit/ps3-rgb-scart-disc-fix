from pathlib import Path
import struct,json,itertools
from machine_support import Checked,CPU,LOG,syms
P=Path(__file__).resolve().parent;R=P.parents[1]
A=(P/'start-576.bin').read_bytes();B=(P/'second-480.bin').read_bytes()
def fixed(b):b=bytearray(b);b[48:52]=bytes(4);b[76:80]=bytes(4);return bytes(b)
class RGB(Checked):
 def write(self,a,v,n):
  if a in (0x900034,0x900050):
   assert n==4 and v==0;self.writes.append((a,n));self.put(a,bytes(4));return
  return super().write(a,v,n)
 def packet(self,n=116):return self.bytes(0x900004,n)
 def complete(self,send=0,reply=0,final=0,order=(0x80030001,0x80030003,0x84000001)):
  self.r[3]=send;self.event(3)
  for cid in order:
   self.put(0x910000,struct.pack('>HHII',0x205,8,cid,reply));self.event(4)
  self.r[31]=final;self.event(5)
 def stores(self):return [x for x in self.writes if x[0] in (0x900034,0x900050)]
count=0
for seed in range(3):
 for order in [(A,A,B,A,B,B),(B,A,B,B,A,A)]:
  c=RGB(seed)
  for b in order:c.tx(b);assert c.packet()==fixed(b);c.complete()
  assert c.read(LOG+64,4)==6 and c.read(LOG+88,4)==0 and len(c.stores())==12;count+=1
 for b in [A,B]:
  for i in range(116):
   c=RGB(seed);bad=bytearray(b);bad[i]^=1;c.tx(bad);assert c.packet()==bad and not c.stores() and c.read(LOG+16,4)==0;(count:=count+1)
for gate in ['loss','fault','limit','disabled','busy','cas','race','capacity']:
 c=RGB(4)
 if gate in ['loss','fault','limit','disabled','busy','capacity']:
  off,val={'loss':(12,1),'fault':(88,1),'limit':(64,0xfffffffe),'disabled':(4,0),'busy':(8,1),'capacity':(16,185)}[gate];c.put(LOG+off,val.to_bytes(4,'big'))
 if gate=='cas':c.failcas=True
 if gate=='race':c.disable_on_reserve=True
 c.tx(A);assert not c.stores(),gate;count+=1
for n in [0,1,7,8,115,117,192,2048,2049]:
 c=RGB(5);b=(A+bytes(2049))[:n];c.tx(b,n);assert not c.stores() and c.read(LOG+16,4)==0;count+=1
for fault in ['send','reply','final','missing','duplicate','wrong']:
 c=RGB(6);c.tx(A)
 order={'missing':(0x80030001,0x84000001),'duplicate':(0x80030001,0x80030001,0x84000001),'wrong':(0x80030001,0x80030004,0x84000001)}.get(fault,(0x80030001,0x80030003,0x84000001))
 c.complete(send=fault=='send',reply=fault=='reply',final=fault=='final',order=order)
 assert c.read(LOG+88,4)==1;before=len(c.stores());c.tx(B);assert c.packet()==B and len(c.stores())==before;count+=1
for order in itertools.permutations((0x80030001,0x80030003,0x84000001)):
 c=RGB(7);c.tx(B);c.complete(order=order);assert c.read(LOG+88,4)==0;count+=1
c=RGB(8)
for i in range(65):
 b=[A,B][i%2];c.tx(b);assert c.packet()==fixed(b);c.complete()
assert c.read(LOG+64,4)==65 and c.read(LOG+16,4)==30 and c.read(LOG+124,4)==2 and len(c.stores())==130;count+=1
# 1000 unrelated commands and their callbacks never consume log capacity.
c=RGB(9)
for i in range(1000):
 c.tx(struct.pack('>HHII',0x205,8,0x20002,0));c.complete()
assert c.read(LOG+16,4)==0;c.tx(A);c.complete();assert c.read(LOG+16,4)==6;count+=1
# Transaction identity remains mandatory, overlapping matching TX disables logging.
c=RGB(10);c.tx(A);c.r[22]+=4;c.complete();assert c.read(LOG+16,4)==1
c.tx(B);assert c.read(LOG+48,4)==1 and c.read(LOG+4,4)==0 and len(c.stores())==2;count+=1
# Non-block-aligned high record count cannot be recycled or modified.
c=RGB(11);c.put(LOG+16,(184).to_bytes(4,'big'));c.tx(A);assert not c.stores() and c.read(LOG+100,4)==1;count+=1
# Public synthetic regression; private native traces are intentionally excluded.
c=RGB(12)
for b in (A,B):c.tx(b);c.complete()
c.put(LOG+4,bytes(4));c.put(LOG+8,(1).to_bytes(4,'big'))
(P/'synthetic-perfect-days.bin').write_bytes(c.bytes(LOG,61056))
r={'passed':count+1,'failed':0,'private_native_traces_included':False,'scope':'bounded built-instruction model; synthetic fixtures'}
(P/'reuse-tests.json').write_text(json.dumps(r,indent=2)+'\n');print(json.dumps(r))
