"""Contextual Assessment Service orchestrating spatial zone evaluation and behavior event classification."""

import uuid
from typing import List, Optional, Dict, Any, Tuple
from src.domain.interfaces import IContextualAssessmentService
from src.domain.entities import (
    DetectionResult, TrackRecord, RestrictedZone, ObservableEvent,
    SeparateContextualAssessment
)
from src.infrastructure.services.spatial_zone_evaluator import SpatialZoneEvaluator


class ContextualAssessmentService(IContextualAssessmentService):
    """
    Orchestrates spatial zone intersection math, observable behavior event classification,
    and Separate Proposed Contextual Assessment generation without mutating Feature 003 primary threat scores.
    """

    def __init__(self, zone_evaluator: Optional[SpatialZoneEvaluator] = None):
        self.zone_evaluator = zone_evaluator or SpatialZoneEvaluator()

    def evaluate_spatial_context(
        self,
        analysis_id: str,
        detections: List[DetectionResult],
        tracks: List[TrackRecord],
        platform: str,
        zones: Optional[List[RestrictedZone]] = None,
        scenario_metadata_signal: bool = False
    ) -> SeparateContextualAssessment:
        """
        Evaluates spatial target positions against normalized restricted zones [0.0, 1.0],
        computes spatial boundary-crossing events, and generates a Separate Proposed Spatial Assessment.
        """
        events: List[ObservableEvent] = []
        computed_spatial_breach = False

        # Filter active zones matching current platform
        active_zones = [z for z in (zones or []) if z.is_active and z.platform.upper() == platform.upper()]

        # Default fallback if no spatial zone configuration exists
        if not active_zones:
            # Evaluate tracks for routine transit
            for tr in tracks:
                events.append(ObservableEvent(
                    event_id=str(uuid.uuid4()),
                    track_id=tr.track_id,
                    class_name=tr.class_name,
                    event_type="ROUTINE_TRANSIT",
                    timestamp_sec=tr.first_timestamp,
                    description=f"Target Track #{tr.track_id} ({tr.class_name}) observed in open transit corridor outside restricted zone bounds.",
                    confidence_score=tr.avg_confidence,
                    is_uncertain=tr.avg_confidence < 0.40
                ))

            return SeparateContextualAssessment(
                analysis_id=analysis_id,
                spatial_threat_score=0.0,
                spatial_threat_level="LOW",
                computed_spatial_breach=False,
                scenario_metadata_signal=scenario_metadata_signal,
                events=events,
                xai_reason="No spatial restricted zones configured for sector. Movement evaluated as routine open transit.",
                recommended_sop="Continue routine surveillance monitoring of open sector."
            )

        # Spatial zone evaluation across tracks
        zone_intersection_count = 0

        for tr in tracks:
            # Check trajectory points for spatial zone intersection
            track_intersects = False
            for pt in tr.trajectory_points:
                # Normalize pixel coordinates (assuming 1280x720 frame default)
                norm_cx = pt.x / 1280.0
                norm_cy = pt.y / 720.0
                
                for zone in active_zones:
                    if self.zone_evaluator.is_centroid_in_zone((norm_cx, norm_cy), zone):
                        track_intersects = True
                        break
                if track_intersects:
                    break

            if track_intersects:
                computed_spatial_breach = True
                zone_intersection_count += 1
                
                event_type = "STATIONARY_OBJECT_IN_ZONE" if tr.movement_state.upper() == "STATIONARY" else "ZONE_ENTRY"
                desc = (
                    f"Target Track #{tr.track_id} ({tr.class_name}) stationary inside spatial restricted zone boundary."
                    if event_type == "STATIONARY_OBJECT_IN_ZONE"
                    else f"Target Track #{tr.track_id} ({tr.class_name}) entered spatial restricted zone boundary."
                )

                events.append(ObservableEvent(
                    event_id=str(uuid.uuid4()),
                    track_id=tr.track_id,
                    class_name=tr.class_name,
                    event_type=event_type,
                    timestamp_sec=tr.first_timestamp,
                    description=desc,
                    confidence_score=tr.avg_confidence,
                    is_uncertain=tr.avg_confidence < 0.40
                ))
            else:
                events.append(ObservableEvent(
                    event_id=str(uuid.uuid4()),
                    track_id=tr.track_id,
                    class_name=tr.class_name,
                    event_type="ROUTINE_TRANSIT",
                    timestamp_sec=tr.first_timestamp,
                    description=f"Target Track #{tr.track_id} ({tr.class_name}) in routine transit outside spatial zone bounds.",
                    confidence_score=tr.avg_confidence,
                    is_uncertain=tr.avg_confidence < 0.40
                ))

        # Compute separate spatial score (isolated from Feature 003 primary score)
        spatial_score = 70.0 if computed_spatial_breach else (5.0 if tracks else 0.0)
        spatial_level = "HIGH" if computed_spatial_breach else "LOW"

        xai_reason = (
            f"Separate Spatial Assessment: Computed {zone_intersection_count} spatial zone intersection event(s) across target tracks."
            if computed_spatial_breach
            else "Separate Spatial Assessment: Target tracks observed outside spatial zone boundaries."
        )

        sop = (
            "1. Dispatch security patrol to verify spatial boundary breach sector. 2. Log spatial telemetry."
            if computed_spatial_breach
            else "1. Continue routine surveillance monitoring."
        )

        return SeparateContextualAssessment(
            analysis_id=analysis_id,
            spatial_threat_score=spatial_score,
            spatial_threat_level=spatial_level,
            computed_spatial_breach=computed_spatial_breach,
            scenario_metadata_signal=scenario_metadata_signal,
            events=events,
            xai_reason=xai_reason,
            recommended_sop=sop
        )
