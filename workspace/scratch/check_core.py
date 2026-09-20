import re, sys
f = sys.argv[1] if len(sys.argv) > 1 else 'scratch/hollis-raze-core.ans'
data = open(f,'rb').read().decode('latin-1')
lines = data.split('\n')
def vis(s): return len(re.sub(r'\x1b\[[0-9;]*m','',s))
over = [(i,vis(l)) for i,l in enumerate(lines) if vis(l)>80]
print(f, 'rows:', len(lines), 'over80:', len(over), over[:3])
tail_ok = data.rstrip().endswith('\x1b[0m')
print('ends reset standalone:', tail_ok)
sgr = set(re.findall(r'\x1b\[([0-9;]*)m', data))
print('distinct SGR groups:', len(sgr))
