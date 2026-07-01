import os
import sys

ROOT = os.path.dirname(os.path.dirname(__file__))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from app import MillerPicDesktopApp


def test_appledouble_sidecar_is_ignored():
    assert MillerPicDesktopApp._is_ignored_sidecar_file("._IMG_0008.HEIC") is True
    assert MillerPicDesktopApp._is_ignored_sidecar_file("._img_0008.heic") is True


def test_os_junk_files_are_ignored():
    assert MillerPicDesktopApp._is_ignored_sidecar_file(".DS_Store") is True
    assert MillerPicDesktopApp._is_ignored_sidecar_file("Thumbs.db") is True
    assert MillerPicDesktopApp._is_ignored_sidecar_file("desktop.ini") is True


def test_real_photos_are_not_ignored():
    assert MillerPicDesktopApp._is_ignored_sidecar_file("IMG_0008.HEIC") is False
    assert MillerPicDesktopApp._is_ignored_sidecar_file("vacation.jpg") is False


def test_sync_image_filter_rejects_sidecar_but_accepts_real_photo():
    assert MillerPicDesktopApp._is_sync_image_file("._img_0008.heic") is False
    assert MillerPicDesktopApp._is_sync_image_file("IMG_0008.HEIC") is True


def test_sync_video_filter_rejects_sidecar():
    assert MillerPicDesktopApp._is_sync_video_file("._clip.mov") is False
    assert MillerPicDesktopApp._is_sync_video_file("clip.mov") is True


def test_format_size_is_human_readable():
    assert MillerPicDesktopApp._format_size(0) == "0 B"
    assert MillerPicDesktopApp._format_size(512) == "512 B"
    assert MillerPicDesktopApp._format_size(1024) == "1.0 KB"
    assert MillerPicDesktopApp._format_size(195000000) == "186.0 MB"
    assert MillerPicDesktopApp._format_size(5 * 1024 ** 3) == "5.0 GB"


def test_hamming_distance_counts_differing_bits():
    assert MillerPicDesktopApp._hamming_distance(0b1111, 0b1111) == 0
    assert MillerPicDesktopApp._hamming_distance(0b1111, 0b1010) == 2
    # Missing hashes are treated as maximally different.
    assert MillerPicDesktopApp._hamming_distance(None, 0b1) == 64
    assert MillerPicDesktopApp._hamming_distance(0b1, None) == 64


def test_assign_burst_groups_clusters_similar_and_splits_different():
    items = [
        {"phash": 0b0000, "modifiedEpoch": 1},
        {"phash": 0b0001, "modifiedEpoch": 2},  # 1 bit from prev -> same burst
        {"phash": 0xFFFF, "modifiedEpoch": 3},  # far from prev -> new burst
        {"phash": 0xFFFE, "modifiedEpoch": 4},  # 1 bit from prev -> same burst
    ]
    assert MillerPicDesktopApp._assign_burst_groups(items) == [0, 0, 1, 1]


def test_assign_burst_groups_breaks_chain_on_missing_hash():
    items = [
        {"phash": 0b0000, "modifiedEpoch": 1},
        {"phash": None, "modifiedEpoch": 2},  # unknown -> new group, breaks chain
        {"phash": 0b0000, "modifiedEpoch": 3},  # cannot chain through None
    ]
    assert MillerPicDesktopApp._assign_burst_groups(items) == [0, 1, 2]


def test_assign_burst_groups_orders_by_time():
    items = [
        {"phash": 0xFFFF, "modifiedEpoch": 10},
        {"phash": 0b0000, "modifiedEpoch": 1},
        {"phash": 0b0001, "modifiedEpoch": 2},
    ]
    # Sorted by time: (0b0000@1, 0b0001@2, 0xFFFF@10) -> groups 0,0,1 mapped back.
    assert MillerPicDesktopApp._assign_burst_groups(items) == [1, 0, 0]


def test_assign_burst_groups_handles_empty():
    assert MillerPicDesktopApp._assign_burst_groups([]) == []


def test_pictures_root_finds_pictures_ancestor():
    root = MillerPicDesktopApp._pictures_root(r"c:\users\adam\onedrive\pictures\AppleHill")
    assert os.path.basename(root).lower() == "pictures"
    assert root.lower().endswith(os.path.join("onedrive", "pictures"))


def test_pictures_root_falls_back_to_home_pictures():
    root = MillerPicDesktopApp._pictures_root(r"c:\some\random\folder")
    assert os.path.basename(root).lower() == "pictures"


def test_unique_destination_avoids_collisions(tmp_path):
    dest = str(tmp_path)
    first = MillerPicDesktopApp._unique_destination(dest, "IMG_1.jpg")
    assert first == os.path.join(dest, "IMG_1.jpg")
    # Create it, then the next call must not collide.
    open(first, "w").close()
    second = MillerPicDesktopApp._unique_destination(dest, "IMG_1.jpg")
    assert second == os.path.join(dest, "IMG_1 (1).jpg")



