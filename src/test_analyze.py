from pathlib import Path
import json
from analyze import analyze
P=Path(__file__).resolve().parent;b=(P/'synthetic-perfect-days.bin').read_bytes();r=analyze(b);assert r['all_corrections_and_responses']=='PASS'
positions=[12,64,68,72,76,80,84,88,100,104,108,128+128+48,128+6*320+128+76]
for pos in positions:
 x=bytearray(b);x[pos]^=1
 try:analyze(x)
 except (AssertionError,ValueError):pass
 else:raise AssertionError(pos)
(P/'analysis-tests.json').write_text(json.dumps({'PASS':True,'negative_controls':len(positions),'positive':'synthetic built-instruction replay, not native execution'},indent=2)+'\n');print('Analyzer PASS',len(positions))
