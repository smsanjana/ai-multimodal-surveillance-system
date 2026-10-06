"""Integration tests for application startup and foundation initialization."""

import unittest
from src.core.di_container import DIContainer
from src.core.config import ConfigurationService
from src.core.database import DatabaseService
from src.infrastructure.database.repositories import AnalysisRepository


class TestFoundationStartup(unittest.TestCase):

    def test_full_startup_initialization(self):
        DIContainer.reset()
        container = DIContainer()

        config = container.resolve(ConfigurationService)
        self.assertEqual(config.get("theme.mode"), "dark")

        db = container.resolve(DatabaseService)
        self.assertTrue(db.db_path.exists())

        analysis_repo = container.resolve(AnalysisRepository)
        records = analysis_repo.get_all()
        self.assertGreaterEqual(len(records), 10)


if __name__ == "__main__":
    unittest.main()
