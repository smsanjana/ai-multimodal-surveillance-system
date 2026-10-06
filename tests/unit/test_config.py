"""Unit tests for ConfigurationService."""

import unittest
from src.core.config import ConfigurationService


class TestConfigurationService(unittest.TestCase):

    def test_config_loading(self):
        config = ConfigurationService()
        self.assertEqual(config.get("app.name"), "AI Surveillance Command Center")
        self.assertEqual(config.get("ai.confidence_threshold"), 0.25)
        self.assertEqual(config.get("non_existent_key", "default_val"), "default_val")

    def test_config_all(self):
        config = ConfigurationService()
        all_cfg = config.get_all()
        self.assertIn("app", all_cfg)
        self.assertIn("ai", all_cfg)
        self.assertIn("theme", all_cfg)


if __name__ == "__main__":
    unittest.main()
