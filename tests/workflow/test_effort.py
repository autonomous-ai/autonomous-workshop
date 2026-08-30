import unittest

from workshop.errors import ContractError
from workshop.workflow.effort import (
    DEFAULT_WORKSHOP_EFFORT,
    SPARK_AUTO_COMPACT_TOKEN_LIMIT,
    SPARK_ECONOMICS_CAPABILITY_PATH,
    SPARK_ECONOMICS_V1_CAPABILITY_PATH,
    WORKSHOP_EFFORTS,
    workshop_effort,
)


class WorkshopEffortTest(unittest.TestCase):
    def test_named_efforts_have_exact_passthrough_lifecycles(self):
        self.assertEqual(DEFAULT_WORKSHOP_EFFORT, "spark")
        self.assertEqual(
            SPARK_ECONOMICS_CAPABILITY_PATH,
            ".agents/skills/autonomous-workshop/references/spark-economics-v2.md",
        )
        self.assertEqual(
            SPARK_ECONOMICS_V1_CAPABILITY_PATH,
            ".agents/skills/autonomous-workshop/references/spark-economics-v1.md",
        )
        self.assertEqual(SPARK_AUTO_COMPACT_TOKEN_LIMIT, 64_000)
        self.assertEqual(
            {name: effort.lifecycle for name, effort in WORKSHOP_EFFORTS.items()},
            {
                "spark": ("wish", "make", "release"),
                "forge": ("wish", "invent", "make", "release"),
                "quest": (
                    "wish",
                    "invent",
                    "make",
                    "playtest",
                    "release",
                ),
            },
        )
        self.assertEqual(workshop_effort("spark").next_stage("wish"), "make")
        self.assertEqual(workshop_effort("forge").next_stage("make"), "release")
        self.assertEqual(workshop_effort("quest").next_stage("make"), "playtest")

    def test_unknown_effort_fails_closed(self):
        for value in (None, "", "minimal", "SPARK", 1):
            with self.subTest(value=value), self.assertRaises(ContractError):
                workshop_effort(value)

    def test_effort_registry_is_immutable(self):
        with self.assertRaises(TypeError):
            WORKSHOP_EFFORTS["spark"] = workshop_effort("quest")  # type: ignore[index]


if __name__ == "__main__":
    unittest.main()
