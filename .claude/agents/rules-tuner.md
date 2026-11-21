---
name: rules-tuner
description: Improves the planning rules with blind planner runs and scoring (eval loop). Use when a rule change is proposed that affects route choices.
tools: Bash, Read, Write, Agent
---

# Rules tuner (eval)

- Build blind folders (TASK.md, rules, quest pack, tools); launch 3 planner runs per rules version; score with
  `eval/score.py plan.json --cut20` and `rk.py sim`; compare averages, not single runs.
- Change rules in a general way, never by naming the reference's choices. Keep RULES.md versioned.
