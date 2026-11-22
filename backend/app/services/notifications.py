import ipaddress
from urllib.parse import urlsplit


def validate_webhook_url(url: str) -> str:
    parsed = urlsplit(url)
    if parsed.scheme != "https" or not parsed.hostname:
        raise ValueError("Webhook URL must use HTTPS and include a hostname")
    if parsed.username or parsed.password or parsed.fragment:
        raise ValueError("Webhook URL must not include credentials or a fragment")
    hostname = parsed.hostname.rstrip(".").lower()
    if hostname in {"localhost", "metadata.google.internal"} or hostname.endswith(
        (".localhost", ".local", ".internal", ".test", ".invalid")
    ):
        raise ValueError("Local and reserved webhook targets are not allowed")

    try:
        address = ipaddress.ip_address(hostname)
    except ValueError as exc:
        if "." not in hostname:
            raise ValueError(
                "Webhook hostname must be a public fully qualified domain name"
            ) from exc
    else:
        if not address.is_global:
            raise ValueError("Private and non-global webhook IP addresses are not allowed")
    try:
        port = parsed.port
    except ValueError as exc:
        raise ValueError("Webhook URL contains an invalid port") from exc
    if port == 0:
        raise ValueError("Webhook URL port must be greater than zero")
    return url
