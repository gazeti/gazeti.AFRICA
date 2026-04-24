import os


def _patch_archive_prefix():
    """Prepend ALEPH_ARCHIVE_PATH to S3 object keys if not already prefixed.

    Aleph 3.x servicelayer does not honour ALEPH_ARCHIVE_PATH when building
    S3 keys — this patch restores that behaviour so files stored under
    s3://<bucket>/aleph/<hash> are found correctly.
    """
    archive_type = os.environ.get("ALEPH_ARCHIVE_TYPE", "").strip().lower()
    archive_path = os.environ.get("ALEPH_ARCHIVE_PATH", "").strip().strip("/")
    if archive_type != "s3" or not archive_path:
        return
    try:
        from servicelayer.archive.archive import Archive
    except Exception:
        return
    original_get_prefix = getattr(Archive, "_get_prefix", None)
    if original_get_prefix is None or getattr(original_get_prefix, "_gazeti_patched", False):
        return

    def patched_get_prefix(self, content_hash):
        prefix = original_get_prefix(self, content_hash)
        if not prefix:
            return prefix
        if prefix == archive_path or prefix.startswith(archive_path + "/"):
            return prefix
        return os.path.join(archive_path, prefix)

    patched_get_prefix._gazeti_patched = True
    Archive._get_prefix = patched_get_prefix


_patch_archive_prefix()
