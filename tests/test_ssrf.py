import pytest

from page_ready.ssrf import UnsafeURLError, assert_public_http_url


def test_rejects_non_http():
    with pytest.raises(UnsafeURLError):
        assert_public_http_url("file:///etc/passwd")


def test_rejects_localhost():
    with pytest.raises(UnsafeURLError):
        assert_public_http_url("http://localhost/admin")


def test_rejects_metadata_host():
    with pytest.raises(UnsafeURLError):
        assert_public_http_url("http://metadata.google.internal/")


def test_allows_example():
    assert assert_public_http_url("https://example.com/path") == "https://example.com/path"
