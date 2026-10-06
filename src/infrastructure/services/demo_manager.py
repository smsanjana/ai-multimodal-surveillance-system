"""Built-in Offline Demo Asset Manager for Drone and CCTV Image Scenarios."""

import os
import logging
from typing import Dict, List, Any, Optional
import numpy as np
import cv2

logger = logging.getLogger("SurveillanceSystem")

DEMO_DIR = "data/demo"

# Manifest of 6 built-in demo image scenarios
DEMO_SCENARIOS: List[Dict[str, Any]] = [
    # --- Drone Scenarios ---
    {
        "id": "drone_traffic_obs",
        "platform": "DRONE",
        "title": "Drone Traffic Observation",
        "description": "Routine aerial sweep over main transportation corridor. Vehicle presence and density are evaluated as routine observations.",
        "file_path": os.path.join(DEMO_DIR, "drone", "images", "drone_traffic_density.jpg"),
        "expected_level": "LOW",
        "zone_violation_flag": False,
        "unauthorized_access_signal": False
    },
    {
        "id": "drone_convoy_obs",
        "platform": "DRONE",
        "title": "Drone Convoy/Vehicle Group Observation",
        "description": "Aerial sweep over transport route. Observed vehicle grouping represents routine transit activity.",
        "file_path": os.path.join(DEMO_DIR, "drone", "images", "drone_convoy_movement.jpg"),
        "expected_level": "LOW",
        "zone_violation_flag": False,
        "unauthorized_access_signal": False
    },
    {
        "id": "drone_restricted_entry",
        "platform": "DRONE",
        "title": "Drone Restricted Area Entry",
        "description": "High-altitude perimeter view. Includes explicit verified restricted-zone evidence signal.",
        "file_path": os.path.join(DEMO_DIR, "drone", "images", "drone_restricted_area.jpg"),
        "expected_level": "HIGH",
        "zone_violation_flag": True,
        "unauthorized_access_signal": False
    },

    # --- CCTV Scenarios ---
    {
        "id": "cctv_normal_entrance",
        "platform": "CCTV",
        "title": "CCTV Normal Entrance Activity",
        "description": "Fixed camera monitoring facility main entrance gateway. Routine access activity without restricted-zone signals.",
        "file_path": os.path.join(DEMO_DIR, "cctv", "images", "cctv_entrance_patrol.jpg"),
        "expected_level": "LOW",
        "zone_violation_flag": False,
        "unauthorized_access_signal": False
    },
    {
        "id": "cctv_restricted_gate_entry",
        "platform": "CCTV",
        "title": "CCTV Restricted Gate Vehicle Entry",
        "description": "Fixed view monitoring secure access gate. Includes explicit verified restricted-zone evidence signal.",
        "file_path": os.path.join(DEMO_DIR, "cctv", "images", "cctv_unauthorized_vehicle.jpg"),
        "expected_level": "HIGH",
        "zone_violation_flag": True,
        "unauthorized_access_signal": False
    },
    {
        "id": "cctv_facility_access",
        "platform": "CCTV",
        "title": "CCTV Facility Access Signal (Medium Threat)",
        "description": "Fixed camera monitoring perimeter access point. Includes explicit verified unauthorized access signal.",
        "file_path": os.path.join(DEMO_DIR, "cctv", "images", "cctv_unauthorized_access.jpg"),
        "expected_level": "MEDIUM",
        "zone_violation_flag": False,
        "unauthorized_access_signal": True
    }
]


# Manifest of built-in demo video scenarios (Clearly labeled synthetic offline demo assets)
DEMO_VIDEO_SCENARIOS: List[Dict[str, Any]] = [
    {
        "id": "drone_perimeter_video",
        "platform": "DRONE",
        "title": "Drone Aerial Border Patrol - Routine Transit",
        "description": "Synthetic offline demo video asset showing high-altitude aerial drone monitoring of a border corridor with routine vehicle/convoy transit outside restricted bounds.",
        "file_path": os.path.join(DEMO_DIR, "drone", "videos", "kiit_mita_drone_demo.mp4"),
        "expected_level": "LOW",
        "zone_violation_flag": False,
        "unauthorized_access_signal": False,
        "synthetic_status": "SYNTHETIC_OFFLINE_DEMO"
    },
    {
        "id": "drone_restricted_video",
        "platform": "DRONE",
        "title": "Drone Aerial Border Sweep - Restricted Zone Breach",
        "description": "Synthetic offline demo video asset showing aerial drone tracking of a target unit approaching and crossing a marked restricted boundary zone.",
        "file_path": os.path.join(DEMO_DIR, "drone", "videos", "kiit_mita_drone_restricted_breach.mp4"),
        "expected_level": "HIGH",
        "zone_violation_flag": True,
        "unauthorized_access_signal": False,
        "synthetic_status": "SYNTHETIC_OFFLINE_DEMO"
    },
    {
        "id": "cctv_perimeter_video",
        "platform": "CCTV",
        "title": "CCTV Checkpoint Access Gate - Routine Patrol",
        "description": "Synthetic offline demo video asset showing a fixed CCTV checkpoint camera view monitoring vehicle access along an open facility corridor without restricted zone violations.",
        "file_path": os.path.join(DEMO_DIR, "cctv", "videos", "cctv_perimeter_demo.mp4"),
        "expected_level": "LOW",
        "zone_violation_flag": False,
        "unauthorized_access_signal": False,
        "synthetic_status": "SYNTHETIC_OFFLINE_DEMO"
    },
    {
        "id": "cctv_restricted_video",
        "platform": "CCTV",
        "title": "CCTV Restricted Perimeter - Unauthorized Gate Access",
        "description": "Synthetic offline demo video asset showing a fixed CCTV security camera view of a restricted gate where a vehicle crosses into a secure facility zone.",
        "file_path": os.path.join(DEMO_DIR, "cctv", "videos", "cctv_restricted_gate_entry.mp4"),
        "expected_level": "HIGH",
        "zone_violation_flag": True,
        "unauthorized_access_signal": False,
        "synthetic_status": "SYNTHETIC_OFFLINE_DEMO"
    },
    {
        "id": "cctv_critical_video_breach",
        "platform": "CCTV",
        "title": "CCTV High Security Gateway - Compound Access Breach",
        "description": "Synthetic offline demo video asset showing a fixed CCTV camera monitoring a secure compound. Includes both restricted zone breach and unauthorized access signals.",
        "file_path": os.path.join(DEMO_DIR, "cctv", "videos", "cctv_restricted_gate_entry.mp4"),
        "expected_level": "CRITICAL",
        "zone_violation_flag": True,
        "unauthorized_access_signal": True,
        "synthetic_status": "SYNTHETIC_OFFLINE_DEMO"
    }
]


class DemoManager:
    """Manages offline demo image and video scenarios and ensures local demo files exist."""

    def __init__(self, demo_dir: str = DEMO_DIR):
        self.demo_dir = demo_dir
        self.ensure_demo_assets_exist()

    def ensure_demo_assets_exist(self) -> None:
        """Verifies local demo image and video files exist."""
        # 1. Image scenarios
        for scenario in DEMO_SCENARIOS:
            file_path = scenario["file_path"]
            dir_name = os.path.dirname(file_path)
            os.makedirs(dir_name, exist_ok=True)

            if not os.path.exists(file_path):
                logger.info("Generating synthetic demo image asset at %s", file_path)
                self._generate_synthetic_demo_image(file_path, scenario["title"], scenario["platform"])

        # 2. Video scenarios
        for scenario in DEMO_VIDEO_SCENARIOS:
            file_path = scenario["file_path"]
            dir_name = os.path.dirname(file_path)
            os.makedirs(dir_name, exist_ok=True)

            if not os.path.exists(file_path):
                logger.info("Generating synthetic demo video asset at %s", file_path)
                self._generate_synthetic_demo_video(
                    file_path,
                    scenario["title"],
                    scenario["platform"],
                    scenario.get("zone_violation_flag", False)
                )


    def _generate_synthetic_demo_image(self, file_path: str, title: str, platform: str) -> None:
        """Generates a structured synthetic surveillance image (1280x720) for offline demo testing."""
        h, w = 720, 1280
        img = np.zeros((h, w, 3), dtype=np.uint8)
        
        # Dark command-room grid background
        img[:] = (30, 35, 45)

        # Draw grid lines
        for y in range(0, h, 60):
            cv2.line(img, (0, y), (w, y), (45, 50, 60), 1)
        for x in range(0, w, 80):
            cv2.line(img, (x, 0), (x, h), (45, 50, 60), 1)

        # Draw simulated target elements depending on scenario
        if "Intrusion" in title or "Unauthorized" in title:
            # High threat elements
            cv2.rectangle(img, (400, 250), (600, 550), (180, 180, 190), -1)  # vehicle box
            cv2.circle(img, (750, 350), 30, (200, 200, 200), -1)             # person shape
            cv2.circle(img, (820, 370), 25, (200, 200, 200), -1)
        elif "Traffic" in title or "Parking" in title:
            # Medium threat elements
            cv2.rectangle(img, (300, 300), (500, 450), (180, 180, 190), -1)
            cv2.rectangle(img, (650, 320), (850, 470), (180, 180, 190), -1)
        else:
            # Low threat element
            cv2.circle(img, (640, 360), 25, (200, 200, 200), -1)

        # Header watermark text
        header_text = f"SURVEILLANCE DEMO FEED: [{platform}] - {title.upper()}"
        cv2.putText(img, header_text, (40, 50), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 200), 2, cv2.LINE_AA)
        cv2.putText(img, "STATUS: OFFLINE DEMO ASSET (1280x720)", (40, 90), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (180, 180, 180), 1, cv2.LINE_AA)

        cv2.imwrite(file_path, img)

    def _generate_synthetic_demo_video(
        self, file_path: str, title: str, platform: str, is_restricted: bool = False
    ) -> None:
        """Generates a playable 20-second mp4 video (1280x720 at 25 FPS = 500 frames) with target movement."""
        h, w = 720, 1280
        fps = 25.0
        num_frames = 500
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        out = cv2.VideoWriter(file_path, fourcc, fps, (w, h))

        if not out.isOpened():
            fourcc = cv2.VideoWriter_fourcc(*'MJPG')
            out = cv2.VideoWriter(file_path, fourcc, fps, (w, h))

        # Check local test images to composite realistic military targets
        test_img_dir = "data/datasets/military/KIIT-MiTA/test/images"
        sample_img = None
        if os.path.exists(test_img_dir):
            files = sorted([f for f in os.listdir(test_img_dir) if f.endswith(('.jpeg', '.jpg', '.png'))])
            if files:
                # Select a high-confidence military target base image depending on platform/scenario
                idx = 0
                if "Restricted" in title or "Gate" in title:
                    idx = min(15, len(files) - 1)
                elif platform.upper() == "CCTV":
                    idx = min(10, len(files) - 1)
                base_img_path = os.path.join(test_img_dir, files[idx])
                sample_img = cv2.imread(base_img_path)
                if sample_img is not None:
                    sample_img = cv2.resize(sample_img, (w, h))

        for i in range(num_frames):
            if sample_img is not None:
                frame = sample_img.copy()
            else:
                frame = np.zeros((h, w, 3), dtype=np.uint8)
                frame[:] = (30, 35, 45)
                for y in range(0, h, 60):
                    cv2.line(frame, (0, y), (w, y), (45, 50, 60), 1)
                for x in range(0, w, 80):
                    cv2.line(frame, (x, 0), (x, h), (45, 50, 60), 1)

            # Apply slight spatial translation across frames to simulate continuous movement
            dx = int((i / num_frames) * 80)
            dy = int(np.sin(i / 15.0) * 10)
            M = np.float32([[1, 0, dx - 40], [0, 1, dy]])
            frame = cv2.warpAffine(frame, M, (w, h), borderMode=cv2.BORDER_REFLECT)

            # Overlay synthetic telemetry banner and zone boundary markings
            hud_color = (0, 200, 255) if is_restricted else (0, 255, 150)
            status_tag = "RESTRICTED BOUNDARY BREACH" if is_restricted else "ROUTINE SURVEILLANCE"

            cv2.putText(frame, f"[SYNTHETIC OFFLINE DEMO] {platform} - {title.upper()}", (30, 40), cv2.FONT_HERSHEY_SIMPLEX, 0.65, (255, 255, 255), 2, cv2.LINE_AA)
            cv2.putText(frame, f"PERSPECTIVE: {platform} | STATUS: {status_tag} | TIME: {i/fps:.2f}s | FRAME: {i+1}/{num_frames}", (30, 70), cv2.FONT_HERSHEY_SIMPLEX, 0.5, hud_color, 1, cv2.LINE_AA)

            if is_restricted:
                cv2.line(frame, (w // 2, 0), (w // 2, h), (0, 0, 255), 3)
                cv2.putText(frame, "<<< RESTRICTED PERIMETER ZONE BOUNDARY >>>", (w // 2 + 15, 120), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 2, cv2.LINE_AA)
            else:
                cv2.line(frame, (w // 4, 0), (w // 4, h), (0, 255, 0), 1)
                cv2.putText(frame, "OPEN TRANSIT CORRIDOR", (w // 4 + 15, 120), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (0, 255, 0), 1, cv2.LINE_AA)

            out.write(frame)

        out.release()

    def list_scenarios(self, platform: Optional[str] = None) -> List[Dict[str, Any]]:
        """Returns list of available demo scenarios, optionally filtered by platform."""
        if not platform:
            return DEMO_SCENARIOS
        plat = platform.upper()
        return [s for s in DEMO_SCENARIOS if s["platform"].upper() == plat]

    def list_video_scenarios(self, platform: Optional[str] = None) -> List[Dict[str, Any]]:
        """Returns list of available demo video scenarios, optionally filtered by platform."""
        if not platform:
            return DEMO_VIDEO_SCENARIOS
        plat = platform.upper()
        return [s for s in DEMO_VIDEO_SCENARIOS if s["platform"].upper() == plat]

    def _match_scenario_in_list(self, target: str, scenarios: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        target = target.lower().strip()
        # 1. Exact match by id or title
        for s in scenarios:
            if s["id"].lower() == target or s["title"].lower() == target:
                return s
        # 2. Substring match by id or title
        for s in scenarios:
            sid = s["id"].lower()
            stitle = s["title"].lower()
            if target in sid or target in stitle:
                return s
        # 3. Word set overlap match
        target_words = set(target.replace("-", " ").replace("_", " ").split())
        if target_words:
            best_match = None
            best_overlap = 0
            for s in scenarios:
                s_words = set(s["id"].replace("-", " ").replace("_", " ").split()) | set(s["title"].lower().replace("-", " ").replace("_", " ").split())
                overlap = len(target_words & s_words)
                if overlap > best_overlap:
                    best_overlap = overlap
                    best_match = s
            if best_match and best_overlap > 0:
                return best_match
        return None

    def get_image_scenario(self, scenario_id_or_title: str) -> Optional[Dict[str, Any]]:
        """Finds image scenario metadata by ID or title."""
        return self._match_scenario_in_list(scenario_id_or_title, DEMO_SCENARIOS)

    def get_video_scenario(self, scenario_id_or_title: str) -> Optional[Dict[str, Any]]:
        """Finds video scenario metadata by ID or title."""
        return self._match_scenario_in_list(scenario_id_or_title, DEMO_VIDEO_SCENARIOS)

    def get_scenario(self, scenario_id_or_title: str, media_type: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """Finds scenario metadata by ID or title (image or video)."""
        if media_type and media_type.upper() == "VIDEO":
            return self.get_video_scenario(scenario_id_or_title)
        if media_type and media_type.upper() == "IMAGE":
            return self.get_image_scenario(scenario_id_or_title)

        matched = self.get_image_scenario(scenario_id_or_title)
        if matched:
            return matched
        return self.get_video_scenario(scenario_id_or_title)

    def load_demo_image_bytes(self, scenario_id_or_title: str) -> bytes:
        """Reads raw binary bytes of specified demo scenario image."""
        scenario = self.get_image_scenario(scenario_id_or_title)
        if not scenario:
            scenario = DEMO_SCENARIOS[0]

        file_path = scenario["file_path"]
        if not os.path.exists(file_path):
            self.ensure_demo_assets_exist()

        with open(file_path, "rb") as f:
            return f.read()

