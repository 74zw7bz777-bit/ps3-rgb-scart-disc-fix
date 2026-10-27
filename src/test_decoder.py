import struct,json
from pathlib import Path
from decode_capture import decode
P=Path(__file__).resolve().parent
child=struct.pack('>HHI4H4B',0x205,16,0x10001,0x10,5,1,1,0,0,0,0)
tx=struct.pack('>HHI4H',0x205,12+len(child),0x4000001,0,0,1,0)+child
rx=struct.pack('>HHII',0x205,8,0x84000001,3)
def sample():
 b=bytearray(61056);struct.pack_into('>6I',b,0,0x41564332,0,1,0,4,0);struct.pack_into('>I',b,40,1)
 for i,k in enumerate((2,3,4,5)):
  r=128+i*320;p=tx if k==2 else rx if k==4 else b''
  struct.pack_into('>8I',b,r,1,k,i,len(p),{2:0x5dc300,3:0x5dc310,4:0x5dc404,5:0x5dc328}[k],0xd0008b20,0x10007060,0x10016110)
  struct.pack_into('>6Q',b,r+32,0,0,0,0,0,0);struct.pack_into('>I',b,r+80,len(p));struct.pack_into('>I',b,r+88,73);b[r+128:r+128+len(p)]=p
 return b
b=sample();d=decode(b);t=d['transactions'][0]
assert t['event_order_valid'] and t['command_responses'][0]['matching_replies'][0]['status']==3
assert t['mapped_send_results']==['0x0'] and t['final_result']=='0x0'
assert t['events'][0]['elapsed_seconds_coarse']==73
neg=0
for off,val in [(0,0),(4,1),(8,0),(16,191),(128,0),(132,1),(136,99),(140,193)]:
 b=sample();struct.pack_into('>I',b,off,val)
 try:decode(b)
 except ValueError:neg+=1
 else:raise AssertionError(off)
for off in [12,48,52]:
 b=sample();struct.pack_into('>I',b,off,1);assert not decode(b)['usable'];neg+=1
b=sample();struct.pack_into('>I',b,128+84,4);struct.pack_into('>I',b,128+80,2048);d=decode(b);assert not d['usable'] and not d['transactions'][0]['command_responses'];neg+=1
b=sample();struct.pack_into('>I',b,16,3);d=decode(b);assert not d['transactions'] and d['partial_events'];neg+=1
b=sample();struct.pack_into('>I',b,128+2*320+28,0x10016114);d=decode(b);assert not d['transactions'][0]['command_responses'][0]['matching_replies'];neg+=1
(P/'decoder-tests.json').write_text(json.dumps({'PASS':True,'negative_controls':neg,'nonzero_reply_not_masked_by_send_success':True,'TX_start_not_synthetic_BEGIN':True},indent=2)+'\n');print('PASS decoder',neg,'negative controls')
