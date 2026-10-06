"""Unit tests for DemoManager."""

from src.infrastructure.services.demo_manager import DemoManager, DEMO_SCENARIOS


def test_demo_manager_listing():
    manager = DemoManager()
    all_scens = manager.list_scenarios()
    assert len(all_scens) == 6

    drone_scens = manager.list_scenarios(platform="DRONE")
    assert len(drone_scens) == 3
    for s in drone_scens:
        assert s["platform"] == "DRONE"

    cctv_scens = manager.list_scenarios(platform="CCTV")
    assert len(cctv_scens) == 3
    for s in cctv_scens:
        assert s["platform"] == "CCTV"


def test_demo_manager_load_bytes():
    manager = DemoManager()
    img_bytes = manager.load_demo_image_bytes("Drone Traffic Observation")
    assert img_bytes is not None
    assert len(img_bytes) > 0


