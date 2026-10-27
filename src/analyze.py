"""Strict offline validation; physical RGB still requires visual confirmation."""
from pathlib import Path
import json,sys
from decode_capture import decode
P=Path(__file__).resolve().parent
def analyze(b):
 d=decode(b);h=d['RGB']
 assert not any(d['contention'].values()),'contention prevented full test coverage'
 assert d['usable'] and not d['partial_events']
 assert h['inflight']==h['fault']==h['capacity_refusal']==0
 assert 1<=h['stage']<0xffffffff and h['stage']==d['retired_blocks']*30+h['count576']+h['count480']
 assert d['records']==6*(h['count576']+h['count480']) and len(d['transactions'])==h['count576']+h['count480']
 assert h['reply_mask']==7 and h['send_seen']==1
 counts={1:0,2:0};last={1:0,2:0};found=[]
 for t in d['transactions']:
  e=t['events'][0];kind=e['rewrite_stage'];assert kind in (1,2,3)
  group=1 if kind==1 else 2;counts[group]+=1;last[group]=e['sequence']
  assert e['captured_bytes']==e['declared_bytes']==116 and e['flags']==0
  expected=bytearray((P/({1:'start-576.bin',2:'second-480.bin',3:'samsara-480.bin'}[kind])).read_bytes());expected[48:52]=bytes(4);expected[76:80]=bytes(4)
  actual=b''.join(bytes.fromhex(x['raw']) for x in e['packets']);assert actual==expected
  assert t['event_order_valid'] and t['mapped_send_results']==['0x0'] and t['final_result']=='0x0'
  assert len(t['events'])==6 and len(t['command_responses'])==3
  for q in t['command_responses']:assert len(q['matching_replies'])==1 and q['matching_replies'][0]['status']==0
  found.append({'template':kind,'sequence':e['sequence'],'elapsed_seconds_coarse':e['elapsed_seconds_coarse']})
 assert counts=={1:h['count576'],2:h['count480']}
 assert last=={1:h['sequence576'],2:h['sequence480']}
 return {'all_corrections_and_responses':'PASS','counts_current_block':counts,'retired_blocks':d['retired_blocks'],'total_corrections':h['stage'],'transactions':found,'physical_color':'requires user confirmation','unmatched_commands':'not recorded or modified','rollback':'requires separate live instruction verification'}
if __name__=='__main__':print(json.dumps(analyze(Path(sys.argv[1]).read_bytes()),indent=2))
