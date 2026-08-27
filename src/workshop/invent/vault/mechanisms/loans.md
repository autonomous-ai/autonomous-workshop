---
type: mechanism
name: "Loans"
created: 2026-08-21
source: agent
status: seeded
bgg_id: null
---

# Loans

## Definition
A mechanism where players can borrow resources (usually money) from a bank or other players, typically at an interest cost, to accelerate their position in the game. The tension arises from the risk-reward calculation: borrowing accelerates short-term gains but creates a future liability that must be repaid, potentially leaving a player vulnerable if cash flow dries up or if opponents exploit the debt strategically.

## Relations
- risks:: [[anti-patterns/analysis-paralysis]], [[anti-patterns/kingmaking]], [[anti-patterns/missing-info]], [[anti-patterns/runaway-leader]]
- variant-of:: [[mechanisms/market]]
- requires:: [[mechanisms/income]]

## Notes
Loan mechanics work better when issued algorithmically (bank rules) than player-to-player, since peer lending creates strategic default incentives and lender reluctance.
Interest rates and repayment schedules are critical; poorly tuned mechanics can create death spirals or make borrowing strictly dominant/dominated.
sources: https://dr.wictz.com/2014/10/market-mechanic-lecture-credit-loans.html https://board-game-rules.com/game-mechanics/loans/ https://www.boardgamehalv.com/best-loan-board-games/ https://en.wikipedia.org/wiki/Pay_Day_(board_game)
