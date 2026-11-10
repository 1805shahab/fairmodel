"""Sandbox-only transport. Secrets/tokens never enter errors, database rows or diagnostics."""

import hashlib
import threading
import time
from urllib.parse import urlparse

import httpx

from .config import settings

SANDBOX_ORIGIN = "https://api-m.sandbox.paypal.com"
SANDBOX_NOTICE = "PAYPAL SANDBOX — TEST TRANSACTION — NO REAL MONEY"


class PayPalError(Exception):
    def __init__(self, category: str, status: int | None = None, uncertain: bool = False):
        self.category, self.status, self.uncertain = category, status, uncertain
        super().__init__(f"PayPal Sandbox: {category}. No mock fallback was used.")


class PayPalClient:
    def __init__(self, config=settings, transport=None, clock=time.monotonic):
        self.config, self.clock = config, clock
        self.http = httpx.Client(
            base_url=SANDBOX_ORIGIN,
            timeout=httpx.Timeout(25, connect=8),
            follow_redirects=False,
            transport=transport,
        )
        self._token = ""
        self._expires = 0.0
        self._signature = ""
        self._scope = ""
        self._lock = threading.RLock()

    @property
    def configured(self):
        return bool(
            self.config.paypal_client_id.get_secret_value()
            and self.config.paypal_client_secret.get_secret_value()
        )

    @property
    def merchant_key(self):
        # Binds local intents to the configured app without persisting its Client ID.
        return hashlib.sha256(self.config.paypal_client_id.get_secret_value().encode()).hexdigest()

    def _json(self, response):
        try:
            value = response.json()
            if not isinstance(value, dict):
                raise ValueError
            return value
        except ValueError:
            raise PayPalError("INVALID_PROVIDER_RESPONSE", response.status_code) from None

    def _error(self, response, uncertain=False):
        category = {
            400: "INVALID_REQUEST",
            401: "INVALID_CREDENTIALS_OR_TOKEN",
            403: "PERMISSION_DENIED",
            404: "NOT_FOUND",
            422: "VALIDATION_FAILED",
            429: "RATE_LIMITED",
        }.get(response.status_code, "PROVIDER_UNAVAILABLE")
        try:
            if response.json().get("name") == "DUPLICATE_INVOICE_NUMBER":
                category = "DUPLICATE_INVOICE_NUMBER"
        except (ValueError, AttributeError):
            pass
        return PayPalError(category, response.status_code, uncertain or response.status_code >= 500)

    def access_token(self, force=False):
        if self.config.paypal_environment != "sandbox":
            raise PayPalError("PRODUCTION_FORBIDDEN")
        if not self.configured:
            raise PayPalError("CREDENTIALS_NOT_CONFIGURED")
        signature = hashlib.sha256(
            (
                self.config.paypal_client_id.get_secret_value()
                + "\0"
                + self.config.paypal_client_secret.get_secret_value()
            ).encode()
        ).hexdigest()
        with self._lock:
            if not force and self._token and signature == self._signature and self.clock() < self._expires:
                return self._token
            try:
                response = self.http.post(
                    "/v1/oauth2/token",
                    auth=(
                        self.config.paypal_client_id.get_secret_value(),
                        self.config.paypal_client_secret.get_secret_value(),
                    ),
                    data={"grant_type": "client_credentials"},
                )
            except httpx.HTTPError:
                raise PayPalError("NETWORK_OR_TIMEOUT") from None
            if response.status_code != 200:
                raise self._error(response)
            data = self._json(response)
            try:
                token, duration = data["access_token"], int(data["expires_in"])
                if (
                    not isinstance(token, str)
                    or not token
                    or duration <= 0
                    or data.get("token_type", "").lower() != "bearer"
                ):
                    raise ValueError
            except (KeyError, TypeError, ValueError):
                raise PayPalError("INVALID_OAUTH_RESPONSE") from None
            self._token, self._signature = token, signature
            self._scope = str(data.get("scope", ""))
            self._expires = self.clock() + max(0, duration - min(60, duration / 10))
            return token

    def request(self, method, path, *, body=None, params=None, request_id=None):
        if (
            not path.startswith(("/v2/invoicing/", "/v1/notifications/verify-webhook-signature"))
            or ".." in path
            or "?" in path
        ):
            raise PayPalError("UNSUPPORTED_API_PATH")
        for attempt in range(2):
            headers = {
                "Authorization": f"Bearer {self.access_token()}",
                "Accept": "application/json",
                "Content-Type": "application/json",
                "Prefer": "return=representation",
            }
            if request_id:
                headers["PayPal-Request-Id"] = request_id
            try:
                response = self.http.request(method, path, headers=headers, json=body, params=params)
            except httpx.HTTPError:
                if method == "GET" and attempt == 0:
                    time.sleep(0.2)
                    continue
                raise PayPalError("NETWORK_OR_TIMEOUT", uncertain=method != "GET") from None
            if response.status_code == 401 and attempt == 0:
                self.access_token(force=True)
                continue
            if method == "GET" and response.status_code in {429, 500, 502, 503, 504} and attempt == 0:
                try:
                    delay = min(2.0, max(0.2, float(response.headers.get("Retry-After", "0.2"))))
                except ValueError:
                    delay = 0.2
                time.sleep(delay)
                continue
            if response.status_code >= 300:
                raise self._error(response)
            if response.status_code == 204 or not response.content:
                return {}
            result = self._json(response)
            # Create may return a HATEOAS link; caller validates it, never follows arbitrary URLs.
            return result
        raise PayPalError("AUTHENTICATION_FAILED")

    def diagnostic(self, capability=False):
        result = {
            "credentials_configured": self.configured,
            "sandbox_authentication": "FAILED",
            "invoicing_capability": "UNVERIFIED",
            "webhook_configuration": "CONFIGURED"
            if self.config.paypal_webhook_id.get_secret_value()
            else "NOT_CONFIGURED",
            "environment": "sandbox",
        }
        try:
            self.access_token()
            result["sandbox_authentication"] = "SUCCESS"
            if capability:
                self.request(
                    "GET", "/v2/invoicing/invoices", params={"page_size": 1, "total_required": "false"}
                )
                result["invoicing_capability"] = "VERIFIED_READ_ONLY"
        except PayPalError as error:
            result["error_category"] = error.category
            result["provider_http_status"] = error.status
            if capability and error.status == 403:
                result["invoicing_capability"] = "UNAVAILABLE"
        return result


def sandbox_link(value):
    if not isinstance(value, str):
        return None
    try:
        parsed = urlparse(value)
        port = parsed.port
    except ValueError:
        return None
    if (
        parsed.scheme == "https"
        and parsed.hostname in {"www.sandbox.paypal.com", "sandbox.paypal.com"}
        and not parsed.username
        and not parsed.password
        and port in (None, 443)
    ):
        return value
    return None


paypal_client = PayPalClient()
