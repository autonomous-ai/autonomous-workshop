---
type: rule-pattern
name: "Goal Reachability Validation"
created: 2026-08-27
source: agent
status: seeded
---

# Goal Reachability Validation

## Definition
Model the legal game states and verify that every permitted setup has at least one path to a winning state. For games where play can irreversibly destroy that path, either prohibit those transitions, provide recovery actions, or immediately resolve the position as a loss; exhaustive validation can be costly when the state space is large.

## Relations

## Notes
- Constructing setups backward from a valid goal can guarantee at least one solution when actions are reversible.
- Automated state-space searches should cover setup variants and irreversible player choices.
