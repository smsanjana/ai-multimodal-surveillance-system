"""SQLite Database Connection & Initialization Module."""

import sqlite3
from pathlib import Path
from typing import Optional
from src.core.logger import setup_logger

logger = setup_logger()


class DatabaseService:
    """Manages SQLite connection lifecycle and schema initialization."""

    def __init__(self, db_path: Optional[str] = None):
        if db_path is None:
            db_path = str(Path(__file__).parent.parent.parent / "data" / "surveillance.db")
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.initialize_database()

    def get_connection(self) -> sqlite3.Connection:
        """Returns a new SQLite connection with dict-like row formatting."""
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        return conn

    def initialize_database(self) -> None:
        """Creates all 7 baseline database tables if they do not exist."""
        logger.info("Initializing database schema at: %s", self.db_path)
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # 1. analyses table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS analyses (
                    id TEXT PRIMARY KEY,
                    timestamp TEXT NOT NULL,
                    source_type TEXT NOT NULL,
                    platform TEXT NOT NULL,
                    media_type TEXT NOT NULL,
                    scenario_name TEXT,
                    threat_score REAL NOT NULL,
                    threat_level TEXT NOT NULL,
                    confidence_avg REAL NOT NULL,
                    processing_time_ms REAL NOT NULL,
                    status TEXT NOT NULL,
                    artifact_path TEXT
                )
            """)

            # 2. detections table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS detections (
                    id TEXT PRIMARY KEY,
                    analysis_id TEXT NOT NULL,
                    class_name TEXT NOT NULL,
                    confidence REAL NOT NULL,
                    bbox_json TEXT NOT NULL,
                    frame_index INTEGER,
                    FOREIGN KEY(analysis_id) REFERENCES analyses(id) ON DELETE CASCADE
                )
            """)

            # 3. threat_assessments table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS threat_assessments (
                    id TEXT PRIMARY KEY,
                    analysis_id TEXT NOT NULL,
                    score REAL NOT NULL,
                    level TEXT NOT NULL,
                    xai_reason TEXT NOT NULL,
                    recommended_sop TEXT NOT NULL,
                    FOREIGN KEY(analysis_id) REFERENCES analyses(id) ON DELETE CASCADE
                )
            """)

            # 4. alerts table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS alerts (
                    id TEXT PRIMARY KEY,
                    analysis_id TEXT NOT NULL,
                    severity TEXT NOT NULL,
                    reason TEXT NOT NULL,
                    status TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    FOREIGN KEY(analysis_id) REFERENCES analyses(id) ON DELETE CASCADE
                )
            """)

            # 5. reports table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS reports (
                    id TEXT PRIMARY KEY,
                    analysis_id TEXT NOT NULL,
                    file_path TEXT NOT NULL,
                    report_type TEXT NOT NULL,
                    generated_at TEXT NOT NULL,
                    FOREIGN KEY(analysis_id) REFERENCES analyses(id) ON DELETE CASCADE
                )
            """)

            # 6. restricted_zones table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS restricted_zones (
                    id TEXT PRIMARY KEY,
                    zone_name TEXT NOT NULL,
                    platform TEXT NOT NULL,
                    polygon_json TEXT NOT NULL,
                    is_active INTEGER NOT NULL DEFAULT 1
                )
            """)

            # 7. settings table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS settings (
                    key TEXT PRIMARY KEY,
                    value TEXT NOT NULL,
                    category TEXT NOT NULL
                )
            """)

            # 8. analyst_reviews table (Feature 005)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS analyst_reviews (
                    id TEXT PRIMARY KEY,
                    analysis_id TEXT NOT NULL UNIQUE,
                    review_status TEXT NOT NULL CHECK (review_status IN ('PENDING_REVIEW', 'ACKNOWLEDGED', 'FALSE_POSITIVE', 'ESCALATED')),
                    analyst_id TEXT NOT NULL DEFAULT 'OPERATOR_01',
                    notes TEXT,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    FOREIGN KEY(analysis_id) REFERENCES analyses(id) ON DELETE CASCADE
                )
            """)

            # 9. analyst_review_history table (Feature 005 transition audit log)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS analyst_review_history (
                    history_id TEXT PRIMARY KEY,
                    review_id TEXT NOT NULL,
                    analysis_id TEXT NOT NULL,
                    from_status TEXT NOT NULL,
                    to_status TEXT NOT NULL,
                    analyst_id TEXT NOT NULL,
                    notes TEXT,
                    timestamp TEXT NOT NULL,
                    FOREIGN KEY(review_id) REFERENCES analyst_reviews(id) ON DELETE CASCADE,
                    FOREIGN KEY(analysis_id) REFERENCES analyses(id) ON DELETE CASCADE
                )
            """)

            conn.commit()
            logger.info("Database schema initialized successfully.")
