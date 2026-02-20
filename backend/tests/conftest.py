import os
import pytest

# Set AWS credentials and region before any boto3 imports happen
os.environ.setdefault("AWS_DEFAULT_REGION", "us-east-1")
os.environ.setdefault("AWS_ACCESS_KEY_ID", "testing")
os.environ.setdefault("AWS_SECRET_ACCESS_KEY", "testing")
os.environ.setdefault("AWS_SECURITY_TOKEN", "testing")
os.environ.setdefault("AWS_SESSION_TOKEN", "testing")

# Set application environment variables
os.environ.setdefault("PHOTOS_TABLE", "photos-test")
os.environ.setdefault("PHOTO_BUCKET", "photos-test-bucket")
os.environ.setdefault("ALBUMS_TABLE", "albums-test")
