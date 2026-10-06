"""Verification script for Case A, Case B, Case C, and Case D evidence-based threat scoring."""

from src.core.di_container import DIContainer
from src.application.image_surveillance_service import ImageSurveillanceService
from src.domain.entities import ImageAnalysisRequest

def run_tests():
    container = DIContainer()
    service: ImageSurveillanceService = container.resolve(ImageSurveillanceService)

    print("=" * 80)
    print("EVIDENCE-BASED THREAT ASSESSMENT VERIFICATION RUN")
    print("=" * 80)

    # CASE A: Normal image with detections, no zone flag, no access flag
    req_a = ImageAnalysisRequest(
        source_type="DEMO",
        platform="DRONE",
        scenario_name="Drone Traffic Observation",
        zone_violation_flag=False,
        unauthorized_access_signal=False
    )
    res_a = service.process_image(req_a)
    score_a = res_a.threat_assessment.threat_score
    level_a = res_a.threat_assessment.threat_level
    det_a = len(res_a.detections)
    print(f"CASE A (Detection Only):                  ID={res_a.analysis_id[:8]} Detections={det_a} Zone=False Access=False => Score={score_a} Level={level_a}")
    assert score_a == 5.0 and level_a == "LOW", f"CASE A failed! Expected 5.0 LOW, got {score_a} {level_a}"

    # CASE B: Restricted-zone demo with zone_violation_flag=True
    req_b = ImageAnalysisRequest(
        source_type="DEMO",
        platform="DRONE",
        scenario_name="Drone Restricted Area Entry",
        zone_violation_flag=True,
        unauthorized_access_signal=False
    )
    res_b = service.process_image(req_b)
    score_b = res_b.threat_assessment.threat_score
    level_b = res_b.threat_assessment.threat_level
    det_b = len(res_b.detections)
    print(f"CASE B (Restricted Zone Breach):           ID={res_b.analysis_id[:8]} Detections={det_b} Zone=True  Access=False => Score={score_b} Level={level_b}")
    assert score_b == 70.0 and level_b == "HIGH", f"CASE B failed! Expected 70.0 HIGH, got {score_b} {level_b}"

    # CASE C: Unauthorized access signal=True, no zone violation
    req_c = ImageAnalysisRequest(
        source_type="DEMO",
        platform="CCTV",
        scenario_name="CCTV Facility Access Signal (Medium Threat)",
        zone_violation_flag=False,
        unauthorized_access_signal=True
    )
    res_c = service.process_image(req_c)
    score_c = res_c.threat_assessment.threat_score
    level_c = res_c.threat_assessment.threat_level
    det_c = len(res_c.detections)
    print(f"CASE C (Unauthorized Access Signal Only): ID={res_c.analysis_id[:8]} Detections={det_c} Zone=False Access=True  => Score={score_c} Level={level_c}")
    assert score_c == 25.0 and level_c == "MEDIUM", f"CASE C failed! Expected 25.0 MEDIUM, got {score_c} {level_c}"

    # CASE D: Zone violation + unauthorized access with detections
    req_d = ImageAnalysisRequest(
        source_type="DEMO",
        platform="CCTV",
        scenario_name="CCTV Restricted Gate Vehicle Entry",
        zone_violation_flag=True,
        unauthorized_access_signal=True
    )
    res_d = service.process_image(req_d)
    score_d = res_d.threat_assessment.threat_score
    level_d = res_d.threat_assessment.threat_level
    det_d = len(res_d.detections)
    print(f"CASE D (Zone Breach + Access Breach):     ID={res_d.analysis_id[:8]} Detections={det_d} Zone=True  Access=True  => Score={score_d} Level={level_d}")
    assert score_d == 90.0 and level_d == "CRITICAL", f"CASE D failed! Expected 90.0 CRITICAL, got {score_d} {level_d}"

    print("=" * 80)
    print("ALL 4 THREAT SCORING CASES VERIFIED SUCCESSFULLY!")
    print("=" * 80)

if __name__ == "__main__":
    run_tests()
