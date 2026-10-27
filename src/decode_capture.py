#!/usr/bin/env python3
"""Offline decoder. Input is an exact read-only dump of the private capture buffer.
No console access. Never infer success from missing or truncated events.
"""
import struct,json,sys
from pathlib import Path
SIZE=61056
u32=lambda b,o:struct.unpack_from('>I',b,o)[0]
def packets(data,reply=False,depth=0):
 if depth>1:raise ValueError('nested packet depth')
 out=[];at=0
 while at<len(data):
  if len(data)-at<8:raise ValueError('short header')
  ver,length,cid=struct.unpack_from('>HHI',data,at);n=length+4
  if ver!=0x205 or n<8 or at+n>len(data):raise ValueError('invalid packet boundary/version')
  p=data[at:at+n];r={'offset':at,'command':hex(cid),'bytes':n,'raw':p.hex()}
  if reply:
   if n<12 or not cid&0x80000000:raise ValueError('invalid reply')
   r['status']=u32(p,8)
  elif cid==0x10001:
   if n<20:raise ValueError('short AV_VIDEO_CS')
   port,vid,csout,csin=struct.unpack_from('>4H',p,8)
   r.update(port=port,video_id=vid,cs_out=csout,cs_in=csin,bitlen_out_raw=p[17],color={0:'RGB',1:'YUV444',2:'YUV422'}.get(csout,'unknown'))
  elif cid==0x4000001:
   if n<16:raise ValueError('short batch')
   counts=struct.unpack_from('>4H',p,8);r['counts']=counts
   r['children']=packets(p[16:],False,depth+1)
   if sum(counts)!=len(r['children']):raise ValueError('batch count mismatch')
  out.append(r);at+=n
 return out

def decode(b):
 if len(b)!=SIZE:raise ValueError('wrong dump length')
 magic,enabled,lock,loss,count=struct.unpack_from('>5I',b)
 if magic!=0x41564332 or enabled!=0 or lock!=1 or count>190:raise ValueError('not a stopped valid capture header')
 result={'loss_flag':loss,'capacity_cutoff':u32(b,20),'records':count,'transactions':[],'partial_events':[],'usable':loss==0 and count>0}
 active={}
 for seq in range(count):
  r=b[128+seq*320:128+(seq+1)*320]
  committed,kind,num,n,pc,sp,tls,t=struct.unpack_from('>8I',r)
  if committed!=1 or num!=seq or kind not in range(2,6) or n>192 or pc!={1:0x5dc1ec,2:0x5dc300,3:0x5dc310,4:0x5dc404,5:0x5dc328}.get(kind):raise ValueError('invalid record')
  regs=struct.unpack_from('>6Q',r,32);flags=u32(r,84)
  event={'sequence':seq,'kind':kind,'pc':hex(pc),'flags':flags,'r3':hex(regs[0]),'r31':hex(regs[5])}
  event['declared_bytes']=u32(r,80);event['captured_bytes']=n;event['elapsed_seconds_coarse']=u32(r,88);event['rewrite_stage']=u32(r,92)
  if kind==2 and n and not flags:
   try:event['packets']=packets(r[128:128+n],False)
   except ValueError as e:event['decode_error']=str(e);result['usable']=False
  elif kind==2 and flags==4:
   event['truncated']=True
   if n>=8:event['first_command_header_only']=hex(u32(r,132))
  if kind==4 and n==12 and not flags:
   ver,length,cid,status=struct.unpack_from('>HHII',r,128)
   if ver==0x205 and length+4==u32(r,80) and cid&0x80000000:
    event['packets']=[{'command':hex(cid),'status':status,'reply_header_only':True,'declared_bytes':length+4}]
   else:event['decode_error']='invalid reply header';result['usable']=False
  if flags:result['usable']=False
  key=(t,sp,tls)
  if kind==2:
   if key in active:result['partial_events'].append(active.pop(key))
   active[key]={'key':list(map(hex,key)),'events':[event]}
  elif key not in active:result['partial_events'].append(event)
  else:
   active[key]['events'].append(event)
   if kind==5:
    tr=active.pop(key);tr['final_result']=hex(regs[5]&0xffffffff)
    kinds=[x['kind'] for x in tr['events']]
    # Valid early exit can have only BEGIN/END; no missing reply is fabricated.
    tr['transport_observed']=2 in kinds and 3 in kinds
    tr['mapped_send_results']=[e['r3'] for e in tr['events'] if e['kind']==3]
    tr['event_order_valid']=kinds[0]==2 and kinds[-1]==5 and kinds.count(2)==1 and kinds.count(3)<=1 and (2 in kinds)==(3 in kinds) and (2 not in kinds or kinds.index(2)<kinds.index(3)) and (4 not in kinds or (3 in kinds and kinds.index(3)<kinds.index(4)))
    if not tr['event_order_valid']:result['usable']=False
    # Correlate only inside this invocation, using exact command ID, never stale scratch bytes.
    tx=[p for e in tr['events'] if e['kind']==2 for p in e.get('packets',[])]
    rx=[p for e in tr['events'] if e['kind']==4 for p in e.get('packets',[])]
    tr['command_responses']=[{'command':p['command'],'matching_replies':[q for q in rx if int(q['command'],16)==(int(p['command'],16)|0x80000000)]} for p in tx]
    result['transactions'].append(tr)
 result['partial_events'].extend(active.values())
 result['filter']={name:u32(b,off) for name,off in {'active':24,'selected_TX':40,'skipped_audio_empty_TX':44,'collision':48,'malformed_seen':52,'elapsed_seconds_coarse':56}.items()}
 if result['filter']['collision'] or result['filter']['malformed_seen']:result['usable']=False
 result['RGB']={name:u32(b,off) for name,off in {'stage':64,'inflight':68,'sequence576':72,'sequence480':76,'count576':80,'count480':84,'fault':88,'capacity_refusal':100,'reply_mask':104,'send_seen':108}.items()}
 result['retired_blocks']=u32(b,124)
 result['contention']={'missed_unmodified_candidate':u32(b,116),'lost_selected_callback':u32(b,120)}
 result['note']='Header RGB.stage is total correction count; sequence576/480 are last sequences; rewrite_stage is template ID (1 or 2), not order. Partial edge invocations excluded; capacity cutoff preserves earlier complete records, unlike a lost event. One-second worker tick at each recorded event; no wall-clock timestamp. Only selected TX-started transactions; BEGIN intentionally omitted. TX truncated prefixes are never interpreted as complete packets. Reply captures only header/status, not remaining data. Mapped SEND status is not raw syscall171 byte count. Batch reply does not prove physical RGB.'
 return result
if __name__=='__main__':
 c=Path(sys.argv[2]).read_bytes()
 if len(c)<2168 or c[:16]!=b'DRSM30493C85v1!!':raise ValueError('control magic/size')
 if any(u32(c,o)!=v for o,v in [(16,2),(20,6),(24,0),(588,1),(620,1)]):raise ValueError('control not successfully finished/frozen')
 if any(u32(c,2048+i*24+16)!=0 for i in range(5)):raise ValueError('owned patch remains')
 print(json.dumps(decode(Path(sys.argv[1]).read_bytes()),indent=2))
