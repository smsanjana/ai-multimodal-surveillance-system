"""Analyst Review Service orchestrating human analyst decision workflow and audit history logging."""

import uuid
from datetime import datetime
from typing import List, Optional
from src.domain.interfaces import IAnalystReviewService, IAnalystReviewRepository
from src.domain.entities import AnalystReviewRecord, AnalystReviewHistoryRecord
from src.core.exceptions import ValidationError


class AnalystReviewService(IAnalystReviewService):
    """
    Manages human analyst review workflow (PENDING_REVIEW, ACKNOWLEDGED, FALSE_POSITIVE, ESCALATED),
    resolving default Analyst ID from config and logging transition history in SQLite without mutating AI scores.
    """

    VALID_STATUSES = {"PENDING_REVIEW", "ACKNOWLEDGED", "FALSE_POSITIVE", "ESCALATED"}

    def __init__(
        self,
        review_repository: IAnalystReviewRepository,
        default_analyst_id: str = "OPERATOR_01"
    ):
        self.review_repo = review_repository
        self.default_analyst_id = default_analyst_id

    def submit_review(
        self,
        analysis_id: str,
        review_status: str,
        analyst_id: Optional[str] = None,
        notes: Optional[str] = None
    ) -> AnalystReviewRecord:
        """
        Submits human analyst review decision and logs state transition in SQLite:
        - Validates review_status in ('PENDING_REVIEW', 'ACKNOWLEDGED', 'FALSE_POSITIVE', 'ESCALATED').
        - Resolves analyst_id to default_analyst_id if None.
        - Preserves 100% of machine-generated AI threat scores without overwriting.
        - Records from_status -> to_status transition history row.
        """
        status_upper = review_status.upper()
        if status_upper not in self.VALID_STATUSES:
            raise ValidationError(
                f"Invalid review status '{review_status}'. Must be one of {sorted(list(self.VALID_STATUSES))}."
            )

        active_analyst_id = analyst_id or self.default_analyst_id
        now_str = datetime.utcnow().isoformat()

        # Check existing review record
        existing = self.review_repo.get_review_by_analysis_id(analysis_id)

        if existing:
            review_id = existing.id
            from_status = existing.review_status
            created_at = existing.created_at
        else:
            review_id = str(uuid.uuid4())
            from_status = "PENDING_REVIEW"
            created_at = now_str

        review_record = AnalystReviewRecord(
            id=review_id,
            analysis_id=analysis_id,
            review_status=status_upper,
            analyst_id=active_analyst_id,
            notes=notes,
            created_at=created_at,
            updated_at=now_str
        )

        history_entry = AnalystReviewHistoryRecord(
            history_id=str(uuid.uuid4()),
            review_id=review_id,
            analysis_id=analysis_id,
            from_status=from_status,
            to_status=status_upper,
            analyst_id=active_analyst_id,
            notes=notes,
            timestamp=now_str
        )

        return self.review_repo.save_review(review_record, history_entry)

    def get_review_for_analysis(self, analysis_id: str) -> AnalystReviewRecord:
        """Retrieves analyst review record for analysis_id, returning default PENDING_REVIEW if unreviewed."""
        review = self.review_repo.get_review_by_analysis_id(analysis_id)
        if not review:
            return AnalystReviewRecord(
                id=str(uuid.uuid4()),
                analysis_id=analysis_id,
                review_status="PENDING_REVIEW",
                analyst_id=self.default_analyst_id
            )
        return review

    def get_review_history(self, review_id: str) -> List[AnalystReviewHistoryRecord]:
        """Retrieves full state transition audit history for a review ID."""
        return self.review_repo.get_review_history(review_id)
