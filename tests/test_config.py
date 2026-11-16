"""
Unit tests for ProxyShield Configuration Manager & Security
"""

import os
import tempfile
import stat
import pytest

from proxyshield.config_manager import (
    ensure_config_exists,
    check_permissions,
    enforce_permissions,
    load_config,
    get_identity,
    get_banner_config,
    get_colors_config,
    validate_config,
    reset_config,
    ConfigSecurityError,
)


def test_default_config_creation():
    with tempfile.TemporaryDirectory() as tmpdir:
        cfg_file = os.path.join(tmpdir, "branding.txt")
        assert not os.path.exists(cfg_file)
        created_path = ensure_config_exists(cfg_file)
        assert os.path.exists(created_path)

        config = load_config(created_path)
        identity = get_identity(config)
        assert identity["tool_name"] == "ProxyShield"
        assert identity["author"] == "Quarkova"
        assert identity["website"] == "https://quarkova.com"


def test_author_immutable_rule():
    with tempfile.TemporaryDirectory() as tmpdir:
        cfg_file = os.path.join(tmpdir, "branding.txt")
        with open(cfg_file, "w", encoding="utf-8") as f:
            f.write("[IDENTITY]\ntool_name=Fake\nauthor=SomeRandomName\n")
        config = load_config(cfg_file)
        identity = get_identity(config)
        # Author must strictly always be Quarkova
        assert identity["author"] == "Quarkova"


def test_config_validation():
    with tempfile.TemporaryDirectory() as tmpdir:
        cfg_file = os.path.join(tmpdir, "branding.txt")
        ensure_config_exists(cfg_file)

        is_valid, msgs = validate_config(cfg_file)
        assert is_valid is True

        # Write invalid config
        with open(cfg_file, "w", encoding="utf-8") as f:
            f.write("[BANNER]\nalignment = unknown_align\n")
        is_valid_inv, msgs_inv = validate_config(cfg_file)
        assert any("alignment" in m for m in msgs_inv)


def test_config_reset():
    with tempfile.TemporaryDirectory() as tmpdir:
        cfg_file = os.path.join(tmpdir, "branding.txt")
        with open(cfg_file, "w", encoding="utf-8") as f:
            f.write("[IDENTITY]\ncustom = modified\n")

        ok, msg = reset_config(cfg_file, force=True)
        assert ok is True
        config = load_config(cfg_file)
        assert "BANNER" in config
        assert get_identity(config)["tool_name"] == "ProxyShield"


@pytest.mark.skipif(os.name == "nt", reason="POSIX permissions tests")
def test_posix_permissions_security():
    with tempfile.TemporaryDirectory() as tmpdir:
        cfg_file = os.path.join(tmpdir, "branding.txt")
        ensure_config_exists(cfg_file)

        # Enforce 600
        ok, msg = enforce_permissions(cfg_file)
        assert ok is True

        # Check permissions
        ok_perm, perm_msg = check_permissions(cfg_file)
        assert ok_perm is True

        # Make world writable
        os.chmod(cfg_file, 0o777)
        ok_insecure, warn_msg = check_permissions(cfg_file)
        assert ok_insecure is False
        assert "world-writable" in warn_msg

        # Loading should raise ConfigSecurityError
        with pytest.raises(ConfigSecurityError):
            load_config(cfg_file)

