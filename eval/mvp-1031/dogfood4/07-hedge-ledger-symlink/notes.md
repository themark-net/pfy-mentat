# 07 hedge-ledger-symlink

Human: reject.

Why: `origin/bot/mvp-selfhost2-1031` commit `3eeab42` already changes `pfylib/hedge.py` to replace a ledger symlink instead of writing through it. This lane's ownership check printed that commit and the launch script did not abort. The cloud run then passed on a throwaway clone. The product diff is one file and the gate went from red to green, and it is still not landed here. A second copy would collide with that lane.

Cloud commit: d96b8112f1e3c002d7c46b0664dff31c50b263be (stays on the throwaway branch)
Landed: none
Wall seconds: 92
Attempts: 1
Review: accept (runner). Human: reject.
Exit: 0
Failure class: cross-lane
FINDING-D4-01: hedge ledger symlink follow is already committed on `origin/bot/mvp-selfhost2-1031` as `3eeab42`. Do not take it in this lane.

Fail: not landed. The red gate was dropped before this receipt was pushed.
Recover: leave the fix on the selfhost2 branch. This branch does not edit `pfylib/hedge.py`.
