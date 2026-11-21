"""Solo steps: hostile monsters 3+ levels above the player within 3 map units of the step spot (RULES v16).

Usage: python3 tools/dangercheck.py ROUTE.py PLAYER_LEVEL
"""
import sys
from pathlib import Path
PLANNER = Path(__file__).resolve().parent.parent / "planner"
sys.path.insert(0, str(PLANNER))
import json, importlib.util as u, math, sys
db=json.load(open(PLANNER / 'db.json'))
import rk
ZID={v: k for k, v in rk.ZONE_IDS.items()}
s=u.spec_from_file_location('r',sys.argv[1]);m=u.module_from_spec(s);s.loader.exec_module(m)
lvl=float(sys.argv[2]) if len(sys.argv)>2 else 22
mobs=[]
for v in db['npcs'].values():
    if v.get('friendlyToFaction') or v.get('npcFlags') or not v.get('minLevel') or v['minLevel']>70 or v.get('rank'): continue
    sp=v.get('spawns')
    if isinstance(sp,dict):
        for z,pts in sp.items():
            for p in pts: mobs.append((int(z),p[0],p[1],v['minLevel'],v.get('name','?')))
n=0
for sec in m.ROUTE['sections']:
    for st in sec['steps']:
        n+=1
        if st.get('party') or 'group' in sec['title'].lower() and st['do'] in ('complete',): continue
        if st['do']=='level': lvl=max(lvl,st['level']-1)
        g=st.get('goto')
        if not g or g[0] not in ZID or g[0] in ('Stormwind City','Ironforge','Darnassus','Orgrimmar','Thunder Bluff','Undercity'): continue
        bad={}
        for z,x,y,L,name in mobs:
            if z==ZID[g[0]] and lvl+3<=L<lvl+15 and math.hypot(x-g[1],y-g[2])<3: bad[name]=L   # 15+ above: town NPCs and guards
        if bad: print(n, st.get('name') or st.get('text'), g, '| lvl', lvl, '|', sorted(bad.items(), key=lambda t:-t[1])[:5])
