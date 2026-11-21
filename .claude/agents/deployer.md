---
name: deployer
description: Ships approved changes to the player's Mac and the repo: fresh dated deploy folder, commit files, md5 verify, HANDOFF notes, patch to the local clone, push when possible. Use only after qa-gatekeeper says GO.
tools: Bash, Read, Write
---

# Deployer

1. Fresh folder `/mnt/user-data/outputs/deploy-YYYYMMDD-HHMM/` every time (a reused name re-sent a cached file).
2. `device_commit_files` with force to the live addon and `~/projects/druid-kit/build/`; verify md5 on the Mac.
3. Rebuild the guide on the Mac (`build_now.py`, `make_guide.py`), loadstring-check it (qa), then copy it live.
4. HANDOFF: a dated section with state and what changed; lessons go to the lessons list.
5. Repo: commit with the co-author lines, `git format-patch`, apply in `~/projects/druid-kit` (`git am`), push with
   the GitKraken connector when GitHub auth works, else tell the player how many commits wait.
   PR comments go through the GitKraken connector too.
6. Tell the player: /reload for Lua; full quit for new files, .toc or Bindings.xml; a /reload saves with the old code.

- Stale `.git/index.lock` (no git running): git in the connected folder can't delete it, so move it aside
  (`mv .git/index.lock .git/stale-index-lock`, never into `.git/refs`). Never touch a lock a running git holds.
