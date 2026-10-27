from pathlib import Path
import json,struct
P=Path(__file__).resolve().parent
s=(P/'ppu_model.py').read_text()
s=s.replace("'bgt','blt']","'bgt','blt','ble']").replace("'blt':bool(cr&8)}","'blt':bool(cr&8),'ble':not cr&4}")
s=s.replace("elif m in ['cmpwi','cmpdi','cmplwi']:","""elif m in ['cmpw','cmplw']:
    a=rv(args[0])&0xffffffff;b=rv(args[1])&0xffffffff
    if m=='cmpw':a=signed(a,32);b=signed(b,32)
    v=8 if a<b else 4 if a>b else 2
    self.s['cr']=(self.s['cr']&0xfffffff)|((v|((self.s['xer']>>31)&1))<<28)
   elif m=='and':dst(rv(args[1])&rv(args[2]))
   elif m=='or':dst(rv(args[1])|rv(args[2]))
   elif m=='subf':dst(rv(args[2])-rv(args[1]))
   elif m in ['cmpwi','cmpdi','cmplwi']:""")
ns={'__file__':str(P/'test_filter.py')};exec(s,ns)
CPU=ns['CPU'];LOG=ns['LOG'];syms=ns['syms'];MASK=ns['MASK'];signed=ns['signed'];sites=json.loads((P/'sites.json').read_text())['sites']
class Checked(CPU):
 def __init__(self,seed):super().__init__(seed);self.running=False;self.bound=2048;self.put(LOG+88,bytes(4))
 def read(self,a,n):
  if syms['template576']<=a and a+n<=syms['template576']+348:return CPU.read(self,a,n)
  if self.running:
   assert (0x7ffe00<=a and a+n<=0x800000) or (LOG<=a and a+n<=LOG+61056) or (a==syms['log_pointer'] and n==4) or (a==0x900804 and n==4) or (0x900004<=a and a+n<=0x900004+self.bound) or (0x910000<=a and a+n<=0x91000c),('outside read bound',hex(a),n,self.bound)
  return super().read(a,n)
 def event(self,kind):
  q=sites[kind-1];before=self.r[:];special=self.s.copy();self.running=True
  try:self.run(syms[q['symbol']],int(q['va'],16)+4)
  finally:self.running=False
  want=before[:]
  if kind==1:want[22]=before[3]
  if kind==2:want[4]=self.read(0x900804,4)
  if kind==4:want[4]=before[28]
  if kind==5:want[3]=signed(before[31],32)&MASK
  assert self.r==want and self.s==special,('register mismatch',kind)
 def tx(self,b,declared=None):
  self.bound=min(len(b),2048);self.put(0x900004,b);self.put(0x900804,(len(b) if declared is None else declared).to_bytes(4,'big'));self.event(2)
 def bytes(self,a,n):return bytes(self.mem[a+i] for i in range(n))

