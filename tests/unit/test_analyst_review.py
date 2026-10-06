"""Unit tests for AnalystReviewService, AnalystReviewRepository, and audit trail transition logging."""

import os
import pytest
from src.core.database import DatabaseService
from src.infrastructure.database.repositories import AnalystReviewRepository
from src.application.analyst_review_service import AnalystReviewService
from src.core.exceptions import ValidationError


@pytest.fixture
def temp_db(tmp_path):
    db_file = str(tmp_path / "test_surveillance.db")
    db_service = DatabaseService(db_path=db_file)
    return db_service


def test_submit_review_initial_flow(temp_db):
    repo = AnalystReviewRepository(temp_db)
    service = AnalystReviewService(review_repository=repo, default_analyst_id="OPERATOR_01")

    # Initial submission: PENDING_REVIEW -> ACKNOWLEDGED
    review = service.submit_review(
        analysis_id="A201",
        review_status="ACKNOWLEDGED",
        notes="Verified routine convoy patrol."
    )

    assert review.analysis_id == "A201"
    assert review.review_status == "ACKNOWLEDGED"
    assert review.analyst_id == "OPERATOR_01"
    assert review.notes == "Verified routine convoy patrol."

    # Retrieve from DB
    retrieved = repo.get_review_by_analysis_id("A201")
    assert retrieved is not None
    assert retrieved.review_status == "ACKNOWLEDGED"

    # Check history
    history = repo.get_review_history(review.id)
    assert len(history) == 1
    assert history[0].from_status == "PENDING_REVIEW"
    assert history[0].to_status == "ACKNOWLEDGED"


def test_submit_review_false_positive_transition(temp_db):
    repo = AnalystReviewRepository(temp_db)
    service = AnalystReviewService(review_repository=repo, default_analyst_id="OPERATOR_02")

    # Step 1: ACKNOWLEDGED
    r1 = service.submit_review("A202", "ACKNOWLEDGED", analyst_id="OPERATOR_02")
    assert r1.review_status == "ACKNOWLEDGED"

    # Step 2: Transition to FALSE_POSITIVE
    r2 = service.submit_review("A202", "FALSE_POSITIVE", analyst_id="OPERATOR_02", notes="Sensor glare misclassification.")
    assert r2.review_status == "FALSE_POSITIVE"

    # Verify history has 2 records
    history = repo.get_review_history(r1.id)
    assert len(history) == 2
    assert history[0].from_status == "PENDING_REVIEW"
    assert history[0].to_status == "ACKNOWLEDGED"
    assert history[1].from_status == "ACKNOWLEDGED"
    assert history[1].to_status == "FALSE_POSITIVE"


def test_invalid_status_rejection(temp_db):
    repo = AnalystReviewRepository(temp_db)
    service = AnalystReviewService(review_repository=repo)

    with pytest.raises(ValidationError):
        service.submit_review("A203", "INVALID_STATUS_STRING")
