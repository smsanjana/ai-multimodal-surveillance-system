"""Contextual Threat Scoring Service implementing AbstractThreatScoringService."""

from typing import List, Dict, Any
from src.domain.interfaces import AbstractThreatScoringService
from src.domain.entities import DetectionResult, ThreatAssessmentResult, FactorContribution


class ThreatScoringService(AbstractThreatScoringService):
    """
    Evaluates detected objects and contextual scenario signals into a 0.0-100.0 threat score
    and classifies into LOW, MEDIUM, HIGH, or CRITICAL threat levels.

    Scoring Weights & Model:
    - BASELINE OBSERVATION (0.0 - 10.0 pts):
      * Zero detections: 0.0 delta
      * Active frame observations: 5.0 delta (LOW level baseline)
    - VERIFIED SECURITY EVIDENCE (+60.0 to +70.0 pts):
      * Verified restricted-zone violation signal: +65.0 delta (HIGH level)
      * Absent/false zone signal: 0.0 delta
    - VERIFIED ACCESS BREACH CONDITION (+20.0 pts):
      * Explicit verified unauthorized access signal: +20.0 delta (CRITICAL level)
    - NO THREAT DELTA (0.0 pts):
      * Object classes, counts, crowding density, and scenario names NEVER contribute threat points.
    """

    def evaluate_threat(
        self, detections: List[DetectionResult], metadata: Dict[str, Any]
    ) -> ThreatAssessmentResult:
        """
        Calculates threat score strictly from verified security evidence signals.

        :param detections: List of object DetectionResult items.
        :param metadata: Contextual metadata (platform, scenario_name, zone_violation_flag, etc.).
        :return: ThreatAssessmentResult DTO.
        """
        score = 0.0
        factors: List[FactorContribution] = []

        # 1. Baseline Surveillance Observation Factor (0.0 - 10.0 pts max)
        if not detections:
            factors.append(
                FactorContribution(
                    factor_name="Zero Detections Baseline",
                    score_delta=0.0,
                    description="Clear surveillance sector without detected entities."
                )
            )
        else:
            class_counts: Dict[str, int] = {}
            for det in detections:
                class_counts[det.class_name] = class_counts.get(det.class_name, 0) + 1

            counts_desc_parts = [f"{count} {cls}" for cls, count in class_counts.items()]
            counts_str = ", ".join(counts_desc_parts)

            baseline_delta = 5.0
            score += baseline_delta
            factors.append(
                FactorContribution(
                    factor_name="Surveillance Baseline Observation",
                    score_delta=baseline_delta,
                    description=f"Identified {len(detections)} total object(s) ({counts_str}). Object presence is a routine surveillance observation."
                )
            )

        # 2. Verified Security Evidence: Restricted-Zone Violation (+65.0 pts)
        zone_violation = bool(metadata.get("zone_violation_flag", False))
        if zone_violation:
            zone_delta = 65.0
            score += zone_delta
            factors.append(
                FactorContribution(
                    factor_name="Verified Restricted Zone Signal",
                    score_delta=zone_delta,
                    description="Verified pre-existing restricted-zone violation signal registered."
                )
            )
        else:
            factors.append(
                FactorContribution(
                    factor_name="Restricted Zone Signal",
                    score_delta=0.0,
                    description="No restricted-zone violation was established."
                )
            )

        # 3. Verified Access Breach Condition (Optional explicit signal: +20.0 pts)
        unauth_signal = bool(metadata.get("unauthorized_access_signal", False))
        if unauth_signal:
            access_delta = 20.0
            score += access_delta
            factors.append(
                FactorContribution(
                    factor_name="Verified Unauthorized Access Signal",
                    score_delta=access_delta,
                    description="Verified perimeter access breach signal registered."
                )
            )

        # Cap score between 0.0 and 100.0
        final_score = min(100.0, max(0.0, round(score, 1)))

        # Threat Level Mapping (Preserving strict boundaries)
        if final_score < 25.0:
            threat_level = "LOW"
        elif final_score < 50.0:
            threat_level = "MEDIUM"
        elif final_score < 75.0:
            threat_level = "HIGH"
        else:
            threat_level = "CRITICAL"

        return ThreatAssessmentResult(
            threat_score=final_score,
            threat_level=threat_level,
            factors=factors,
            xai_reason="",       # Populated by ExplainabilityService
            recommended_sop=""   # Populated by ExplainabilityService
        )

