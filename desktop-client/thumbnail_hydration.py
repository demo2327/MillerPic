LIST_THUMBNAIL_MAX_ATTEMPTS = 24


def is_image_content_type(content_type):
    return str(content_type or "").lower().startswith("image/")


def build_thumbnail_candidates(photos, bytes_cache, max_attempts=LIST_THUMBNAIL_MAX_ATTEMPTS):
    candidates = []
    cache = bytes_cache or {}

    for index, photo in enumerate(photos or []):
        if not is_image_content_type(photo.get("contentType")):
            continue

        photo_id = photo.get("photoId")
        if photo_id and photo_id in cache:
            continue

        candidates.append((index, photo))
        if len(candidates) >= max_attempts:
            break

    return candidates


def count_image_rows(photos):
    return sum(1 for photo in (photos or []) if is_image_content_type(photo.get("contentType")))


def count_cached_rows(photos, bytes_cache):
    cache = bytes_cache or {}
    count = 0
    for photo in photos or []:
        photo_id = photo.get("photoId")
        if photo_id and photo_id in cache:
            count += 1
    return count
