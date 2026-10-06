"""Explainable AI (XAI) & Decision Support Service implementing AbstractExplainabilityService."""

from typing import List, Dict, Any
from src.domain.interfaces import AbstractExplainabilityService
from src.domain.entities import DetectionResult


class ExplainabilityService(AbstractExplainabilityService):
    """
    Generates human-readable decision rationale, factor attribution summaries,
    and Standard Operating Procedure (SOP) operator decision-support action steps.
    """

    SOP_MAPPING = {
        "LOW": (
            "1. Continue routine monitoring and retain the event in the audit history."
        ),
        "MEDIUM": (
            "1. Increase operator review and perform additional visual verification."
        ),
        "HIGH": (
            "1. Escalate to the designated site duty supervisor and follow authorized site security procedures."
        ),
        "CRITICAL": (
            "1. Immediately escalate to the designated supervisor, verify the event, and follow the organization's authorized emergency response procedure."
        )
    }

    def explain(
        self, threat_score: float, threat_level: str, detections: List[DetectionResult], metadata: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Generates natural language rationale narrative and retrieves SOP recommendations.

        :param threat_score: Quantitative threat score (0.0 - 100.0).
        :param threat_level: Threat level string (LOW, MEDIUM, HIGH, CRITICAL).
        :param detections: List of object DetectionResult items.
        :param metadata: Contextual scenario metadata dictionary.
        :return: Dictionary containing 'xai_reason' and 'recommended_sop'.
        """
        total_objects = len(detections)
        platform = str(metadata.get("platform", "DRONE")).upper()
        zone_violation = bool(metadata.get("zone_violation_flag", False))

        # Class counts breakdown
        counts: Dict[str, int] = {}
        for det in detections:
            counts[det.class_name] = counts.get(det.class_name, 0) + 1

        counts_str = ", ".join([f"{count} {cls}" for cls, count in counts.items()]) if counts else "no objects"

        # Construct natural language rationale based strictly on actual evidence
        if zone_violation:
            narrative = (
                f"Elevated threat assessment (Score: {threat_score:.1f}/100, {threat_level}) driven by a verified "
                f"pre-existing restricted-zone violation signal. The detected entities ({counts_str}) are treated as observations "
                f"and are not independently classified as threats. No temporal risk signal was evaluated in this image-only analysis."
            )
        else:
            if total_objects == 0:
                narrative = (
                    f"LOW threat assessment (Score: {threat_score:.1f}/100). Clear sector without detected entities. "
                    f"No verified security-risk signal was available from this image analysis, and no temporal risk signal was evaluated in this image-only analysis."
                )
            else:
                narrative = (
                    f"LOW threat assessment (Score: {threat_score:.1f}/100). Identified {total_objects} object(s) ({counts_str}) "
                    f"in {platform} sector as normal surveillance observations. No verified security-risk signal was available "
                    f"from this image analysis, and no temporal risk signal was evaluated in this image-only analysis."
                )

        recommended_sop = self.SOP_MAPPING.get(threat_level, self.SOP_MAPPING["LOW"])

        return {
            "xai_reason": narrative,
            "recommended_sop": recommended_sop
        }

