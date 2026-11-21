"""ClaudeProgress: an empty realm name at login must not start a second save key ("Cu-")."""

import sys

from claude_progress_test import runtime

L = runtime(False)
L.execute('run("BANKFRAME_OPENED")')  # realm reads "R5": remembered
L.execute('function GetRealmName() return "" end GetNormalizedRealmName=nil')
L.execute('ClaudeProgressDB.bank["Cu-R5"]=nil run("BANKFRAME_OPENED")')
ok = L.eval('ClaudeProgressDB.bank["Cu-R5"] ~= nil') and L.eval('ClaudeProgressDB.bank["Cu-"] == nil')
L2 = runtime(False)
L2.execute('function GetRealmName() return "" end ClaudeProgressDB={_realm="R5"} run("BANKFRAME_OPENED")')
ok = ok and L2.eval('ClaudeProgressDB.bank["Cu-R5"] ~= nil')
print("ok" if ok else "FAIL")
sys.exit(0 if ok else 1)
