import unittest

from workshop.errors import ContractError
from workshop.workflow.effort import (
    DEFAULT_WORKSHOP_EFFORT,
    DEEP_AUTO_COMPACT_TOKEN_LIMIT,
    DEEP_ECONOMICS_CAPABILITY_PATH,
    DEEP_ECONOMICS_V1_CAPABILITY_PATH,
    DEEP_ECONOMICS_V2_CAPABILITY_PATH,
    DEEP_ECONOMICS_V3_CAPABILITY_PATH,
    DEEP_ECONOMICS_V4_CAPABILITY_PATH,
    DEEP_ECONOMICS_V5_CAPABILITY_PATH,
    DEEP_ECONOMICS_V6_CAPABILITY_PATH,
    DEEP_ECONOMICS_V7_CAPABILITY_PATH,
    DEEP_ECONOMICS_V8_CAPABILITY_PATH,
    DEEP_INITIAL_MAKE_PROOF_TIMEOUT_SECONDS,
    DEEP_LEGACY_AUTO_COMPACT_TOKEN_LIMIT,
    DEEP_MAKE_AUTO_COMPACT_TOKEN_LIMIT,
    DEEP_NATIVE_TURN_LIMIT,
    DEEP_V1_AUTO_COMPACT_TOKEN_LIMIT,
    DEEP_V1_NATIVE_TURN_LIMIT,
    DEEP_V5_INITIAL_INVENT_TIMEOUT_SECONDS,
    DEEP_V5_INITIAL_MAKE_PROOF_TIMEOUT_SECONDS,
    DEEP_V5_INVENT_RECOVERY_TIMEOUT_SECONDS,
    DEEP_V8_INITIAL_MAKE_PROOF_TIMEOUT_SECONDS,
    SPARK_AUTO_COMPACT_TOKEN_LIMIT,
    SPARK_ECONOMICS_CAPABILITY_PATH,
    SPARK_ECONOMICS_V1_CAPABILITY_PATH,
    SPARK_ECONOMICS_V2_CAPABILITY_PATH,
    SPARK_NATIVE_TURN_TIMEOUT_SECONDS,
    WORKSHOP_EFFORTS,
    workshop_effort,
)


class WorkshopEffortTest(unittest.TestCase):
    def test_named_efforts_have_exact_passthrough_lifecycles(self):
        self.assertEqual(DEFAULT_WORKSHOP_EFFORT, "spark")
        self.assertEqual(
            SPARK_ECONOMICS_CAPABILITY_PATH,
            ".agents/skills/autonomous-workshop/references/spark-economics-v3.md",
        )
        self.assertEqual(
            SPARK_ECONOMICS_V2_CAPABILITY_PATH,
            ".agents/skills/autonomous-workshop/references/spark-economics-v2.md",
        )
        self.assertEqual(
            SPARK_ECONOMICS_V1_CAPABILITY_PATH,
            ".agents/skills/autonomous-workshop/references/spark-economics-v1.md",
        )
        self.assertEqual(SPARK_AUTO_COMPACT_TOKEN_LIMIT, 64_000)
        self.assertEqual(SPARK_NATIVE_TURN_TIMEOUT_SECONDS, 1_200)
        self.assertEqual(
            DEEP_ECONOMICS_CAPABILITY_PATH,
            ".agents/skills/autonomous-workshop/references/deep-economics-v9.md",
        )
        self.assertEqual(
            DEEP_ECONOMICS_V8_CAPABILITY_PATH,
            ".agents/skills/autonomous-workshop/references/deep-economics-v8.md",
        )
        self.assertEqual(
            DEEP_ECONOMICS_V7_CAPABILITY_PATH,
            ".agents/skills/autonomous-workshop/references/deep-economics-v7.md",
        )
        self.assertEqual(
            DEEP_ECONOMICS_V6_CAPABILITY_PATH,
            ".agents/skills/autonomous-workshop/references/deep-economics-v6.md",
        )
        self.assertEqual(
            DEEP_ECONOMICS_V5_CAPABILITY_PATH,
            ".agents/skills/autonomous-workshop/references/deep-economics-v5.md",
        )
        self.assertEqual(
            DEEP_ECONOMICS_V4_CAPABILITY_PATH,
            ".agents/skills/autonomous-workshop/references/deep-economics-v4.md",
        )
        self.assertEqual(
            DEEP_ECONOMICS_V3_CAPABILITY_PATH,
            ".agents/skills/autonomous-workshop/references/deep-economics-v3.md",
        )
        self.assertEqual(
            DEEP_ECONOMICS_V2_CAPABILITY_PATH,
            ".agents/skills/autonomous-workshop/references/deep-economics-v2.md",
        )
        self.assertEqual(
            DEEP_ECONOMICS_V1_CAPABILITY_PATH,
            ".agents/skills/autonomous-workshop/references/deep-economics-v1.md",
        )
        self.assertEqual(DEEP_AUTO_COMPACT_TOKEN_LIMIT, 256_000)
        self.assertEqual(DEEP_LEGACY_AUTO_COMPACT_TOKEN_LIMIT, 24_000)
        self.assertEqual(DEEP_MAKE_AUTO_COMPACT_TOKEN_LIMIT, 16_000)
        self.assertEqual(DEEP_INITIAL_MAKE_PROOF_TIMEOUT_SECONDS, 720)
        self.assertEqual(DEEP_V5_INITIAL_INVENT_TIMEOUT_SECONDS, 1_200)
        self.assertEqual(DEEP_V5_INVENT_RECOVERY_TIMEOUT_SECONDS, 600)
        self.assertEqual(DEEP_V5_INITIAL_MAKE_PROOF_TIMEOUT_SECONDS, 480)
        self.assertEqual(DEEP_V8_INITIAL_MAKE_PROOF_TIMEOUT_SECONDS, 960)
        self.assertEqual(DEEP_V1_AUTO_COMPACT_TOKEN_LIMIT, 32_000)
        self.assertEqual(DEEP_NATIVE_TURN_LIMIT, 8)
        self.assertEqual(DEEP_V1_NATIVE_TURN_LIMIT, 8)
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
