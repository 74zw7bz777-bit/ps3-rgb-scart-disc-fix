"""Bounded interleaving model. Native atomicity/cache semantics are assumptions,
not proven by this model; the late-entry counterexample is explicitly tested."""
import itertools,json
from pathlib import Path
P=Path(__file__).resolve().parent
sequences=[]
for order in itertools.permutations(['fetch','enter','leave','restore','stop','unload']):
 if not order.index('fetch')<order.index('enter')<order.index('leave'):continue
 if not order.index('restore')<order.index('stop')<order.index('unload'):continue
 sequences.append(order)
def run(seq,pinned):
 branch=True;resident=True;target=None;module_state=5
 for action in seq:
  if action=='fetch':target='adapter' if branch else 'original'
  elif action=='restore':branch=False
  elif action=='stop':module_state=5 if pinned else 7
  elif action=='unload':
   if (1<<module_state)&0x8c:resident=False
  elif action=='enter' and target=='adapter' and not resident:return False
 return True
assert all(run(s,True) for s in sequences)
negative=[s for s in sequences if not run(s,False)]
assert negative
r={'result':'PASS bounded model','interleavings':len(sequences),'pinned_safe_in_model':True,'hot_unload_negative_controls':negative,'assumptions':['single-word publication atomic','fetched old-or-new branch, no torn word','native stop phase2 refusal semantics as checked against local kernel','no forced unmap or reboot during execution']}
(P/'lifetime-tests.json').write_text(json.dumps(r,indent=2)+'\n');print('PASS',len(sequences),'lifetime interleavings; ordinary hot-unload counterexample retained')
