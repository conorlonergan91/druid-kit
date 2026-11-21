"""tests/wowenv.py reads the repo's DruidKit files by default and the live folder under DK_LIVE."""

import os
import tempfile
from pathlib import Path

from expect import check, done
from wowenv import ROOT, addon_dir, source

os.environ.pop("DK_LIVE", None)
check(addon_dir() == ROOT / "DruidKit", "default: the repo's DruidKit folder", addon_dir())
check(source("DruidKit/DruidKit.lua") == (ROOT / "DruidKit/DruidKit.lua").read_text(), "default source: repo copy")

live = Path(tempfile.mkdtemp())
(live / "DruidKit.lua").write_text("-- live copy", encoding="utf-8")
os.environ["DK_LIVE"] = str(live)
check(source("DruidKit/DruidKit.lua") == "-- live copy", "DK_LIVE: DruidKit/ files come from the live folder")
cp = "ClaudeProgress/ClaudeProgress.lua"
check(source(cp) == (ROOT / cp).read_text(), "DK_LIVE: other folders still come from the repo")
done("py_wowenv_test")
