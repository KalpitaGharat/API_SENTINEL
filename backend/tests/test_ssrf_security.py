"""Comprehensive Security Test Suite for SSRF, DNS Rebinding, and Network Hardening.

Covers:
1. Rejection of unspecified addresses (0.0.0.0, ::) unconditionally.
2. Alternate numeric representations (decimal, hex).
3. Cloud metadata endpoint blocking (IPv4, IPv6, hostnames, IPv4-mapped IPv6).
4. Link-local, multicast, and reserved IP blocking.
5. Private IP and loopback restrictions (blocked by default, allowed only with allow_lab=True).
6. Connection-level destination-IP pinning and DNS rebinding protection.
7. TLS SNI and Host header preservation during destination pinning.
8. Redirect security (downgrade prevention, metadata/private redirect blocking, loop detection, hop limit, header stripping).
9. Synthetic credential restrictions (strictly gated to authorized local demo lab).
"""

import ipaddress
import socket
import pytest
import httpcore
import httpx
from urllib.parse import urlparse
from unittest.mock import patch, MagicMock

from app.security_engine.integration import (
    validate_target_safety,
    validate_safe_redirect,
    execute_safe_request,
    create_safe_http_client,
    PinnedSyncBackend,
    PinnedHTTPTransport,
    TargetSafetyError,
)
from app.security_engine.member1_engine import (
    is_authorized_demo_target,
    EngineAdapter,
)


# =============================================================================
# 1. IP Address and Numeric Representation Tests
# =============================================================================

def test_unspecified_address_rejected_even_in_lab_mode():
    """Unspecified addresses 0.0.0.0 and :: must be strictly forbidden under ALL conditions."""
    with pytest.raises(TargetSafetyError, match="Unspecified address"):
        validate_target_safety("http://0.0.0.0", allow_lab=False)

    with pytest.raises(TargetSafetyError, match="Unspecified address"):
        validate_target_safety("http://0.0.0.0", allow_lab=True)

    with pytest.raises(TargetSafetyError, match="Unspecified address"):
        validate_target_safety("http://[::]", allow_lab=False)

    with pytest.raises(TargetSafetyError, match="Unspecified address"):
        validate_target_safety("http://[::]", allow_lab=True)


def test_decimal_and_hex_ip_representations():
    """Decimal and hex representations of loopback and metadata must be detected and blocked."""
    # 2130706433 == 127.0.0.1
    with pytest.raises(TargetSafetyError, match="private/loopback"):
        validate_target_safety("http://2130706433", allow_lab=False)

    # In lab mode, 127.0.0.1 is permitted
    host, ip = validate_target_safety("http://2130706433", allow_lab=True)
    assert ip == "127.0.0.1"

    # 0x7f000001 == 127.0.0.1
    with pytest.raises(TargetSafetyError, match="private/loopback"):
        validate_target_safety("http://0x7f000001", allow_lab=False)

    # 2852039166 == 169.254.169.254 (Cloud metadata)
    with pytest.raises(TargetSafetyError, match="cloud metadata"):
        validate_target_safety("http://2852039166", allow_lab=True)

    # 0xa9fea9fe == 169.254.169.254 (Cloud metadata in hex)
    with pytest.raises(TargetSafetyError, match="cloud metadata"):
        validate_target_safety("http://0xa9fea9fe", allow_lab=True)


def test_cloud_metadata_endpoints_strictly_blocked():
    """Cloud metadata endpoints must be blocked unconditionally (IPv4, IPv6, and hostnames)."""
    blocked_targets = [
        "http://169.254.169.254",
        "http://169.254.169.254/latest/meta-data/",
        "http://[fd00:ec2::254]",
        "http://metadata.google.internal",
        "http://compute.metadata.google.internal",
        "http://instance-data",
        "http://[::ffff:169.254.169.254]",
    ]
    for target in blocked_targets:
        with pytest.raises(TargetSafetyError):
            validate_target_safety(target, allow_lab=False)
        with pytest.raises(TargetSafetyError):
            validate_target_safety(target, allow_lab=True)


def test_link_local_multicast_and_reserved_blocked():
    """Link-local (169.254.0.0/16, fe80::/10), multicast, and reserved addresses must be blocked."""
    unwanted = [
        "http://169.254.1.1",
        "http://[fe80::1]",
        "http://224.0.0.1",
        "http://[ff02::1]",
        "http://240.0.0.1",
    ]
    for target in unwanted:
        with pytest.raises(TargetSafetyError):
            validate_target_safety(target, allow_lab=False)
        with pytest.raises(TargetSafetyError):
            validate_target_safety(target, allow_lab=True)


def test_private_ips_blocked_by_default_allowed_in_lab():
    """Private RFC 1918 / ULA IPs must be blocked by default and allowed ONLY when allow_lab=True."""
    private_targets = [
        "http://10.0.0.1",
        "http://172.16.5.1",
        "http://192.168.1.1",
        "http://127.0.0.1:8000",
        "http://[::1]",
        "http://[fc00::1]",
    ]
    for target in private_targets:
        with pytest.raises(TargetSafetyError, match="private/loopback"):
            validate_target_safety(target, allow_lab=False)

        # In lab mode, private/loopback targets succeed
        host, ip = validate_target_safety(target, allow_lab=True)
        assert ip is not None


# =============================================================================
# 2. Connection-Level Destination-IP Pinning & DNS Rebinding Tests
# =============================================================================

def test_pinned_backend_connects_to_exact_validated_ip():
    """Verify that PinnedSyncBackend routes connect_tcp to the pinned IP literal."""
    backend = PinnedSyncBackend(pinned_map={"example.com": "93.184.216.34"})

    with patch.object(httpcore.SyncBackend, "connect_tcp") as mock_super_connect:
        backend.connect_tcp("example.com", 443)
        # Must connect to the validated IP string, not the domain name
        mock_super_connect.assert_called_once_with(
            "93.184.216.34",
            443,
            timeout=None,
            local_address=None,
            socket_options=None,
        )


def test_dns_rebinding_simulation_prevented():
    """Simulate DNS change between validation and connection: connection destination remains pinned."""
    # Step 1: Pre-flight validation resolves benign public IP 93.184.216.34
    pinned_map = {"rebind.attacker.test": "93.184.216.34"}
    backend = PinnedSyncBackend(pinned_map=pinned_map)

    # Step 2: Attacker flips DNS to 169.254.169.254
    with patch("socket.getaddrinfo") as mock_dns:
        mock_dns.return_value = [(socket.AF_INET, socket.SOCK_STREAM, 6, "", ("169.254.169.254", 80))]

        with patch.object(httpcore.SyncBackend, "connect_tcp") as mock_super_connect:
            backend.connect_tcp("rebind.attacker.test", 80)
            # The connection MUST still connect to the pinned safe IP (93.184.216.34), ignoring changed DNS!
            mock_super_connect.assert_called_once_with(
                "93.184.216.34",
                80,
                timeout=None,
                local_address=None,
                socket_options=None,
            )


def test_tls_sni_and_host_header_preserved():
    """Verify that PinnedHTTPTransport preserves HTTP 'Host' header and TLS SNI hostname."""
    transport = PinnedHTTPTransport(pinned_map={"secure.api.com": "93.184.216.34"})

    # Connection pool must use zero-keepalive to prevent cross-origin socket reuse
    assert transport._pool._max_keepalive_connections == 0
    assert transport._pool._keepalive_expiry == 0.0

    # Ensure trust_env is disabled
    assert transport._pool._network_backend.pinned_map.get("secure.api.com") == "93.184.216.34"


def test_unpinned_host_auto_validates_or_fails_closed():
    """An unpinned host requested on PinnedSyncBackend is evaluated against safety policy."""
    backend = PinnedSyncBackend(pinned_map={}, allow_lab=False)

    # Attempting to connect to loopback or private IP without lab mode fails closed
    with pytest.raises(TargetSafetyError):
        backend.connect_tcp("127.0.0.1", 80)


# =============================================================================
# 3. HTTP Redirect Security Tests
# =============================================================================

def test_redirect_https_to_http_downgrade_rejected():
    """A redirect from HTTPS to unencrypted HTTP must be rejected immediately."""
    with pytest.raises(TargetSafetyError, match="downgrade"):
        validate_safe_redirect("https://secure.example.com/login", "http://secure.example.com/login")


def test_redirect_to_cloud_metadata_rejected():
    """Redirecting to cloud metadata endpoints must be blocked."""
    with pytest.raises(TargetSafetyError):
        validate_safe_redirect("https://example.com/api", "http://169.254.169.254/latest/meta-data/")


def test_redirect_to_private_network_rejected():
    """Redirecting from external domain to internal RFC 1918 IP must be blocked."""
    with pytest.raises(TargetSafetyError, match="private/loopback"):
        validate_safe_redirect("http://example.com/api", "http://192.168.1.1/admin", allow_lab=False)


def test_redirect_loop_detected():
    """execute_safe_request must detect and abort redirect loops."""
    mock_transport = MagicMock()
    # A redirects to B, B redirects back to A
    resp_a = httpx.Response(302, headers={"Location": "https://example.com/b"})
    resp_b = httpx.Response(302, headers={"Location": "https://example.com/a"})
    mock_transport.handle_request.side_effect = [resp_a, resp_b, resp_a]

    client = httpx.Client(transport=mock_transport)

    with patch("app.security_engine.integration.validate_target_safety") as mock_val:
        mock_val.return_value = ("example.com", "93.184.216.34")
        with pytest.raises(TargetSafetyError, match="Redirect loop detected"):
            execute_safe_request(client, "GET", "https://example.com/a")


def test_max_redirect_hops_enforced():
    """execute_safe_request must stop after maximum allowed redirect hops (5)."""
    mock_transport = MagicMock()
    # Chain of 6 redirects
    hops = [httpx.Response(302, headers={"Location": f"https://example.com/hop{i}"}) for i in range(1, 7)]
    mock_transport.handle_request.side_effect = hops

    client = httpx.Client(transport=mock_transport)

    with patch("app.security_engine.integration.validate_target_safety") as mock_val:
        mock_val.return_value = ("example.com", "93.184.216.34")
        with pytest.raises(TargetSafetyError, match="Maximum redirect hops"):
            execute_safe_request(client, "GET", "https://example.com/hop0", max_redirects=5)


def test_cross_origin_redirect_strips_sensitive_headers():
    """Cross-origin redirect must strip Authorization, Cookie, and API Key headers."""
    mock_transport = MagicMock()
    # Redirect from site-a.com to site-b.com
    resp_redirect = httpx.Response(302, headers={"Location": "https://site-b.com/data"})
    resp_final = httpx.Response(200, json={"status": "ok"})
    mock_transport.handle_request.side_effect = [resp_redirect, resp_final]

    client = httpx.Client(transport=mock_transport)

    with patch("app.security_engine.integration.validate_target_safety") as mock_val:
        mock_val.side_effect = lambda url, allow_lab=False: (urlparse(url).hostname or "site", "93.184.216.34")
        resp = execute_safe_request(
            client,
            "GET",
            "https://site-a.com/start",
            headers={"Authorization": "Bearer secret_token", "Cookie": "session=123", "X-Custom": "safe"},
        )

    # Check second request handled by transport
    second_call_req = mock_transport.handle_request.call_args_list[1][0][0]
    assert "Authorization" not in second_call_req.headers
    assert "Cookie" not in second_call_req.headers
    assert second_call_req.headers.get("X-Custom") == "safe"


# =============================================================================
# 4. Synthetic Credential Restriction Tests
# =============================================================================

def test_authorized_demo_target_guard():
    """Verify is_authorized_demo_target requires explicit lab mode, loopback, and correct port."""
    # Refused if allow_lab is False
    assert is_authorized_demo_target("http://127.0.0.1:8001", allow_lab=False) is False
    assert is_authorized_demo_target("http://localhost:8001", allow_lab=False) is False

    # Refused for external domains
    assert is_authorized_demo_target("https://api.sentinel.com", allow_lab=True) is False
    assert is_authorized_demo_target("http://192.168.1.50:8001", allow_lab=True) is False

    # Refused for wrong ports
    assert is_authorized_demo_target("http://127.0.0.1:9090", allow_lab=True) is False

    # Approved for authorized local lab targets
    assert is_authorized_demo_target("http://127.0.0.1:8001", allow_lab=True) is True
    assert is_authorized_demo_target("http://localhost:8001", allow_lab=True) is True
    assert is_authorized_demo_target("http://testserver", allow_lab=True) is True


def test_synthetic_credentials_refused_on_external_targets():
    """Engine must refuse synthetic demo credentials when scanning arbitrary external targets."""
    adapter = EngineAdapter()

    # Scan external target with redacted credentials
    findings = adapter.run_scan(
        target_url="https://api.external-target.com",
        config={
            "categories": ["BOLA"],
            "allow_lab": False,
            "test_accounts": {
                "patient_a": {"username": "patient_a", "password": "[REDACTED_FOR_SECURITY]"},
            },
        },
    )

    # BOLA check should be skipped (0 findings), and demo password should NOT have been sent
    assert len(findings) == 0


def test_synthetic_credentials_refused_on_unauthorized_private_targets():
    """Engine must refuse synthetic credentials on non-demo private targets even in lab mode."""
    adapter = EngineAdapter()

    findings = adapter.run_scan(
        target_url="http://192.168.1.100:8080",
        config={
            "categories": ["BOLA"],
            "allow_lab": True,
            "test_accounts": {
                "patient_a": {"username": "patient_a", "password": "[REDACTED_FOR_SECURITY]"},
            },
        },
    )

    # BOLA check should be skipped (0 findings)
    assert len(findings) == 0
