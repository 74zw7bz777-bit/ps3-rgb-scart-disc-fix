#!/usr/bin/env python3
"""Native assembler/PRX pipeline; no network, no target execution."""
from pathlib import Path
import struct,subprocess,json,hashlib
import os
P=Path(__file__).resolve().parent
AS=Path(os.environ['PPU_AS']);LD=Path(os.environ['PPU_LD']);GEN=Path(os.environ['PRX_GEN']);SCE=Path(os.environ['SCETOOL']);OBJDUMP=Path(os.environ['PPU_OBJDUMP'])
SIGNING=Path(os.environ['SCETOOL_WORKDIR']) # user-provided data; never bundled
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def run(args,cwd=None):
 r=subprocess.run(list(map(str,args)),cwd=cwd,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True)
 with (P/'build.log').open('a') as f:f.write(' '.join(Path(str(x)).name if '/' in str(x) else str(x) for x in args)+'\n'+r.stdout)
 assert r.returncode==0,r.stdout
 return r.stdout
(P/'build.log').write_text('Local assembly build; no C compiler required.\n')
# Fixed passthrough assembly; no capture generator.
anchors=json.loads((P/'anchors.json').read_text())
(P/'program.S').write_text(f'.set ANCHOR_COUNT,{len(anchors)}\n'+(P/'installer.S').read_text()+(P/'data.inc').read_text()+(P/'capture.S').read_text())
run([AS,'-mcell','-o',P/'probe.o',P/'program.S']);run([AS,'-mcell','-o',P/'crt.o',P/'crt.S'])
run([LD,'--no-opd-optimize','--no-toc-optimize','--emit-relocs','-z','max-page-size=16','-T',P/'prx.ld','-Map',P/'link.map','-o',P/'linked.elf',P/'crt.o',P/'probe.o'])
run([GEN,'build',P/'linked.elf','-o',P/'unstripped.prx','--name','disc_rgb_three','--version','1.0'])
a=(P/'unstripped.prx').read_bytes();po=struct.unpack_from('>Q',a,32)[0];pn=struct.unpack_from('>H',a,56)[0]
ph=[struct.unpack_from('>IIQQQQQQ',a,po+i*56) for i in range(pn)]
assert [x[1] for x in ph]==[0x400005,0x600006,0]
b=bytearray(len(a));b[:64]=a[:64];b[po:po+pn*56]=a[po:po+pn*56]
for x in ph:b[x[2]:x[2]+x[5]]=a[x[2]:x[2]+x[5]]
struct.pack_into('>Q',b,40,0);struct.pack_into('>HHH',b,58,0,0,0)
prx=P/'disc_rgb_three.prx';prx.write_bytes(b)
run([SCE,'-0','SELF','-1','TRUE','-s','FALSE','-2','0A','-3','1070000052000001','-4','01000002','-5','APP','-6','0003004000000000','-A','0001000000000000','--self-ctrl-flags','40'+'00'*31,'-e',prx,P/'disc_rgb_three.sprx'],SIGNING)
run([SCE,'-d',P/'disc_rgb_three.sprx',P/'disc_rgb_three.roundtrip.elf'],SIGNING)
assert (P/'disc_rgb_three.roundtrip.elf').read_bytes()==bytes(b)
(P/'disassembly.txt').write_text(run([OBJDUMP,'-dr',P/'linked.elf']))
manifest={'roundtrip_identical':True,'tools':{t.name:sha(t) for t in [AS,LD,GEN,SCE]},'sources':{n:sha(P/n) for n in ['installer.S','capture.S','data.inc','crt.S','prx.ld','build.py','anchors.json']},'artifacts':{n:{'sha256':sha(P/n),'bytes':(P/n).stat().st_size} for n in ['disc_rgb_three.sprx','disc_rgb_three.prx','disc_rgb_three.roundtrip.elf']},'hardware_execution':False,'compiler':'handwritten PPU assembly, native arm64 GNU assembler; no new C compiler or ABI conversion'}
(P/'build-manifest.json').write_text(json.dumps(manifest,indent=2)+'\n');print(json.dumps(manifest['artifacts'],indent=2))
