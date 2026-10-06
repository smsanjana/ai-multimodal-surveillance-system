"""SQLite Database Repositories & Automatic Startup Seeder."""

from datetime import datetime, timedelta
from typing import Dict, List, Optional
import uuid

from src.core.database import DatabaseService
from src.core.logger import setup_logger
from src.domain.entities import (
    AnalysisRecord, AlertRecord, ReportRecord, SystemSettings, DetectionRecord,
    TrackRecord, TrajectoryPoint, AnalystReviewRecord, AnalystReviewHistoryRecord
)
from src.domain.interfaces import (
    IAnalysisRepository, IAlertRepository, IReportRepository, ISettingsRepository,
    IAnalystReviewRepository
)
import os
import json
from dataclasses import asdict

logger = setup_logger()


class AnalysisRepository(IAnalysisRepository):
    """SQLite implementation of Analysis repository."""

    def __init__(self, db_service: DatabaseService):
        self.db_service = db_service

    def get_all(self, platform: Optional[str] = None, threat_level: Optional[str] = None) -> List[AnalysisRecord]:
        query = "SELECT * FROM analyses WHERE 1=1"
        params = []
        if platform:
            query += " AND platform = ?"
            params.append(platform)
        if threat_level:
            query += " AND threat_level = ?"
            params.append(threat_level)
        query += " ORDER BY timestamp DESC"

        records = []
        with self.db_service.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)
            for row in cursor.fetchall():
                records.append(AnalysisRecord(
                    id=row["id"],
                    timestamp=row["timestamp"],
                    source_type=row["source_type"],
                    platform=row["platform"],
                    media_type=row["media_type"],
                    scenario_name=row["scenario_name"],
                    threat_score=row["threat_score"],
                    threat_level=row["threat_level"],
                    confidence_avg=row["confidence_avg"],
                    processing_time_ms=row["processing_time_ms"],
                    status=row["status"],
                    artifact_path=row["artifact_path"]
                ))
        return records

    def get_by_id(self, analysis_id: str) -> Optional[AnalysisRecord]:
        with self.db_service.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM analyses WHERE id = ?", (analysis_id,))
            row = cursor.fetchone()
            if row:
                return AnalysisRecord(
                    id=row["id"],
                    timestamp=row["timestamp"],
                    source_type=row["source_type"],
                    platform=row["platform"],
                    media_type=row["media_type"],
                    scenario_name=row["scenario_name"],
                    threat_score=row["threat_score"],
                    threat_level=row["threat_level"],
                    confidence_avg=row["confidence_avg"],
                    processing_time_ms=row["processing_time_ms"],
                    status=row["status"],
                    artifact_path=row["artifact_path"]
                )
        return None

    def save(self, record: AnalysisRecord) -> AnalysisRecord:
        with self.db_service.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT OR REPLACE INTO analyses 
                (id, timestamp, source_type, platform, media_type, scenario_name, threat_score, threat_level, confidence_avg, processing_time_ms, status, artifact_path)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                record.id, record.timestamp, record.source_type, record.platform,
                record.media_type, record.scenario_name, record.threat_score,
                record.threat_level, record.confidence_avg, record.processing_time_ms,
                record.status, record.artifact_path
            ))
            conn.commit()
        return record

    def save_analysis_with_detections(
        self, record: AnalysisRecord, detections: List[DetectionRecord], threat_assessment: Optional[Dict] = None
    ) -> AnalysisRecord:
        with self.db_service.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT OR REPLACE INTO analyses 
                (id, timestamp, source_type, platform, media_type, scenario_name, threat_score, threat_level, confidence_avg, processing_time_ms, status, artifact_path)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                record.id, record.timestamp, record.source_type, record.platform,
                record.media_type, record.scenario_name, record.threat_score,
                record.threat_level, record.confidence_avg, record.processing_time_ms,
                record.status, record.artifact_path
            ))

            for det in detections:
                cursor.execute("""
                    INSERT OR REPLACE INTO detections
                    (id, analysis_id, class_name, confidence, bbox_json, frame_index)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (
                    det.id, record.id, det.class_name, det.confidence, det.bbox_json, det.frame_index
                ))

            conn.commit()
        return record

    def save_video_analysis_with_tracks(
        self,
        record: AnalysisRecord,
        detections: List[DetectionRecord],
        tracks: List[TrackRecord],
        threat_assessment: Optional[Dict] = None
    ) -> AnalysisRecord:
        """Saves video analysis header in analyses, representative detections in detections, and full 13-field tracks in artifact JSON file."""
        artifacts_dir = "data/artifacts"
        os.makedirs(artifacts_dir, exist_ok=True)
        artifact_file = os.path.join(artifacts_dir, f"{record.id}_tracks.json")

        track_dicts = []
        for t in tracks:
            td = {
                "track_id": t.track_id,
                "class_id": t.class_id,
                "class_name": t.class_name,
                "first_frame": t.first_frame,
                "last_frame": t.last_frame,
                "first_timestamp": t.first_timestamp,
                "last_timestamp": t.last_timestamp,
                "detection_count": t.detection_count,
                "avg_confidence": t.avg_confidence,
                "movement_state": t.movement_state,
                "pixel_displacement": t.pixel_displacement,
                "trajectory_direction": t.trajectory_direction,
                "trajectory_points": [asdict(p) for p in t.trajectory_points]
            }
            track_dicts.append(td)

        with open(artifact_file, "w", encoding="utf-8") as f:
            json.dump({
                "analysis_id": record.id,
                "tracks": track_dicts
            }, f, indent=2)

        record.artifact_path = artifact_file
        record.media_type = "VIDEO"

        return self.save_analysis_with_detections(record, detections, threat_assessment)

    def get_tracks_by_artifact_path(self, artifact_path: str) -> List[TrackRecord]:
        """Reads serialized 13-field TrackRecord items from artifact JSON file."""
        if not artifact_path or not os.path.exists(artifact_path):
            return []
        try:
            with open(artifact_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            tracks_raw = data.get("tracks", [])
            result = []
            for tr in tracks_raw:
                points = [TrajectoryPoint(**p) for p in tr.get("trajectory_points", [])]
                result.append(TrackRecord(
                    track_id=tr["track_id"],
                    class_id=tr["class_id"],
                    class_name=tr["class_name"],
                    first_frame=tr["first_frame"],
                    last_frame=tr["last_frame"],
                    first_timestamp=tr["first_timestamp"],
                    last_timestamp=tr["last_timestamp"],
                    detection_count=tr["detection_count"],
                    avg_confidence=tr["avg_confidence"],
                    movement_state=tr["movement_state"],
                    pixel_displacement=tr["pixel_displacement"],
                    trajectory_direction=tr["trajectory_direction"],
                    trajectory_points=points
                ))
            return result
        except Exception as e:
            logger.warning("Failed to load tracks from artifact JSON '%s': %s", artifact_path, e)
            return []

    def get_detections_by_analysis_id(self, analysis_id: str) -> List[DetectionRecord]:
        results = []
        with self.db_service.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM detections WHERE analysis_id = ?", (analysis_id,))
            for row in cursor.fetchall():
                results.append(DetectionRecord(
                    id=row["id"],
                    analysis_id=row["analysis_id"],
                    class_name=row["class_name"],
                    confidence=row["confidence"],
                    bbox_json=row["bbox_json"],
                    frame_index=row["frame_index"]
                ))
        return results


class AnalystReviewRepository(IAnalystReviewRepository):
    """SQLite implementation of AnalystReview repository."""

    def __init__(self, db_service: DatabaseService):
        self.db_service = db_service

    def save_review(
        self, review: AnalystReviewRecord, history_entry: AnalystReviewHistoryRecord
    ) -> AnalystReviewRecord:
        """Persists or updates an analyst review record and appends a transition history row in SQLite."""
        with self.db_service.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT OR REPLACE INTO analyst_reviews (id, analysis_id, review_status, analyst_id, notes, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (review.id, review.analysis_id, review.review_status, review.analyst_id, review.notes, review.created_at, review.updated_at))

            cursor.execute("""
                INSERT INTO analyst_review_history (history_id, review_id, analysis_id, from_status, to_status, analyst_id, notes, timestamp)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (history_entry.history_id, history_entry.review_id, history_entry.analysis_id, history_entry.from_status, history_entry.to_status, history_entry.analyst_id, history_entry.notes, history_entry.timestamp))
            conn.commit()
        return review

    def get_review_by_analysis_id(self, analysis_id: str) -> Optional[AnalystReviewRecord]:
        """Retrieves analyst review record for analysis_id, returning None if unreviewed."""
        with self.db_service.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM analyst_reviews WHERE analysis_id = ?", (analysis_id,))
            row = cursor.fetchone()
            if not row:
                return None
            return AnalystReviewRecord(
                id=row["id"],
                analysis_id=row["analysis_id"],
                review_status=row["review_status"],
                analyst_id=row["analyst_id"],
                notes=row["notes"],
                created_at=row["created_at"],
                updated_at=row["updated_at"]
            )

    def get_review_history(self, review_id: str) -> List[AnalystReviewHistoryRecord]:
        """Retrieves full transition history for a review ID."""
        history = []
        with self.db_service.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM analyst_review_history WHERE review_id = ? ORDER BY timestamp ASC", (review_id,))
            for row in cursor.fetchall():
                history.append(AnalystReviewHistoryRecord(
                    history_id=row["history_id"],
                    review_id=row["review_id"],
                    analysis_id=row["analysis_id"],
                    from_status=row["from_status"],
                    to_status=row["to_status"],
                    analyst_id=row["analyst_id"],
                    notes=row["notes"],
                    timestamp=row["timestamp"]
                ))
        return history

    def list_reviews_by_status(self, review_status: str) -> List[AnalystReviewRecord]:
        """Lists analyst review records matching specified status filter."""
        reviews = []
        with self.db_service.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM analyst_reviews WHERE review_status = ? ORDER BY updated_at DESC", (review_status,))
            for row in cursor.fetchall():
                reviews.append(AnalystReviewRecord(
                    id=row["id"],
                    analysis_id=row["analysis_id"],
                    review_status=row["review_status"],
                    analyst_id=row["analyst_id"],
                    notes=row["notes"],
                    created_at=row["created_at"],
                    updated_at=row["updated_at"]
                ))
        return reviews




class AlertRepository(IAlertRepository):
    """SQLite implementation of Alert repository."""

    def __init__(self, db_service: DatabaseService):
        self.db_service = db_service

    def get_all(self, status: Optional[str] = None) -> List[AlertRecord]:
        query = "SELECT * FROM alerts WHERE 1=1"
        params = []
        if status:
            query += " AND status = ?"
            params.append(status)
        query += " ORDER BY created_at DESC"

        alerts = []
        with self.db_service.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)
            for row in cursor.fetchall():
                alerts.append(AlertRecord(
                    id=row["id"],
                    analysis_id=row["analysis_id"],
                    severity=row["severity"],
                    reason=row["reason"],
                    status=row["status"],
                    created_at=row["created_at"]
                ))
        return alerts

    def save(self, alert: AlertRecord) -> AlertRecord:
        with self.db_service.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT OR REPLACE INTO alerts (id, analysis_id, severity, reason, status, created_at)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (alert.id, alert.analysis_id, alert.severity, alert.reason, alert.status, alert.created_at))
            conn.commit()
        return alert


class ReportRepository(IReportRepository):
    """SQLite implementation of Report repository."""

    def __init__(self, db_service: DatabaseService):
        self.db_service = db_service

    def get_all(self) -> List[ReportRecord]:
        reports = []
        with self.db_service.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM reports ORDER BY generated_at DESC")
            for row in cursor.fetchall():
                reports.append(ReportRecord(
                    id=row["id"],
                    analysis_id=row["analysis_id"],
                    file_path=row["file_path"],
                    report_type=row["report_type"],
                    generated_at=row["generated_at"]
                ))
        return reports

    def save(self, report: ReportRecord) -> ReportRecord:
        with self.db_service.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT OR REPLACE INTO reports (id, analysis_id, file_path, report_type, generated_at)
                VALUES (?, ?, ?, ?, ?)
            """, (report.id, report.analysis_id, report.file_path, report.report_type, report.generated_at))
            conn.commit()
        return report


class SettingsRepository(ISettingsRepository):
    """SQLite implementation of Settings repository."""

    def __init__(self, db_service: DatabaseService):
        self.db_service = db_service

    def get_all(self) -> List[SystemSettings]:
        settings = []
        with self.db_service.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM settings")
            for row in cursor.fetchall():
                settings.append(SystemSettings(
                    key=row["key"],
                    value=row["value"],
                    category=row["category"]
                ))
        return settings

    def get(self, key: str, default: Optional[str] = None) -> Optional[str]:
        with self.db_service.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT value FROM settings WHERE key = ?", (key,))
            row = cursor.fetchone()
            if row:
                return row["value"]
        return default

    def set(self, key: str, value: str, category: str = "SYSTEM") -> None:
        with self.db_service.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT OR REPLACE INTO settings (key, value, category)
                VALUES (?, ?, ?)
            """, (key, value, category))
            conn.commit()


def seed_database_if_empty(db_service: DatabaseService) -> None:
    """Seeds baseline realistic mock records if database has no analysis history."""
    analysis_repo = AnalysisRepository(db_service)
    alert_repo = AlertRepository(db_service)
    report_repo = ReportRepository(db_service)
    settings_repo = SettingsRepository(db_service)

    existing_analyses = analysis_repo.get_all()
    if existing_analyses:
        return  # Already seeded

    logger.info("Database is empty. Executing initial baseline startup seeding...")
    
    now = datetime.utcnow()
    mock_scenarios = [
        ("drone_img_01", "DEMO", "DRONE", "IMAGE", "Highway Perimeter Security Patrol", 15.0, "LOW", 0.92, 110.0, "data/demo/drone/images/highway.jpg"),
        ("drone_vid_01", "DEMO", "DRONE", "VIDEO", "Restricted Area Convoy Movement", 82.0, "CRITICAL", 0.88, 340.0, "data/demo/drone/videos/convoy.mp4"),
        ("cctv_img_01", "DEMO", "CCTV", "IMAGE", "North Gate Perimeter Entry", 35.0, "MEDIUM", 0.91, 95.0, "data/demo/cctv/images/north_gate.jpg"),
        ("cctv_vid_01", "DEMO", "CCTV", "VIDEO", "Warehouse Loading Dock Intrusion", 68.0, "HIGH", 0.86, 280.0, "data/demo/cctv/videos/warehouse.mp4"),
        ("upload_img_01", "UPLOAD", "DRONE", "IMAGE", "Manual Aerial Inspection", 10.0, "LOW", 0.94, 105.0, None),
        ("cctv_img_02", "DEMO", "CCTV", "IMAGE", "South Fence Line Patrol", 55.0, "HIGH", 0.89, 120.0, "data/demo/cctv/images/south_fence.jpg"),
        ("drone_vid_02", "DEMO", "DRONE", "VIDEO", "Substation Perimeter Loitering", 42.0, "MEDIUM", 0.87, 210.0, "data/demo/drone/videos/substation.mp4"),
        ("cctv_vid_02", "DEMO", "CCTV", "VIDEO", "Main Entrance Evening Monitoring", 18.0, "LOW", 0.95, 180.0, "data/demo/cctv/videos/entrance.mp4"),
        ("live_stream_01", "LIVE", "CCTV", "VIDEO", "RTSP Camera Stream #4", 78.0, "CRITICAL", 0.84, 150.0, None),
        ("upload_vid_01", "UPLOAD", "CCTV", "VIDEO", "Uploaded Parking Lot Inspection", 28.0, "MEDIUM", 0.90, 260.0, None),
    ]

    for i, (s_id, src, plat, med, title, score, level, conf, proc_time, art) in enumerate(mock_scenarios):
        ts = (now - timedelta(hours=i * 3 + 1)).isoformat()
        rec = AnalysisRecord(
            id=s_id,
            timestamp=ts,
            source_type=src,
            platform=plat,
            media_type=med,
            scenario_name=title,
            threat_score=score,
            threat_level=level,
            confidence_avg=conf,
            processing_time_ms=proc_time,
            status="COMPLETED",
            artifact_path=art
        )
        analysis_repo.save(rec)

        # Seed Alert if High or Critical
        if level in ("HIGH", "CRITICAL"):
            alert = AlertRecord(
                id=str(uuid.uuid4()),
                analysis_id=s_id,
                severity=level,
                reason=f"Restricted perimeter breach detected in scenario '{title}'. Threat score: {score}",
                status="UNACKNOWLEDGED" if i < 3 else "ACKNOWLEDGED",
                created_at=ts
            )
            alert_repo.save(alert)

        # Seed Report
        report = ReportRecord(
            id=str(uuid.uuid4()),
            analysis_id=s_id,
            file_path=f"reports/report_{s_id}.pdf",
            report_type="INCIDENT_SUMMARY" if level in ("HIGH", "CRITICAL") else "DAILY_AUDIT",
            generated_at=ts
        )
        report_repo.save(report)

    # Seed Default Settings
    default_settings = [
        ("ai.model_path", "models/yolov8n.pt", "AI"),
        ("ai.confidence_threshold", "0.45", "AI"),
        ("ai.iou_threshold", "0.50", "AI"),
        ("threat.weights.class", "0.30", "THREAT"),
        ("threat.weights.count", "0.20", "THREAT"),
        ("threat.weights.zone", "0.35", "THREAT"),
        ("threat.weights.motion", "0.15", "THREAT"),
        ("theme.mode", "dark", "SYSTEM"),
        ("database.status", "seeded_and_active", "SYSTEM")
    ]
    for key, val, cat in default_settings:
        settings_repo.set(key, val, cat)

    logger.info("Database startup seeding completed successfully (10 baseline records seeded).")
