import unittest

from inventor_core import (
    CatalogClient,
    PandaClient,
    PandaPublicationCoordinator,
    PublicationCoordinator,
)
from inventor_core.panda import DEFAULT_API
from inventor_core.publishing import DEFAULT_CATALOG_API
from inventor_workshop import Launchpad, Portal
from inventor_workshop.launch import DEFAULT_PORTAL_API


class LegacyCompatibilityTest(unittest.TestCase):
    def test_former_publishing_names_alias_workshop_api(self):
        self.assertIs(CatalogClient, Portal)
        self.assertIs(PublicationCoordinator, Launchpad)
        self.assertEqual(DEFAULT_CATALOG_API, DEFAULT_PORTAL_API)

    def test_legacy_panda_names_alias_workshop_api(self):
        self.assertIs(PandaClient, Portal)
        self.assertIs(PandaPublicationCoordinator, Launchpad)
        self.assertEqual(DEFAULT_API, DEFAULT_PORTAL_API)
        self.assertEqual(PandaClient("token").api_base, DEFAULT_PORTAL_API)


if __name__ == "__main__":
    unittest.main()
