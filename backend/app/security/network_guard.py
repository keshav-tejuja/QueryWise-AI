import ipaddress
import socket
from concurrent.futures import ThreadPoolExecutor
from concurrent.futures import TimeoutError as FutureTimeout
from dataclasses import dataclass

from app.core.config import settings

DNS_TIMEOUT_SECONDS = 5.0
_executor = ThreadPoolExecutor(max_workers=4, thread_name_prefix="dns")
_NAT64 = ipaddress.ip_network("64:ff9b::/96")

BLOCKED_MESSAGE = (
    "This host isn't allowed. Private, loopback and link-local addresses are blocked "
    "unless an administrator allowlists the host."
)


class NetworkPolicyError(Exception):
    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code
        self.message = message


@dataclass(frozen=True)
class NetworkPolicy:
    allow_private: bool = False
    allowed_hosts: frozenset[str] = frozenset()

    @classmethod
    def from_settings(cls) -> "NetworkPolicy":
        return cls(settings.db_allow_private_hosts, settings.allowed_hosts)


def _unwrap(ip: ipaddress.IPv4Address | ipaddress.IPv6Address):
    """Reveal an IPv4 address hidden inside an IPv6 one, so ::ffff:127.0.0.1 can't slip past."""
    if isinstance(ip, ipaddress.IPv6Address):
        if ip.ipv4_mapped is not None:
            return ip.ipv4_mapped
        if ip.sixtofour is not None:
            return ip.sixtofour
        if ip in _NAT64:
            return ipaddress.IPv4Address(int(ip) & 0xFFFFFFFF)
    return ip


def is_blocked_ip(ip: ipaddress.IPv4Address | ipaddress.IPv6Address) -> bool:
    ip = _unwrap(ip)
    return (
        ip.is_loopback
        or ip.is_link_local  # includes the 169.254.169.254 cloud-metadata address
        or ip.is_multicast
        or ip.is_reserved
        or ip.is_unspecified
        or ip.is_private
        or not ip.is_global  # also catches carrier-grade NAT (100.64.0.0/10)
    )


def _resolve(host: str, port: int) -> list[str]:
    future = _executor.submit(socket.getaddrinfo, host, port, 0, socket.SOCK_STREAM)
    try:
        infos = future.result(timeout=DNS_TIMEOUT_SECONDS)
    except FutureTimeout:
        raise NetworkPolicyError("dns_timeout", "The host name lookup timed out. Try again shortly.") from None
    except (socket.gaierror, UnicodeError):
        raise NetworkPolicyError(
            "dns_failed", "The host name couldn't be resolved. Check the spelling."
        ) from None
    addresses: list[str] = []
    for info in infos:
        address = str(info[4][0])
        if address not in addresses:
            addresses.append(address)
    if not addresses:
        raise NetworkPolicyError("dns_failed", "The host name couldn't be resolved. Check the spelling.")
    return addresses


def resolve_and_validate(host: str, port: int, policy: NetworkPolicy | None = None) -> str:
    """Resolve `host` ONCE, validate every resulting address, and return the IP to connect to.

    The caller must connect to the returned IP (not the hostname) so the address that was
    validated is the address that is used: this is what defeats DNS rebinding.
    """
    policy = policy or NetworkPolicy.from_settings()
    normalized = host.strip().lower().rstrip(".")
    addresses = _resolve(normalized, port)
    ips = [ipaddress.ip_address(address.split("%", 1)[0]) for address in addresses]

    allowlisted = normalized in policy.allowed_hosts
    if not (policy.allow_private or allowlisted):
        # ALL records must be public: a name with one public and one private record is rejected.
        if any(is_blocked_ip(ip) for ip in ips):
            raise NetworkPolicyError("host_not_allowed", BLOCKED_MESSAGE)
    return str(ips[0])