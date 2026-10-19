import ipaddress
import socket

import pytest

from app.security import network_guard
from app.security.network_guard import NetworkPolicy, NetworkPolicyError, is_blocked_ip, resolve_and_validate

BLOCKED = [
    "127.0.0.1", "10.0.0.5", "192.168.1.10", "172.16.0.1", "169.254.169.254", "100.64.0.1",
    "0.0.0.0", "224.0.0.1", "::1", "fe80::1", "fc00::1",
    "::ffff:127.0.0.1", "::ffff:10.0.0.1",  # IPv4 hidden inside IPv6
    "2002:7f00:1::",  # 6to4 wrapper around 127.0.0.1
    "64:ff9b::7f00:1",  # NAT64 wrapper around 127.0.0.1
]
PUBLIC = ["8.8.8.8", "1.1.1.1", "2606:4700:4700::1111"]


@pytest.mark.parametrize("address", BLOCKED)
def test_blocks_non_public_addresses(address):
    assert is_blocked_ip(ipaddress.ip_address(address))


@pytest.mark.parametrize("address", PUBLIC)
def test_allows_public_addresses(address):
    assert not is_blocked_ip(ipaddress.ip_address(address))


def test_hostname_resolving_to_private_ip_is_blocked(monkeypatch):
    monkeypatch.setattr(network_guard, "_resolve", lambda host, port: ["10.0.0.5"])
    with pytest.raises(NetworkPolicyError) as exc:
        resolve_and_validate("innocent.example.com", 5432, NetworkPolicy())
    assert exc.value.code == "host_not_allowed"


def test_mixed_public_and_private_records_are_blocked(monkeypatch):
    monkeypatch.setattr(network_guard, "_resolve", lambda host, port: ["8.8.8.8", "10.0.0.5"])
    with pytest.raises(NetworkPolicyError):
        resolve_and_validate("rebind.example.com", 5432, NetworkPolicy())


def test_public_host_returns_the_validated_ip(monkeypatch):
    monkeypatch.setattr(network_guard, "_resolve", lambda host, port: ["8.8.8.8"])
    assert resolve_and_validate("db.example.com", 5432, NetworkPolicy()) == "8.8.8.8"


def test_allowlisted_host_may_be_private(monkeypatch):
    monkeypatch.setattr(network_guard, "_resolve", lambda host, port: ["172.18.0.5"])
    policy = NetworkPolicy(allowed_hosts=frozenset({"sampledb"}))
    assert resolve_and_validate("SampleDB", 5432, policy) == "172.18.0.5"
    with pytest.raises(NetworkPolicyError):
        resolve_and_validate("otherhost", 5432, policy)


def test_allow_private_flag_disables_the_check(monkeypatch):
    monkeypatch.setattr(network_guard, "_resolve", lambda host, port: ["10.0.0.5"])
    assert resolve_and_validate("x", 5432, NetworkPolicy(allow_private=True)) == "10.0.0.5"


@pytest.mark.parametrize("sneaky", ["2130706433", "127.1", "localhost"])
def test_alternative_spellings_of_loopback_are_caught_after_resolution(sneaky):
    """The name 'looks' harmless; only checking the RESOLVED address reveals it."""
    with pytest.raises(NetworkPolicyError) as exc:
        resolve_and_validate(sneaky, 5432, NetworkPolicy())
    assert exc.value.code == "host_not_allowed"


def test_dns_failure_is_reported(monkeypatch):
    def fail(*args, **kwargs):
        raise socket.gaierror("no such host")

    monkeypatch.setattr(socket, "getaddrinfo", fail)
    with pytest.raises(NetworkPolicyError) as exc:
        resolve_and_validate("does-not-exist.example.com", 5432, NetworkPolicy())
    assert exc.value.code == "dns_failed"