"""Unit tests for DIContainer."""

import unittest
from src.core.di_container import DIContainer
from src.core.config import ConfigurationService
from src.core.database import DatabaseService
from src.infrastructure.database.repositories import (
    AnalysisRepository, AlertRepository, ReportRepository, SettingsRepository
)


class TestDIContainer(unittest.TestCase):

    def test_di_resolution(self):
        DIContainer.reset()
        container = DIContainer()

        cfg = container.resolve(ConfigurationService)
        self.assertIsInstance(cfg, ConfigurationService)

        db = container.resolve(DatabaseService)
        self.assertIsInstance(db, DatabaseService)

        analysis_repo = container.resolve(AnalysisRepository)
        self.assertIsInstance(analysis_repo, AnalysisRepository)

        alert_repo = container.resolve(AlertRepository)
        self.assertIsInstance(alert_repo, AlertRepository)

        report_repo = container.resolve(ReportRepository)
        self.assertIsInstance(report_repo, ReportRepository)

        settings_repo = container.resolve(SettingsRepository)
        self.assertIsInstance(settings_repo, SettingsRepository)


if __name__ == "__main__":
    unittest.main()
