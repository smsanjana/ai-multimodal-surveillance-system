"""Unit tests for AnalysisRepository persistence."""

import os
import uuid
import pytest
from src.core.database import DatabaseService
from src.infrastructure.database.repositories import AnalysisRepository
from src.domain.entities import AnalysisRecord, DetectionRecord


def test_analysis_repository_save_and_retrieve(tmp_path):
    db_file = str(tmp_path / "test_surveillance.db")
    db_service = DatabaseService(db_path=db_file)
    repo = AnalysisRepository(db_service)

    analysis_id = str(uuid.uuid4())
    rec = AnalysisRecord(
        id=analysis_id,
        timestamp="2026-09-13T12:00:00",
        source_type="DEMO",
        platform="DRONE",
        media_type="IMAGE",
        scenario_name="Test Scenario",
        threat_score=65.0,
        threat_level="HIGH",
        confidence_avg=0.91,
        processing_time_ms=150.0
    )

    dets = [
        DetectionRecord(
            id=str(uuid.uuid4()),
            analysis_id=analysis_id,
            class_name="person",
            confidence=0.95,
            bbox_json='{"x_min": 10, "y_min": 10, "x_max": 50, "y_max": 50}'
        )
    ]

    saved_rec = repo.save_analysis_with_detections(rec, dets)
    assert saved_rec.id == analysis_id

    fetched_rec = repo.get_by_id(analysis_id)
    assert fetched_rec is not None
    assert fetched_rec.threat_score == 65.0
    assert fetched_rec.threat_level == "HIGH"

    fetched_dets = repo.get_detections_by_analysis_id(analysis_id)
    assert len(fetched_dets) == 1
    assert fetched_dets[0].class_name == "person"
