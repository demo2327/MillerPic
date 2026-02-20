import os
import sys

ROOT = os.path.dirname(os.path.dirname(__file__))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from thumbnail_hydration import build_thumbnail_candidates, cache_put_bounded, count_cached_rows, count_image_rows


def test_build_candidates_skips_non_images_and_cache_hits():
    photos = [
        {"photoId": "a", "contentType": "image/jpeg"},
        {"photoId": "b", "contentType": "video/mp4"},
        {"photoId": "c", "contentType": "image/png"},
        {"photoId": "d", "contentType": "image/webp"},
    ]
    cache = {"a": b"thumb-a"}

    candidates = build_thumbnail_candidates(photos, cache, max_attempts=10)

    assert [index for index, _ in candidates] == [2, 3]
    assert [photo.get("photoId") for _, photo in candidates] == ["c", "d"]


def test_build_candidates_honors_max_attempts():
    photos = [
        {"photoId": "a", "contentType": "image/jpeg"},
        {"photoId": "b", "contentType": "image/jpeg"},
        {"photoId": "c", "contentType": "image/jpeg"},
    ]

    candidates = build_thumbnail_candidates(photos, {}, max_attempts=2)

    assert len(candidates) == 2
    assert [photo.get("photoId") for _, photo in candidates] == ["a", "b"]


def test_count_helpers_reflect_image_and_cached_rows():
    photos = [
        {"photoId": "a", "contentType": "image/jpeg"},
        {"photoId": "b", "contentType": "video/mp4"},
        {"photoId": "c", "contentType": "image/png"},
        {"photoId": "", "contentType": "image/webp"},
    ]
    cache = {"a": b"1", "c": b"2", "missing": b"3"}

    assert count_image_rows(photos) == 3
    assert count_cached_rows(photos, cache) == 2


def test_cache_put_bounded_eviction_keeps_latest_items():
    cache = {}

    cache_put_bounded(cache, "a", b"1", max_items=2)
    cache_put_bounded(cache, "b", b"2", max_items=2)
    cache_put_bounded(cache, "c", b"3", max_items=2)

    assert list(cache.keys()) == ["b", "c"]


def test_cache_put_bounded_overwrite_does_not_drop_entry():
    cache = {"a": b"1"}

    cache_put_bounded(cache, "a", b"2", max_items=2)

    assert cache["a"] == b"2"
    assert len(cache) == 1
