#!/usr/bin/env python3
from pathlib import Path
import struct,json,hashlib,re
P=Path(__file__).resolve().parent;R=P.parents[1]
# Reuse the established independent parser only, not its artifact-specific checks.
source=(P/'prx_parser.py').read_text()
ns={'__file__':str(P/'audit.py')};exec(source,ns)
b,ph,rel,info=ns['parse'](P/'disc_rgb_three.prx')
assert b==(P/'disc_rgb_three.roundtrip.elf').read_bytes()
assert info['module_name']=='disc_rgb_three'
assert len(info['imports'])==1
assert info['imports'][0]['library']=='sysPrxForUser'
assert info['imports'][0]['nids']==['0x24a1ea07']
assert info['imports'][0]['attributes']=='0x9'
symbols={name:int(addr,16) for addr,name in re.findall(r'([0-9a-f]+) <([A-Za-z_][A-Za-z_0-9]*)>:',(P/'disassembly.txt').read_text())}
assert info['exports'][0]['nids']==['0xbc9a0086','0xab779874','0xd7f43016']
assert info['elf_flags']=='0x1000000' and info['shoff']==info['shnum']==0
assert [x[1] for x in ph]==[0x400005,0x600006,0]
loads=[x for x in ph if x[0]==1]
assert loads[1][6]==63264 and loads[1][6]<=65536, 'RW memory budget exceeded'
trials=[]
for bases in [(0x1a70000,0x1a80000),(0x2400000,0x1100000)]:
 mem=[bytearray(b[x[2]:x[2]+x[5]])+bytearray(x[6]-x[5]) for x in loads]
 for at,pad,source,dest,typ,addend in rel:
  assert typ==1 and pad==0 and source<2 and dest<2 and at+4<=len(mem[dest]) and addend<=len(mem[source])
  struct.pack_into('>I',mem[dest],at,bases[source]+addend)
 def get(ptr,n):
  for base,m in zip(bases,mem):
   if base<=ptr and ptr+n<=base+len(m):return m[ptr-base:ptr-base+n]
  raise AssertionError(hex(ptr))
 toc,es,ee,ins,ine=struct.unpack_from('>5I',mem[0],32)
 assert toc==bases[1] and ine-ins==44
 nid,adr=struct.unpack_from('>II',get(es,28),20)
 assert get(nid,12)==bytes.fromhex('bc9a0086ab779874d7f43016')
 start,stop,module=struct.unpack('>III',get(adr,12));assert module==bases[0]
 funcs=[]
 for opd,expected in [(start,symbols['start_code']),(stop,symbols['stop_code'])]:
  entry,toc=struct.unpack('>II',get(opd,8));assert entry==bases[0]+expected and toc==bases[1]
  funcs.append({'entry':hex(entry),'toc':hex(toc)})
 assert get(bases[1],16)==b'DRSM30493C85v1!!'
 worker,slotptr,stop_ptr,nameptr=struct.unpack('>4I',get(bases[1]+528,16))
 assert stop_ptr==stop
 assert struct.unpack('>II',get(worker,8))==(bases[0]+symbols['worker_code'],bases[1])
 assert get(nameptr,15)==b'disc_rgb_three\0'
 assert struct.unpack('>5Q',get(bases[1]+544,40))==(40,2,0,1,0)
 library,nids,slots=struct.unpack_from('>III',get(ins,44),16)
 assert get(library,14)==b'sysPrxForUser\0'
 assert struct.unpack('>I',get(nids,4))[0]==0x24a1ea07
 assert slotptr==slots
 assert struct.unpack('>I',get(slots,4))[0]==bases[0]+symbols['thread_import_stub']
 # Every hook address is relocated RX; log pointer is relocated RW.
 for i,q in enumerate(json.loads((P/'sites.json').read_text())['sites']):
  site,original,adapter,branch,owned,rc=struct.unpack('>6I',get(bases[1]+2048+i*24,24))
  assert site==int(q['va'],16) and original==int(q['original'],16)
  assert adapter==bases[0]+symbols[q['symbol']] and branch==owned==rc==0
 logptr=struct.unpack('>I',get(bases[1]+616,4))[0]
 assert get(logptr,20)==bytes.fromhex('41564332')+bytes(16)
 literal=struct.unpack('>I',get(bases[0]+symbols['log_pointer'],4))[0]
 assert literal==logptr
 trials.append({'segment_bases':list(map(hex,bases)),'descriptors':funcs})

text=(P/'disassembly.txt').read_text();stores=[];indirect=[];sc=[]
for line in text.splitlines():
 m=re.match(r'\s*([0-9a-f]+):\s+(?:[0-9a-f]{2} ){3}[0-9a-f]{2}\s+([\w.]+)\s*(.*)',line)
 if not m:continue
 pc,op,arg=m.groups();addr=int(pc,16)
 if op.startswith('st'):
  if op=='stwcx.':
   assert arg in ('r5,0,r3','r9,0,r10'),line
   classification='Sony instruction CAS' if arg=='r5,0,r3' else 'private log lock CAS'
  else:
   assert op in ('stw','std','stdu','stb'),line
   base=int(re.search(r'\(r(\d+)\)',arg)[1]);assert base in (1,6,7,12,27,30,31),line
   classification={1:'thread stack',6:'record payload destination',7:'two exact-match RGB packet words',12:'record destination',27:'private capture header',30:'private site ownership table',31:'private control/capture header'}[base]
  stores.append({'pc':hex(addr),'op':op,'operands':arg,'destination':classification})
 if op=='bctrl':indirect.append(pc)
 if op=='sc':sc.append(pc)
assert [x['pc'] for x in stores if x['destination']=='two exact-match RGB packet words']==[hex(symbols['rgb_store_format']),hex(symbols['rgb_store_cs'])]
assert len(indirect)==1
assert sum(x['destination']=='Sony instruction CAS' for x in stores)==1
assert '0x6fdd08' not in (P/'program.S').read_text().lower()
assert len([x for x in stores if x['op']=='stwcx.'])==3
assert b[:6]==bytes.fromhex('7f454c460202')
# Absolute BA returns must not be transformed into relative branches by PRX tool.
for q in json.loads((P/'sites.json').read_text())['sites']:
 original=int(q['original'],16);ret=int(q['va'],16)+4
 expected=struct.pack('>II',original,0x48000002|(ret&0x03fffffc))
 assert b.count(expected)==1,(q,expected.hex())
assert json.loads((P/'installer-tests.json').read_text())['result']=='PASS'
assert json.loads((P/'reuse-tests.json').read_text())['failed']==0
assert json.loads((P/'contention-tests.json').read_text())['failed']==0
assert json.loads((P/'session-tests.json').read_text())['failed']==0
assert json.loads((P/'session-tests.json').read_text())['failed']==0
assert json.loads((P/'reuse-tests.json').read_text())['failed']==0
assert json.loads((P/'contention-tests.json').read_text())['failed']==0
assert json.loads((P/'session-tests.json').read_text())['failed']==0
assert json.loads((P/'session-tests.json').read_text())['failed']==0
report={'result':'PASS OFFLINE; not native validation','structure':info,'relocation_trials':trials,'stores':stores,'indirect_calls':indirect,'syscall_sites':sc,'syscalls':[1,8,41,141,351,461,482],'syscall8':'only firmware/Cobra queries and GET_PROC_MEM; no SET','Sony_write_scope':'five fixed instruction CAS; two packet words for each of three exact templates, any order, counter-exhaustion guarded repeat corrections; no state setters','hot_unload':'deliberately refused, module kept resident until full reboot','window_seconds':None,'buffer_bytes':61056,'records':190,'record_bytes':320,'RW_control_offset':0,'capture_pointer_in_control':616,'native_validation':False}
(P/'audit.json').write_text(json.dumps(report,indent=2)+'\n')
print('PASS: PRX structure, separated relocations/OPDs, single thread import, five BA replay returns, all stores classified, roundtrip (not an independent signature proof).')

assert loads[0][5]==loads[0][6]==8192 and loads[1][5]==63260 and loads[1][6]==63264
report['LOAD_footprint_change']='RX8192/RW63264 same as hardware-tested bd_rgb_two; offline structural comparison only'
report['adapters']='same frames; relevance prefilter before private lock, protected recheck; matched TX lock miss passes through with sticky116; selected callback lock loss sticky120/loss12; TX192/RX12; repeated corrections with30-transaction block reuse; unchanged packet store sites'
(P/'audit.json').write_text(json.dumps(report,indent=2)+'\n')

assert json.loads((P/'samsara-tests.json').read_text())['failed']==0
assert b.count((P/'start-576.bin').read_bytes()+(P/'second-480.bin').read_bytes()+(P/'samsara-480.bin').read_bytes())==1
assert b.count(bytes.fromhex('90670030'))==1 and b.count(bytes.fromhex('9067004c'))==1
report['template_count']=3
report['samsara_signaling_preserved']=True
report['native_validation']=False
(P/'audit.json').write_text(json.dumps(report,indent=2)+'\n')
