"""Integration tests for DatabaseService and Repositories."""

import unittest
import os
import tempfile
from src.core.database import DatabaseService
from src.infrastructure.database.repositories import (
    AnalysisRepository, AlertRepository, ReportRepository, SettingsRepository, seed_database_if_empty
)


class TestDatabaseAndRepositories(unittest.TestCase):

    def test_sqlite_tables_and_seeding(self):
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp:
            db_path = tmp.name

        try:
            db_service = DatabaseService(db_path=db_path)
            seed_database_if_empty(db_service)

            analysis_repo = AnalysisRepository(db_service)
            records = analysis_repo.get_all()
            self.assertEqual(len(records), 10)

            alert_repo = AlertRepository(db_service)
            alerts = alert_repo.get_all()
            self.assertGreater(len(alerts), 0)

            report_repo = ReportRepository(db_service)
            reports = report_repo.get_all()
            self.assertEqual(len(reports), 10)

            settings_repo = SettingsRepository(db_service)
            theme = settings_repo.get("theme.mode")
            self.assertEqual(theme, "dark")
        finally:
            if os.path.exists(db_path):
                os.remove(db_path)


if __name__ == "__main__":
    unittest.main()
