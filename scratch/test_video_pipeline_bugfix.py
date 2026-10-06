"""Phase 1, 2, and 3 Video Pipeline Verification Script."""

import os
import cv2
import numpy as np
from src.core.di_container import DIContainer
from src.application.video_surveillance_service import VideoSurveillanceService
from src.domain.entities import VideoAnalysisRequest

def generate_synthetic_test_video(file_path: str) -> None:
    """Generates synthetic_military_tracking_test.mp4 (5s, 1280x720 at 25 FPS = 125 frames)."""
    h, w = 720, 1280
    fps = 25.0
    num_frames = 125
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(file_path, fourcc, fps, (w, h))

    if not out.isOpened():
        fourcc = cv2.VideoWriter_fourcc(*'MJPG')
        out = cv2.VideoWriter(file_path, fourcc, fps, (w, h))

    for i in range(num_frames):
        frame = np.zeros((h, w, 3), dtype=np.uint8)
        frame[:] = (30, 35, 45) # Dark grid
        for y in range(0, h, 60):
            cv2.line(frame, (0, y), (w, y), (45, 50, 60), 1)
        for x in range(0, w, 80):
            cv2.line(frame, (x, 0), (x, h), (45, 50, 60), 1)

        # Synthetic geometric target moving across frame
        cx = int(200 + (i / num_frames) * 600)
        cy = int(360 + np.sin(i / 10.0) * 40)
        cv2.rectangle(frame, (cx - 40, cy - 30), (cx + 40, cy + 30), (180, 180, 190), -1)

        cv2.putText(frame, "SYNTHETIC VIDEO PIPELINE TEST", (40, 50), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 200), 2)
        out.write(frame)

    out.release()
    print(f"Generated synthetic test video at: {file_path}")


def run_verifications():
    container = DIContainer()
    video_service: VideoSurveillanceService = container.resolve(VideoSurveillanceService)

    print("=" * 80)
    print("PHASE 1: SYNTHETIC VIDEO PIPELINE INGESTION & INFERENCE TEST")
    print("=" * 80)

    synth_video_path = "scratch/synthetic_military_tracking_test.mp4"
    generate_synthetic_test_video(synth_video_path)

    # Verify process_video method call on VideoSurveillanceService
    req_synth = VideoAnalysisRequest(
        source_type="UPLOAD",
        platform="DRONE",
        scenario_name="Synthetic Video Test",
        video_path=synth_video_path,
        target_sample_fps=5.0
    )

    # Calling process_video (and process_video_analysis)
    resp_synth = video_service.process_video(req_synth)

    print(f"Phase 1 Results:")
    print(f"  - Analysis ID:        {resp_synth.analysis_id}")
    print(f"  - Video Duration:     {resp_synth.video_metadata.duration_seconds:.2f}s ({resp_synth.video_metadata.total_frames} frames)")
    print(f"  - Sampled Frames:     {resp_synth.video_metadata.sampled_frames}")
    print(f"  - Total Detections:   {resp_synth.total_detections}")
    print(f"  - Track Count:        {len(resp_synth.tracks)}")
    print(f"  - Threat Score/Level: {resp_synth.threat_assessment.threat_score} ({resp_synth.threat_assessment.threat_level})")

    assert resp_synth.analysis_id is not None, "Analysis ID missing!"
    assert resp_synth.video_metadata.sampled_frames > 0, "No frames sampled!"

    print("\n" + "=" * 80)
    print("PHASE 2 & 3: MILITARY VIDEO DETECTION, TRACKING & THREAT ASSESSMENT TEST")
    print("=" * 80)

    demo_video_path = "data/demo/drone/videos/kiit_mita_drone_demo.mp4"
    if not os.path.exists(demo_video_path):
        demo_video_path = "data/demo/drone/videos/real_drone_perimeter_surveillance.mp4"

    req_demo = VideoAnalysisRequest(
        source_type="DEMO",
        platform="DRONE",
        scenario_name="Drone Aerial Border Patrol - Routine Transit",
        target_sample_fps=5.0
    )

    resp_demo = video_service.process_video_analysis(req_demo)

    print(f"Phase 2 & 3 Results (KIIT-MiTA Demo Video):")
    print(f"  - Analysis ID:        {resp_demo.analysis_id}")
    print(f"  - Video Duration:     {resp_demo.video_metadata.duration_seconds:.2f}s ({resp_demo.video_metadata.total_frames} frames)")
    print(f"  - Sampled Frames:     {resp_demo.video_metadata.sampled_frames}")
    print(f"  - Total Detections:   {resp_demo.total_detections}")
    print(f"  - Class Counts:       {resp_demo.class_counts}")
    print(f"  - Track Count:        {len(resp_demo.tracks)}")
    for tr in resp_demo.tracks:
        print(f"    * Track #{tr.track_id}: Class={tr.class_name} Detections={tr.detection_count} State={tr.movement_state} Disp={tr.pixel_displacement:.1f}px Dir={tr.trajectory_direction}")
    print(f"  - Threat Score/Level: {resp_demo.threat_assessment.threat_score} ({resp_demo.threat_assessment.threat_level})")

    print("\n" + "=" * 80)
    print("ALL VIDEO PIPELINE VERIFICATION PHASES COMPLETED SUCCESSFULLY!")
    print("=" * 80)

if __name__ == "__main__":
    run_verifications()
