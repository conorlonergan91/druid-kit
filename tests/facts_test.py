"""Forever facts registry: valid entries, and the stale / find / used-by queries forever-watch relies on."""

import datetime
import sys

from expect import check, done
from wowenv import ROOT

sys.path.insert(0, str(ROOT / "tools"))
import facts  # noqa: E402

data = facts.load()
ids = [f["id"] for f in data["facts"]]
check(len(ids) == len(set(ids)), "fact ids are unique", ids)
need = {"id", "topic", "statement", "sources", "verified", "confidence", "review_days", "used_by"}
bad = [f["id"] for f in data["facts"] if not need <= set(f) or f["confidence"] not in ("high", "medium", "low")]
check(not bad, "every fact has sources, a date, a confidence and its users", bad)
for f in data["facts"]:
    datetime.date.fromisoformat(f["verified"])
far = facts.stale(data, today=datetime.date(2027, 6, 1))
check(len(far) == len(ids), "everything is stale a long time from now", len(far))
soon = facts.stale(data, today=datetime.date(2026, 12, 3), level=20)
check(any(f["id"] == "gear-weights" for f in soon), "low-confidence facts come up for review quickly", soon)
check(
    not any(f["id"] == "riding" for f in facts.stale(data, today=datetime.date(2026, 11, 20), level=20)),
    "facts outside the level window or not due are left alone",
    "",
)
check([f["id"] for f in facts.find(data, ["nighthaven"])] == ["flight-nighthaven"], "find by words", "")
check(any(f["id"] == "gear-weights" for f in facts.used_by(data, "WEIGHTS")), "used-by finds what a file relies on", "")
done("facts_test")
