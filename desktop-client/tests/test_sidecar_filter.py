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
