import unittest

import workshop as workshop


class ProviderPublicApiTest(unittest.TestCase):
    def test_workshop_provider_seams_are_public(self):
        expected = {
            "ClassicEvidenceProvider",
            "PinnedCheckersRulesProvider",
            "PreparedLaneRelease",
            "ProviderIdentity",
            "PublicScienceSource",
            "ScienceAccuracyCase",
            "ScienceComprehensionTrace",
            "ScienceEvidenceProvider",
            "ScienceSimplificationCheck",
            "ScienceVerification",
            "WorkshopLanePlaytestProviders",
            "WorkshopMovingMachineVerifier",
            "MOVING_MACHINE_BINDING_KIND",
            "MOVING_MACHINE_BINDING_VERSION",
            "MovingMachineVerification",
            "WorldConsentRecord",
            "WorldEvidenceProvider",
            "WorldLikenessCase",
            "WorldReferenceMaterial",
            "WorldVerification",
            "workshop_pinned_wear_model",
        }

        self.assertTrue(expected <= set(workshop.__all__))
        self.assertTrue(all(hasattr(workshop, name) for name in expected))
        self.assertEqual(
            workshop.workshop_pinned_wear_model()["kind"],
            "workshop-pinned-digital-clearance-budget",
        )


if __name__ == "__main__":
    unittest.main()
