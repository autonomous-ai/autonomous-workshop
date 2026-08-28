Native resume prompts now make host-gate rejection semantics explicit: a
rejection-bound subject is a new Goal attempt, and Codex must repair and change
the rejected bytes instead of repeatedly finalizing an unchanged proposal.
Once a replacement Make proposal reaches the CAD gate, its newer CAD rejection
supersedes resolved proposal-level feedback in subsequent stage packets.
