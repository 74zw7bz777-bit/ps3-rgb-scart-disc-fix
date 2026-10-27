"""Bounded rolling-log and lifetime regression of built PPU code, offline only."""
from pathlib import Path
import json
from analyze import analyze
P=Path(__file__).resolve().parent
ns={'__file__':str(P/'test_reuse.py')};exec((P/'test_reuse.py').read_text().split('count=0')[0],ns)
RGB=ns['RGB'];LOG=ns['LOG'];A=ns['A'];B=ns['B'];fixed=ns['fixed'];cases=0
for seed in range(3):
 c=RGB(seed)
 for i in range(305):
  b=A if i%3 else B;c.tx(b);assert c.packet()==fixed(b);c.complete()
  assert c.read(LOG+64,4)==i+1 and c.read(LOG+16,4)==6*((i%30)+1)
  assert c.read(LOG+124,4)==i//30 and c.read(LOG+88,4)==0
  cases+=1
 c.put(LOG+4,bytes(4));c.put(LOG+8,(1).to_bytes(4,'big'));blob=c.bytes(LOG,61056);r=analyze(blob)
 assert r['total_corrections']==305 and r['retired_blocks']==10 and len(r['transactions'])==5
 if seed==0:(P/'synthetic-session.bin').write_bytes(blob)
 cases+=1
# No reuse of a failed/incomplete/ambiguous block, no diagnostic erasure.
for fault in ('reply','missing','loss','inflight','badmask','badsend','misaligned'):
 c=RGB(4)
 for i in range(30):c.tx(A);c.complete(reply=1 if i==29 and fault=='reply' else 0,order=(0x84000001,0x80030001) if i==29 and fault=='missing' else (0x84000001,0x80030001,0x80030003))
 if fault in ('loss','inflight','badmask','badsend','misaligned'):
  off,val={'loss':(12,1),'inflight':(68,1),'badmask':(104,3),'badsend':(108,0),'misaligned':(16,181)}[fault];c.put(LOG+off,val.to_bytes(4,'big'))
 before=c.bytes(LOG+128,57600);n=len(c.stores());c.tx(B)
 assert len(c.stores())==n and c.read(LOG+124,4)==0 and c.bytes(LOG+128,57600)==before,fault;cases+=1
# Total count never wraps; exhaustion requests automatic rollback.
c=RGB(5);c.put(LOG+64,(0xfffffffd).to_bytes(4,'big'));c.tx(A);c.complete();assert c.read(LOG+64,4)==0xfffffffe
n=len(c.stores());c.tx(B);assert c.packet()==B and len(c.stores())==n and c.read(LOG+20,4)==1;cases+=1
# Loss flag remains sticky through attempted recycle; epoch corruption rejected by analyzer.
b=(P/'synthetic-session.bin').read_bytes()
for off in (12,64,80,84,88,116,120,124):
 x=bytearray(b);x[off]^=1
 try:analyze(x)
 except (AssertionError,ValueError):pass
 else:raise AssertionError(off)
 cases+=1
r={'passed':cases,'failed':0,'long_sequence':'305 corrections per seed,10 log-block reuses,3 seeds','retention':'current block only; retired responses are not retained','failure_behavior':'no recycle of failed/incomplete block; faults sticky; uint32 exhaustion requests stop','native_execution':False}
(P/'session-tests.json').write_text(json.dumps(r,indent=2)+'\n');print(json.dumps(r,indent=2))
