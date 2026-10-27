"""Built-instruction fault injection. No target access, no native concurrency proof."""
from pathlib import Path
import json,struct
P=Path(__file__).resolve().parent
ns={'__file__':str(P/'test_reuse.py')};exec((P/'test_reuse.py').read_text().split('count=0')[0],ns)
RGB=ns['RGB'];LOG=ns['LOG'];A=ns['A'];B=ns['B'];fixed=ns['fixed'];count=0
irrelevant=struct.pack('>HHII',0x205,8,0x20002,0)
def flags(c):return [c.read(LOG+x,4) for x in (12,88,116,120)]
# The original failure mechanism: irrelevant TX/callback hits a busy/failed lock.
# These events must now bypass reservation and cannot poison the next movie start.
for seed in range(8):
 for mode in ('busy','cas'):
  c=RGB(seed);c.tx(A);c.complete();c.tx(B);c.complete()
  if mode=='busy':c.put(LOG+8,(1).to_bytes(4,'big'))
  else:c.failcas=True
  for _ in range(20):c.tx(irrelevant);c.complete()
  assert flags(c)==[0,0,0,0]
  c.put(LOG+8,bytes(4));c.failcas=False
  c.tx(A);assert c.packet()==fixed(A);c.complete();c.tx(B);assert c.packet()==fixed(B);c.complete()
  assert c.read(LOG+64,4)==4 and c.read(LOG+16,4)==24 and flags(c)==[0,0,0,0];count+=1
# Even a malformed/nonmatching116-byte packet cannot acquire a busy private lock.
for i in range(116):
 c=RGB(1);c.put(LOG+8,(1).to_bytes(4,'big'));bad=bytearray(A);bad[i]^=1;c.tx(bad)
 assert flags(c)==[0,0,0,0] and not c.stores();count+=1
# A matching candidate cannot be silently counted as corrected if reservation fails.
for mode in ('busy','cas'):
 for b in (A,B):
  c=RGB(2)
  if mode=='busy':c.put(LOG+8,(1).to_bytes(4,'big'))
  else:c.failcas=True
  c.tx(b);assert c.packet()==b and not c.stores() and flags(c)==[0,0,1,0]
  c.put(LOG+8,bytes(4));c.failcas=False;c.complete() # callbacks of unmodified TX ignored
  c.tx(b);assert c.packet()==fixed(b);c.complete();assert flags(c)==[0,0,1,0] and c.read(LOG+64,4)==1;count+=1
# Foreign callback T/SP/TLS is ignored without acquiring lock, active transaction intact.
for mode in ('busy','cas'):
 for field in ('T','SP','TLS'):
  for event in (3,4,5):
   c=RGB(3);c.tx(A)
   # SP variation uses stored key offset, leaving emulator's fixed-stack bounds intact.
   off={'T':28,'SP':32,'TLS':36}[field];old=c.read(LOG+off,4);c.put(LOG+off,((old+4)&0xffffffff).to_bytes(4,'big'))
   if mode=='busy':c.put(LOG+8,(1).to_bytes(4,'big'))
   else:c.failcas=True
   c.event(event);assert flags(c)==[0,0,0,0] and c.read(LOG+16,4)==1
   c.put(LOG+off,old.to_bytes(4,'big'));c.put(LOG+8,bytes(4));c.failcas=False;c.complete()
   assert flags(c)==[0,0,0,0] and c.read(LOG+16,4)==6;count+=1
# Losing a selected callback MUST poison future corrections (not just logging).
for mode in ('busy','cas'):
 for event in (3,4,5):
  c=RGB(4);c.tx(A)
  if mode=='busy':c.put(LOG+8,(1).to_bytes(4,'big'))
  else:c.failcas=True
  c.event(event);assert c.read(LOG+12,4)==c.read(LOG+120,4)==1 and c.read(LOG+116,4)==0
  c.put(LOG+8,bytes(4));c.failcas=False;c.complete();n=len(c.stores());c.tx(B)
  assert c.packet()==B and len(c.stores())==n;count+=1
# Packet altered between preliminary comparison and protected recheck: no packet store.
class Mutated(RGB):
 def __init__(self):super().__init__(5);self.inject=False
 def read(self,a,n):
  if self.running and self.inject and a==LOG+8:
   self.inject=False;bad=bytearray(A);bad[75]^=1;self.put(0x900004,bad)
  return super().read(a,n)
c=Mutated();c.inject=True;c.tx(A);assert not c.stores() and c.read(LOG+64,4)==0;count+=1
# Publication order: immutable tuple fields written before active=1 release publication.
c=RGB(6);c.tx(A);addresses=[x[0] for x in c.writes]
for off in (28,32,36):assert addresses.index(LOG+off)<addresses.index(LOG+24)
count+=1
# A skipped candidate must not cause the analysis tool to report complete success.
from analyze import analyze
blob=bytearray((P/'synthetic-perfect-days.bin').read_bytes())
for off in (116,120):
 bad=bytearray(blob);bad[off:off+4]=(1).to_bytes(4,'big')
 try:analyze(bad)
 except (AssertionError,ValueError):pass
 else:raise AssertionError('lost coverage was not rejected')
 count+=1
r={'passed':count,'failed':0,'regression':'first A/B -> irrelevant contention -> second A/B succeeds in model','critical_loss':'selected SEND/REPLY/END contention inhibits further corrections','missed_unmodified_candidate':'sticky116, no rewrite, no success claim; subsequent candidate may retry naturally','assumptions':['T/SP/TLS identifies same synchronous invocation; unchanged native calling flow','aligned u32 loads/stores atomic; release publication plus control-dependent isync acquire','packet source remains readable per existing send path; protected recheck retained'],'scope':'bounded integer instruction execution; native interleavings/cache/MMU remain hardware-test requirements'}
(P/'contention-tests.json').write_text(json.dumps(r,indent=2)+'\n');print(json.dumps(r,indent=2))
