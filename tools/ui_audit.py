"""UI audit: inventory of the addon's look and keys, with the places that break docs/UI_STYLE.md.

Usage: python3 tools/ui_audit.py [--json]

Reports per file: font sizes, button sizes and labels, backdrops and strata; the key bindings (Bindings.xml and the
default keys the addon sets); and findings:
  - text smaller than the minimum size (the player's eyesight: UI_STYLE "Text")
  - buttons that aren't one of the standard sizes
  - panels drawn with their own backdrop instead of DruidKit_Style
  - bindings missing from the key map in UI_STYLE.md
"""

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ADDON = ROOT / "DruidKit"
STYLE_DOC = ROOT / "docs" / "UI_STYLE.md"
MIN_FONT = 13
BUTTON_SIZES = {(64, 22), (96, 22), (64, 20)}  # UI_STYLE "Buttons": standard, wide, compact row

FONT = re.compile(r"SetFont\([^,]+,\s*(\d+)")
FS_HELPER = re.compile(r"\b(?:fs|txt|text)\(\s*(?:[A-Za-z_][\w.]*\s*,\s*)?(\d+)")
SIZE = re.compile(r"(\w+):SetSize\((\d+),\s*(\d+)\)")
BTN = re.compile(r'(?:btn|button)\(\s*(?:[\w.]+,\s*)?"([^"]+)"(?:,\s*(\d+))?')
BACKDROP = re.compile(r"SetBackdropColor\(")
STRATA = re.compile(r'SetFrameStrata\("(\w+)"\)')
BIND_XML = re.compile(r'<Binding name="(\w+)"')
BIND_SET = re.compile(r'SetBinding,\s*"([\w-]+)",\s*"(\w+)"')


def audit():
    files, findings = {}, []
    for p in sorted(ADDON.glob("*.lua")):
        if p.name == "DruidKit_Guide.lua":
            continue
        src = p.read_text(encoding="utf-8")
        fonts = sorted({int(x) for x in FONT.findall(src)} | {int(x) for x in FS_HELPER.findall(src)})
        sizes = [(n, int(w), int(h)) for n, w, h in SIZE.findall(src)]
        buttons = [lbl for lbl, _ in BTN.findall(src)]
        files[p.name] = {
            "fonts": fonts,
            "button_sizes": sorted(
                {(w, h) for n, w, h in sizes if n == "b" or "btn" in n.lower() or "button" in n.lower()}
                | {(int(w), 22) for _, w in BTN.findall(src) if w}
            ),
            "buttons": buttons,
            "own_backdrops": len(BACKDROP.findall(src)),
            "strata": sorted(set(STRATA.findall(src))),
        }
        small = [f for f in fonts if f < MIN_FONT]
        if small:
            findings.append(f"{p.name}: text sizes {small} are below {MIN_FONT}")
        odd = [s for s in files[p.name]["button_sizes"] if s not in BUTTON_SIZES]
        if odd:
            findings.append(f"{p.name}: non-standard button sizes {odd}")
        if files[p.name]["own_backdrops"] and p.name != "DruidKit_Style.lua":
            findings.append(
                f"{p.name}: {files[p.name]['own_backdrops']} panel(s) with their own backdrop, not DruidKit_Style"
            )
    xml = (ADDON / "Bindings.xml").read_text(encoding="utf-8")
    bindings = BIND_XML.findall(xml)
    defaults = {}
    for p in ADDON.glob("*.lua"):
        for key, action in BIND_SET.findall(p.read_text(encoding="utf-8")):
            defaults[action] = key
    doc = STYLE_DOC.read_text(encoding="utf-8") if STYLE_DOC.exists() else ""
    missing = [b for b in bindings if b not in doc]
    if missing:
        findings.append(f"UI_STYLE.md key map is missing bindings: {missing}")
    return {"files": files, "bindings": bindings, "default_keys": defaults, "findings": findings}


if __name__ == "__main__":
    r = audit()
    if "--json" in sys.argv:
        print(json.dumps(r, indent=1, default=list))
    else:
        for name, f in r["files"].items():
            print(
                f"{name}: fonts {f['fonts']} · buttons {f['button_sizes']} · own backdrops {f['own_backdrops']} "
                f"· strata {f['strata']}"
            )
        print("default keys:", ", ".join(f"{k} -> {a}" for a, k in r["default_keys"].items()))
        print(f"\n{len(r['findings'])} finding(s):")
        for x in r["findings"]:
            print("  - " + x)
