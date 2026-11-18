"""UI consistency: the audit runs, the key map in docs/UI_STYLE.md covers every binding, and no change adds a UI
finding beyond the known backlog (docs/ui_baseline.json)."""

import json
import sys

from expect import check, done
from wowenv import ROOT

sys.path.insert(0, str(ROOT / "tools"))
import ui_audit  # noqa: E402

r = ui_audit.audit()
check(len(r["bindings"]) >= 13, "bindings read from Bindings.xml", r["bindings"])
check(not any("key map is missing" in f for f in r["findings"]), "UI_STYLE key map lists every binding", r["findings"])
base = set(json.loads((ROOT / "docs" / "ui_baseline.json").read_text(encoding="utf-8"))["findings"])
new = [f for f in r["findings"] if f not in base]
check(not new, "no new UI findings (fix them, or agree them in docs/ui_baseline.json)", new)
done("ui_test")
