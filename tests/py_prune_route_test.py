"""tools/prune_route.py drops travel only behind the player: up to the last hand-in of the done run at the start."""

import sys

from expect import check, done
from wowenv import ROOT

sys.path.insert(0, str(ROOT / "tools"))
import prune_route  # noqa: E402
import route_check  # noqa: E402

ROUTE = {
    "id": "r1",
    "sections": [
        {
            "title": "A",
            "steps": [
                {"do": "goto", "text": "Walk to Bob"},
                {"do": "turnin", "q": 1, "name": "Done"},
                {"do": "goto", "text": "Walk to the farm"},
                {"do": "accept", "q": 2, "name": "Not yet"},
                {"do": "fly", "to": "Ironforge"},
                {"do": "turnin", "q": 3, "name": "Skipped"},
                {"do": "goto", "text": "Walk on"},
                {"do": "turnin", "q": 4, "name": "Handed in early"},
            ],
        }
    ],
}
STATE = {"log": {}, "done": [1, 4], "route": {"skipped": ["3"]}, "travel": {"flights": []}}
out, n = prune_route.prune(ROUTE, STATE)
left = [st.get("text") or st.get("to") or st.get("name") for st in out["sections"][0]["steps"]]
check(left == ["Walk to the farm", "Not yet", "Ironforge", "Walk on"], "unreached travel stays", left)
check(n == 4, "only the walk to Bob and three hand-ins go", n)

check(route_check.town_of("Harbor") is None, "a bare word doesn't match a town by substring", "")
check(route_check.town_of("Menethil Harbor") == "Menethil", "a town named in the text matches", "")
s = {"travel": {"flights": ["Thelsamar, Loch Modan"], "home": "Lakeshire"}, "log": {}, "done": []}
check(prune_route.done_by_state({"do": "fp", "to": "Thelsamar"}, s), "a known flight path is done", "")
check(not prune_route.done_by_state({"do": "home", "to": "Shire"}, s), "home 'Shire' is not Lakeshire", "")
done("py_prune_route_test")
