"""Security Testing Engine Integration Layer.

This module acts as the bridge between the API Sentinel backend
and Member 1's security testing engine.

Features:
- Standardized findings interface and schema validation.
- Target URL security safeguards (SSRF & private IP restrictions).
- Pluggable architecture allowing seamless swap when Member 1's real
  engine is dropped into the project.
- Isolated Mock Adapter for local testing and CI/CD verification with
  clear labeling of simulated vs real results.
"""

import ipaddress
import logging
import socket
import ssl
from typing import Any, Dict, List, Optional, Set, Tuple
from urllib.parse import urlparse, urljoin
import httpcore
import httpx
from httpx._config import create_ssl_context

from app.config import settings
from app.schemas import FindingCreate, EvidenceCreate

logger = logging.getLogger(__name__)


class TargetSafetyError(ValueError):
    """Raised when target URL violates security safety policies (e.g. SSRF)."""
    pass


def _parse_ip_literal(host: str) -> Optional[ipaddress.IPv4Address | ipaddress.IPv6Address]:
    """Detect standard, decimal, and hexadecimal IP representations."""
    clean = host.strip("[]")

    # 1. Standard dotted-decimal or IPv6 literal
    try:
        return ipaddress.ip_address(clean)
    except ValueError:
        pass

    # 2. Decimal integer IP representation (e.g. 2130706433 -> 127.0.0.1)
    if clean.isdigit():
        try:
            val = int(clean)
            if 0 <= val <= 0xFFFFFFFF:
                return ipaddress.IPv4Address(val)
        except ValueError:
            pass

    # 3. Hexadecimal integer IP representation (e.g. 0x7f000001 -> 127.0.0.1)
    if clean.lower().startswith("0x"):
        try:
            val = int(clean, 16)
            if 0 <= val <= 0xFFFFFFFF:
                return ipaddress.IPv4Address(val)
        except ValueError:
            pass

    return None


def _check_ip_safety(ip_obj: ipaddress.IPv4Address | ipaddress.IPv6Address, allow_lab: bool = False) -> None:
    """Examine a single IP address against SSRF policies.

    Enforces unconditional rejection of:
    - Unspecified addresses (0.0.0.0, ::)
    - Cloud metadata endpoints (169.254.169.254, fd00:ec2::254)
    - Link-local addresses (169.254.0.0/16, fe80::/10)
    - Multicast addresses (224.0.0.0/4, ff00::/8)
    - Reserved addresses (e.g. 240.0.0.0/4)
    - IPv4-mapped IPv6 ranges
    """
    cloud_metadata_v4 = ipaddress.ip_address("169.254.169.254")
    cloud_metadata_v6 = ipaddress.ip_address("fd00:ec2::254")

    inspected_ips = [ip_obj]
    if isinstance(ip_obj, ipaddress.IPv6Address) and ip_obj.ipv4_mapped:
        inspected_ips.append(ip_obj.ipv4_mapped)

    for ip in inspected_ips:
        # 1. Unspecified address (0.0.0.0, ::) - STRICTLY BLOCKED ALWAYS (even in lab mode)
        if ip.is_unspecified:
            raise TargetSafetyError(
                f"Unspecified address '{ip}' is strictly forbidden by security policy."
            )

        # 2. Cloud metadata endpoints - STRICTLY BLOCKED ALWAYS (even in lab mode)
        if ip in (cloud_metadata_v4, cloud_metadata_v6):
            raise TargetSafetyError("Requests resolving to cloud metadata IPs are strictly forbidden.")

        # 3. Link-local addresses (169.254.0.0/16, fe80::/10) - STRICTLY BLOCKED ALWAYS
        if ip.is_link_local:
            raise TargetSafetyError(
                f"Scanning link-local address '{ip}' is strictly forbidden by security policy."
            )

        # 4. Multicast addresses - STRICTLY BLOCKED ALWAYS
        if ip.is_multicast:
            raise TargetSafetyError(
                f"Scanning multicast address '{ip}' is strictly forbidden by security policy."
            )

        # 5. Reserved addresses (excluding standard loopback) - STRICTLY BLOCKED ALWAYS
        if ip.is_reserved and not ip.is_loopback:
            raise TargetSafetyError(
                f"Scanning reserved address '{ip}' is strictly forbidden by security policy."
            )

        # 6. Private (RFC 1918 / ULA) and Loopback (127.0.0.0/8, ::1)
        # Blocked unless allow_lab=True
        if (ip.is_private or ip.is_loopback) and not allow_lab:
            raise TargetSafetyError(
                f"Scanning private/loopback address '{ip}' is blocked by safety policy. "
                "Enable ALLOW_LOCAL_LAB_SCANNING only in controlled lab testing environments."
            )


def validate_target_safety(target_url: str, allow_lab: bool = False) -> Tuple[str, str]:
    """Validate target URL against SSRF, DNS rebinding, loopback, link-local, and cloud metadata attacks.

    Supports both IPv4 and IPv6 resolution, checks all A and AAAA records,
    inspects IPv4-mapped IPv6 ranges, checks decimal/hex alternative notations,
    and enforces strict cloud metadata and unspecified address blocking.

    Args:
        target_url: URL to validate.
        allow_lab: If True, permits localhost/private RFC 1918 IPs for controlled hackathon lab testing.
                   Cloud metadata, unspecified (0.0.0.0/::), and link-local addresses remain strictly blocked.

    Returns:
        Tuple[str, str]: (normalized_hostname, primary_validated_ip)
    """
    parsed = urlparse(target_url)
    if parsed.scheme not in ("http", "https"):
        raise TargetSafetyError(f"Unsupported URL scheme: {parsed.scheme}. Only HTTP/HTTPS permitted.")

    hostname = parsed.hostname
    if not hostname:
        raise TargetSafetyError("Target URL does not contain a valid hostname.")

    hostname_clean = hostname.lower().strip("[]")

    # Cloud metadata hostnames - strictly forbidden under ALL conditions (even lab mode)
    forbidden_metadata_hosts = {
        "169.254.169.254",
        "metadata.google.internal",
        "instance-data",
        "fd00:ec2::254",
    }
    if hostname_clean in forbidden_metadata_hosts or hostname_clean.endswith(".metadata.google.internal"):
        raise TargetSafetyError("Requests to cloud metadata endpoints are strictly forbidden.")

    # 1. Direct IP or numeric literal validation
    direct_ip = _parse_ip_literal(hostname_clean)
    if direct_ip is not None:
        _check_ip_safety(direct_ip, allow_lab=allow_lab)
        return hostname_clean, str(direct_ip)

    # 2. Dual-stack DNS Resolution (IPv4 A and IPv6 AAAA)
    try:
        addr_info = socket.getaddrinfo(hostname_clean, None, proto=socket.IPPROTO_TCP)
    except socket.gaierror:
        # Offline fallback for simulated/mock targets in authorized lab mode
        if allow_lab:
            return hostname_clean, "127.0.0.1"
        raise TargetSafetyError(f"Unable to resolve hostname '{hostname}'.")

    if not addr_info:
        raise TargetSafetyError(f"No address records found for hostname '{hostname}'.")

    primary_ip: Optional[str] = None
    for family, _, _, _, sockaddr in addr_info:
        raw_ip = sockaddr[0]
        try:
            ip_obj = ipaddress.ip_address(raw_ip)
        except ValueError:
            raise TargetSafetyError(f"Target resolved to an invalid IP address '{raw_ip}'.")

        _check_ip_safety(ip_obj, allow_lab=allow_lab)

        if primary_ip is None:
            primary_ip = str(ip_obj)

    return hostname_clean, primary_ip or "127.0.0.1"


def validate_safe_redirect(initial_url: str, redirect_target: str, allow_lab: bool = False) -> str:
    """Validate HTTP redirect target against SSRF and protocol downgrades before an HTTP client follows it."""
    absolute_target = urljoin(initial_url, redirect_target)

    init_parsed = urlparse(initial_url)
    target_parsed = urlparse(absolute_target)

    # Reject HTTPS -> HTTP protocol downgrade
    if init_parsed.scheme == "https" and target_parsed.scheme == "http":
        raise TargetSafetyError(
            f"Protocol downgrade from HTTPS ({initial_url}) to HTTP ({absolute_target}) is forbidden."
        )

    validate_target_safety(absolute_target, allow_lab=allow_lab)
    return absolute_target


class PinnedSyncBackend(httpcore.SyncBackend):
    """Custom httpcore NetworkBackend guaranteeing connection-level destination-IP pinning.

    Eliminates Time-of-Check to Time-of-Use (TOCTOU) DNS rebinding vulnerabilities:
    1. Connects the raw TCP socket directly to the pre-validated IP address.
    2. Preserves the original hostname for HTTP 'Host' header and TLS SNI.
    3. Retains full TLS certificate hostname verification.
    4. Rejects connections to any unvalidated destination.
    """

    def __init__(self, pinned_map: Optional[Dict[str, str]] = None, allow_lab: bool = False):
        super().__init__()
        self.pinned_map: Dict[str, str] = {k.lower().strip("[]"): v for k, v in (pinned_map or {}).items()}
        self.allow_lab = allow_lab

    def pin_host(self, host: str, ip: str) -> None:
        """Explicitly register a validated IP for a target host."""
        self.pinned_map[host.lower().strip("[]")] = ip

    def connect_tcp(
        self,
        host: str,
        port: int,
        timeout: Optional[float] = None,
        local_address: Optional[str] = None,
        socket_options: Optional[Any] = None,
    ) -> httpcore.NetworkStream:
        clean_host = host.lower().strip("[]")

        # Resolve and validate host destination
        if clean_host in self.pinned_map:
            target_ip = self.pinned_map[clean_host]
        else:
            _, target_ip = validate_target_safety(f"http://{clean_host}:{port}", allow_lab=self.allow_lab)
            self.pinned_map[clean_host] = target_ip

        logger.debug("[PinnedSyncBackend] Direct TCP connection to %s:%d (pinned for host '%s')", target_ip, port, host)
        return super().connect_tcp(
            target_ip,
            port,
            timeout=timeout,
            local_address=local_address,
            socket_options=socket_options,
        )


class PinnedHTTPTransport(httpx.HTTPTransport):
    """Custom HTTPX Transport with enforced destination-IP pinning and zero-keepalive pooling.

    Ensures that socket connections cannot be redirected via DNS rebinding and
    connection pooling cannot reuse sockets for different validated destinations.
    """

    def __init__(
        self,
        pinned_map: Optional[Dict[str, str]] = None,
        allow_lab: bool = False,
        verify: Any = True,
        cert: Any = None,
        http1: bool = True,
        http2: bool = False,
        retries: int = 0,
        **kwargs,
    ):
        super().__init__(
            verify=verify,
            cert=cert,
            trust_env=False,  # Disable untrusted environment proxy behavior by default
            http1=http1,
            http2=http2,
            retries=retries,
            **kwargs,
        )
        self.allow_lab = allow_lab
        self.pinned_backend = PinnedSyncBackend(pinned_map=pinned_map, allow_lab=allow_lab)

        ssl_context = create_ssl_context(verify=verify, cert=cert, trust_env=False)
        self._pool = httpcore.ConnectionPool(
            ssl_context=ssl_context,
            max_connections=10,
            max_keepalive_connections=0,  # Zero keepalive pooling prevents reusing sockets across destinations
            keepalive_expiry=0.0,
            http1=http1,
            http2=http2,
            retries=retries,
            network_backend=self.pinned_backend,
        )

    def pin_target_url(self, target_url: str, allow_lab: Optional[bool] = None) -> None:
        """Register the validated IP for a target URL into the pinned backend."""
        lab = self.allow_lab if allow_lab is None else allow_lab
        host, ip = validate_target_safety(target_url, allow_lab=lab)
        self.pinned_backend.pin_host(host, ip)


def execute_safe_request(
    client: httpx.Client,
    method: str,
    url: str,
    *,
    allow_lab: bool = False,
    max_redirects: int = 5,
    headers: Optional[Dict[str, str]] = None,
    json_body: Any = None,
    **kwargs,
) -> httpx.Response:
    """Execute HTTP request with strict per-hop SSRF validation, loop detection, and credential stripping."""
    current_url = url
    current_headers = dict(headers or {})
    visited_urls: Set[str] = set()

    for hop in range(max_redirects + 1):
        if current_url in visited_urls:
            raise TargetSafetyError(f"Redirect loop detected at '{current_url}'.")
        visited_urls.add(current_url)

        # Validate current hop destination
        validate_target_safety(current_url, allow_lab=allow_lab)

        # Pin host if transport supports it
        transport = getattr(client, "_transport", None)
        if isinstance(transport, PinnedHTTPTransport):
            transport.pin_target_url(current_url, allow_lab=allow_lab)

        resp = client.request(
            method=method,
            url=current_url,
            headers=current_headers,
            json=json_body,
            **kwargs,
        )

        # Check for HTTP redirect response
        if resp.status_code in (301, 302, 303, 307, 308):
            location = resp.headers.get("Location")
            if not location:
                return resp

            if hop >= max_redirects:
                raise TargetSafetyError(f"Maximum redirect hops ({max_redirects}) exceeded.")

            next_url = validate_safe_redirect(current_url, location, allow_lab=allow_lab)

            # Cross-origin credential stripping
            curr_p = urlparse(current_url)
            next_p = urlparse(next_url)
            if (curr_p.scheme, curr_p.hostname, curr_p.port) != (next_p.scheme, next_p.hostname, next_p.port):
                current_headers.pop("Authorization", None)
                current_headers.pop("authorization", None)
                current_headers.pop("Cookie", None)
                current_headers.pop("cookie", None)
                current_headers.pop("X-API-Key", None)
                current_headers.pop("x-api-key", None)

            # Change method to GET for 301/302/303 according to standard HTTP redirection semantics
            if resp.status_code in (301, 302, 303) and method != "HEAD":
                method = "GET"
                json_body = None

            current_url = next_url
        else:
            return resp

    return resp


class BaseSecurityEngineAdapter:
    """Abstract interface defining the contract with Member 1's testing engine."""

    engine_name: str = "base_engine"
    is_simulated: bool = False

    def run_scan(self, target_url: str, config: Dict[str, Any]) -> List[FindingCreate]:
        """Execute full suite of security checks against target API."""
        raise NotImplementedError("Subclasses must implement run_scan")

    def retest_finding(
        self,
        target_url: str,
        finding_data: Dict[str, Any],
        config: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Re-execute a specific security check to verify remediation."""
        raise NotImplementedError("Subclasses must implement retest_finding")


class MockSecurityEngineAdapter(BaseSecurityEngineAdapter):
    """Simulated testing adapter used for local development before Member 1's engine is connected.

    NOTE: All findings and retest outputs are explicitly branded with '[SIMULATED MOCK]'
    to prevent simulated test data from ever being confused with real security discoveries.
    """
    engine_name = "mock_adapter"
    is_simulated = True

    def run_scan(self, target_url: str, config: Dict[str, Any]) -> List[FindingCreate]:
        logger.info("[MockEngine] Executing simulated security scan against: %s", target_url)
        categories = config.get("categories", ["BOLA", "AUTH", "HEADERS", "CONFIG"])
        findings: List[FindingCreate] = []

        # 1. BOLA / IDOR Check
        if "BOLA" in categories:
            findings.append(
                FindingCreate(
                    vulnerability="[SIMULATED MOCK] Broken Object Level Authorization (BOLA/IDOR)",
                    category="BOLA",
                    endpoint="GET /api/patients/{id}",
                    severity="High",
                    description=(
                        "[SIMULATED MOCK FINDING - DEVELOPER HARNESS ONLY] Endpoint accepts arbitrary patient identifiers "
                        "without verifying that the authenticated user has legitimate ownership or permission."
                    ),
                    recommendation=(
                        "[SIMULATED REMEDIATION] Enforce strict server-side authorization checks comparing user_id "
                        "from token claims against resource owner."
                    ),
                    status="Open",
                    evidence=EvidenceCreate(
                        test_user="Patient_A (Token A)",
                        requested_resource="/api/patients/patient_b_9921",
                        observed_status=200,
                        expected_status=403,
                        request_details={
                            "simulation_notice": "GENERATED BY MOCK ENGINE - SIMULATED TELEMETRY",
                            "method": "GET",
                            "url": f"{target_url.rstrip('/')}/api/patients/patient_b_9921",
                            "auth": "Bearer [REDACTED_TOKEN_A]",
                        },
                        response_details={
                            "simulation_notice": "GENERATED BY MOCK ENGINE - SIMULATED TELEMETRY",
                            "status_code": 200,
                            "data_returned": {
                                "patient_id": "patient_b_9921",
                                "name": "Alice Bob",
                                "ssn": "***-**-1234",
                            },
                        },
                    ),
                )
            )

        # 2. Missing Security Headers
        if "HEADERS" in categories:
            findings.append(
                FindingCreate(
                    vulnerability="[SIMULATED MOCK] Missing Crucial HTTP Security Headers",
                    category="HEADERS",
                    endpoint="GET /api/v1/status",
                    severity="Medium",
                    description=(
                        "[SIMULATED MOCK FINDING - DEVELOPER HARNESS ONLY] Response headers lack X-Content-Type-Options, "
                        "Strict-Transport-Security (HSTS), and Content-Security-Policy."
                    ),
                    recommendation=(
                        "[SIMULATED REMEDIATION] Configure middleware to include security headers: "
                        "X-Content-Type-Options: nosniff, HSTS, and X-Frame-Options: DENY."
                    ),
                    status="Open",
                    evidence=EvidenceCreate(
                        test_user="Anonymous",
                        requested_resource="/api/v1/status",
                        observed_status=200,
                        expected_status=200,
                        request_details={
                            "simulation_notice": "GENERATED BY MOCK ENGINE - SIMULATED TELEMETRY",
                            "method": "GET",
                            "url": f"{target_url.rstrip('/')}/api/v1/status",
                        },
                        response_details={
                            "simulation_notice": "GENERATED BY MOCK ENGINE - SIMULATED TELEMETRY",
                            "missing_headers": [
                                "Strict-Transport-Security",
                                "X-Content-Type-Options",
                                "X-Frame-Options",
                            ],
                        },
                    ),
                )
            )

        # 3. Authentication Weakness
        if "AUTH" in categories:
            findings.append(
                FindingCreate(
                    vulnerability="[SIMULATED MOCK] Unauthenticated Sensitive Endpoint Access",
                    category="AUTH",
                    endpoint="GET /api/admin/metrics",
                    severity="Critical",
                    description=(
                        "[SIMULATED MOCK FINDING - DEVELOPER HARNESS ONLY] Administrative metrics endpoint does not enforce "
                        "authentication or role verification, exposing internal service metrics to unauthenticated users."
                    ),
                    recommendation=(
                        "[SIMULATED REMEDIATION] Require valid administrative JWT and enforce role-based access control (RBAC)."
                    ),
                    status="Open",
                    evidence=EvidenceCreate(
                        test_user="Unauthenticated",
                        requested_resource="/api/admin/metrics",
                        observed_status=200,
                        expected_status=401,
                        request_details={
                            "simulation_notice": "GENERATED BY MOCK ENGINE - SIMULATED TELEMETRY",
                            "method": "GET",
                            "url": f"{target_url.rstrip('/')}/api/admin/metrics",
                        },
                        response_details={
                            "simulation_notice": "GENERATED BY MOCK ENGINE - SIMULATED TELEMETRY",
                            "status_code": 200,
                            "leaked_metrics": "cpu, memory, active_sessions",
                        },
                    ),
                )
            )

        return findings

    def retest_finding(
        self,
        target_url: str,
        finding_data: Dict[str, Any],
        config: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Simulate re-executing a check against an endpoint with explicit mock branding."""
        logger.info("[MockEngine] Retesting finding %s on %s", finding_data.get("id"), target_url)
        endpoint = finding_data.get("endpoint", "")
        category = finding_data.get("category", "")

        target_fixed = "fixed" in target_url.lower() or config.get("simulate_fix") is True

        if target_fixed:
            return {
                "verified": True,
                "new_status": "Resolved",
                "observed_result": {
                    "simulation_notice": "GENERATED BY MOCK ENGINE - SIMULATED RETEST PROBE",
                    "http_status": 403 if category in ("BOLA", "AUTH") else 200,
                    "message": "[SIMULATED MOCK RETEST] Authorization check succeeded: access was denied to unauthorized principal.",
                    "timestamp": "verified",
                },
            }
        else:
            return {
                "verified": False,
                "new_status": "Still Vulnerable",
                "observed_result": {
                    "simulation_notice": "GENERATED BY MOCK ENGINE - SIMULATED RETEST PROBE",
                    "http_status": 200,
                    "message": "[SIMULATED MOCK RETEST] Resource still accessible without proper authorization.",
                    "timestamp": "retested",
                },
            }


_override_engine: Optional[BaseSecurityEngineAdapter] = None


def set_security_engine_override(adapter: Optional[BaseSecurityEngineAdapter]) -> None:
    """Set an engine adapter override (used for testing or runtime pluggability)."""
    global _override_engine
    _override_engine = adapter


def reset_security_engine() -> None:
    """Clear any active engine adapter override."""
    global _override_engine
    _override_engine = None


def create_safe_http_client(
    allow_lab: bool = False,
    timeout: float = 10.0,
    headers: Optional[Dict[str, str]] = None,
    transport: Optional[httpx.BaseTransport] = None,
    target_url: Optional[str] = None,
) -> httpx.Client:
    """Create an HTTP client configured with strict timeouts, destination-IP pinning, and disabled automatic redirects.

    Guarantees:
    - No automatic redirects (follow_redirects=False).
    - Pinned destination IP transport preventing DNS rebinding TOCTOU attacks.
    - Environment proxy disabled (trust_env=False).
    """
    client_headers = {
        "User-Agent": "API-Sentinel-Security-Scanner/1.0",
        **(headers or {}),
    }

    if transport is None:
        pinned_map: Dict[str, str] = {}
        if target_url:
            try:
                host, ip = validate_target_safety(target_url, allow_lab=allow_lab)
                pinned_map[host] = ip
            except Exception:
                pass
        transport = PinnedHTTPTransport(pinned_map=pinned_map, allow_lab=allow_lab)

    return httpx.Client(
        transport=transport,
        timeout=httpx.Timeout(timeout, connect=5.0),
        follow_redirects=False,  # Redirects MUST be validated via validate_safe_redirect() / execute_safe_request()
        headers=client_headers,
        trust_env=False,
    )


def get_security_engine() -> BaseSecurityEngineAdapter:
    """Factory function returning the active security engine adapter.

    1. Returns any runtime override registered via set_security_engine_override().
    2. If Member 1's engine module (app.security_engine.member1_engine) is present, loads it.
    3. Otherwise, falls back to MockSecurityEngineAdapter for isolated development.
    """
    global _override_engine
    if _override_engine is not None:
        return _override_engine

    try:
        # Check if Member 1 has provided engine module in app.security_engine.member1_engine
        from app.security_engine import member1_engine  # type: ignore
        logger.info("Loaded Member 1's security engine module.")
        return member1_engine.EngineAdapter()
    except (ImportError, AttributeError):
        logger.info("Using standard isolated security testing engine adapter.")
        return MockSecurityEngineAdapter()
