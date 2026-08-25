"""The creative seams this inventor chooses to own.

Return exact Workshop records when the implementation is ready. Until then,
waiting is honest: never invent CAD, print, or play evidence.
"""

from inventor_workshop import Made, MakeContext, Need, WaitingFor


def make(context: MakeContext) -> Made:
    """Replace this wait with this inventor's artifact-producing Make."""

    # The trusted checkout/tier supplies this per-Wish allowance. Custom Make
    # receives it on every round; never infer or increase it from Wish text.
    playtest_rounds = context.playtest_rounds
    del playtest_rounds
    raise WaitingFor(
        Need(
            "make",
            "inventor-make",
            "This inventor's custom Make has not been connected yet.",
            "Implement make(context) and return a Made record bound to exact artifact bytes.",
        )
    )


from inventor_workshop import PlaytestContext, Playtested


def playtest(context: PlaytestContext) -> Playtested:
    """Replace this wait with this inventor's evidence-producing Playtest."""

    # This is the same trusted per-Wish allowance received by custom Make.
    playtest_rounds = context.playtest_rounds
    del playtest_rounds
    raise WaitingFor(
        Need(
            "playtest",
            "inventor-playtest",
            "This inventor's custom Playtest has not been connected yet.",
            "Implement playtest(context) and return Playtested evidence for the exact Make.",
        )
    )
