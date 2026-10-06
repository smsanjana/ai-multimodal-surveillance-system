"""Unit tests for Surveillance Incident Report compiler."""

import pytest
from src.domain.entities import AnalysisRecord, DetectionRecord, TrackRecord
from src.ui.pages.reports import compile_incident_report


def test_compile_incident_report_full():
    record = AnalysisRecord(
        id="test_analysis_123",
        timestamp="2026-09-28T12:00:00Z",
        source_type="DEMO",
        platform="DRONE",
        media_type="VIDEO",
        scenario_name="Drone Perimeter Sweep",
        threat_score=75.5,
        threat_level="HIGH",
        confidence_avg=0.88,
        processing_time_ms=145.2,
        status="COMPLETED"
    )

    detections = [
        DetectionRecord(id="d1", analysis_id="test_analysis_123", class_name="Tank", confidence=0.92, frame_index=5),
        DetectionRecord(id="d2", analysis_id="test_analysis_123", class_name="Soldier", confidence=0.84, frame_index=5),
    ]

    tracks = [
        {
            "track_id": 1,
            "class_name": "Tank",
            "first_frame": 1,
            "last_frame": 10,
            "detection_count": 8,
            "avg_confidence": 0.92,
            "movement_state": "MOVING",
            "pixel_displacement": 45.2,
            "trajectory_direction": "North-East"
        }
    ]

    report = compile_incident_report(record, detections=detections, tracks=tracks, report_type="INCIDENT_SUMMARY", include_sop=True)

    assert "SURVEILLANCE INCIDENT & TELEMETRY REPORT" in report
    assert "test_analysis_123" in report
    assert "DRONE" in report
    assert "VIDEO" in report
    assert "HIGH" in report
    assert "75.5 / 100" in report
    assert "Tank" in report
    assert "Soldier" in report
    assert "Track #1" in report
    assert "North-East" in report


def test_compile_incident_report_missing_optional_fields():
    record = AnalysisRecord(
        id="test_analysis_minimal",
        timestamp="2026-09-28T12:00:00Z",
        source_type="UPLOAD",
        platform="CCTV",
        media_type="IMAGE",
        scenario_name=None,
        threat_score=0.0,
        threat_level="LOW",
        confidence_avg=0.0,
        processing_time_ms=50.0,
        status="COMPLETED"
    )

    report = compile_incident_report(record, detections=None, tracks=None, report_type="DAILY_AUDIT", include_sop=False)

    assert "test_analysis_minimal" in report
    assert "Custom Upload / Feed" in report
    assert "LOW" in report
    assert "No individual detection records logged" in report
    assert "Multi-Object Tracking" not in report  # Since media_type == IMAGE


def test_compile_incident_report_none_record():
    report = compile_incident_report(None)
    assert "No analysis record selected" in report
