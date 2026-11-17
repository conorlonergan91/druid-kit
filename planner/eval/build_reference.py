"""Reference route: RestedXP's free WoW Forever route (CC BY-NC-SA 4.0) as a Night Elf Druid, levels 1-20.

Follows the guides' #next chain from "1-6 Shadowglen", keeps only steps whose class/race conditions match,
and records ordered events. Output: reference.json (kept OUT of the generator's reach).
"""

import json
import os
import re
import sys
from collections import Counter
from pathlib import Path

# Usage: python3 build_reference.py GUIDE.lua [GUIDE.lua ...]  (free RestedXP Forever guides, CC BY-NC-SA:
# used only to score plans locally; the reference is never committed or copied into a route)
FILES = sys.argv[1:]
ME = {"Alliance", "NightElf", "Druid"}
STOP_AT_LEVEL = 20


def cond_ok(expr):
    """RXP conditions: groups separated by '/', tokens inside a group are ANDed, '!' negates."""
    expr = expr.strip()
    if not expr:
        return True
    for group in expr.split("/"):
        ok = True
        for tok in group.split():
            neg = tok.startswith("!")
            t = tok[1:] if neg else tok
            has = t in ME
            if has == neg:
                ok = False
                break
        if ok:
            return True
    return False


def split_cond(line):
    if "<<" in line:
        a, b = line.split("<<", 1)
        return a, b
    return line, ""


guides = {}
for f in FILES:
    src = Path(f).read_text(encoding="utf-8")
    for body in re.findall(r"RXPGuides\.RegisterGuide\(\[\[(.*?)\]\]", src, re.S):
        lines = body.split("\n")
        head = {"cond": "", "name": None, "next": []}
        steps, cur = [], None
        for raw in lines:
            line = raw.split("--", 1)[0].rstrip() if not raw.strip().startswith(">>") else raw.rstrip()
            s = line.strip()
            if not s:
                continue
            if cur is None and s.startswith("<<"):
                head["cond"] = s[2:]
            elif s.startswith("#name"):
                head["name"] = s[5:].strip()
            elif s.startswith("#next"):
                txt, c = split_cond(s[5:])
                head["next"].append((txt.strip(), c))
            elif s.startswith("step"):
                _, c = split_cond(s)
                cur = {"cond": c, "flags": [], "cmds": []}
                steps.append(cur)
            elif cur is not None:
                if s.startswith("#"):
                    cur["flags"].append(s.split()[0])
                elif s.startswith("."):
                    cmd, c = split_cond(s)
                    cur["cmds"].append((cmd.strip(), c))
        guides[head["name"]] = {"head": head, "steps": steps}

events, chain = [], []
name = "1-6 Shadowglen"
while name and name in guides:
    g = guides[name]
    chain.append(name)
    lo = int(re.match(r"(\d+)", name).group(1))
    if lo >= STOP_AT_LEVEL:
        chain.pop()
        break
    for st in g["steps"]:
        if not cond_ok(st["cond"]):
            continue
        optional = "#optional" in st["flags"]
        for cmd, c in st["cmds"]:
            if not cond_ok(c):
                continue
            m = re.match(r"\.(accept|turnin|complete|abandon)\s+(\d+)", cmd)
            if m:
                events.append({"guide": name, "kind": m.group(1), "q": int(m.group(2)), "optional": optional})
            m = re.match(r"\.home\s*(.*?)\s*>>\s*(.*)", cmd)
            if m:
                events.append({"guide": name, "kind": "home", "text": m.group(2)[:80], "optional": optional})
            if cmd.startswith(".hs"):
                events.append({"guide": name, "kind": "hearth", "text": cmd[:80], "optional": optional})
            if re.match(r"\.(trainer|train)\b", cmd):
                events.append({"guide": name, "kind": "train", "optional": optional})
            m = re.match(r"\.xp\s+(\d+(?:\.\d+)?)(?:\s|$|>>)", cmd)
            if m and ">>" in cmd:
                events.append({"guide": name, "kind": "grind", "to": float(m.group(1)), "optional": optional})
    nxt = None
    for txt, c in g["head"]["next"]:
        if cond_ok(c):
            nxt = txt.split(";")[0].split("\\")[-1].strip()
            break
    name = nxt

Path(os.path.dirname(os.path.abspath(__file__)), "reference.json").write_text(
    json.dumps({"chain": chain, "events": events}, indent=0), encoding="utf-8"
)
print(chain)
print(Counter(e["kind"] for e in events))
print([e["text"] for e in events if e["kind"] == "home"])
