"""Allowlisted provider diagnostics. Never expose bodies, audio, keys or transcripts."""

from fastapi import HTTPException

MESSAGES = {
    "BILLING_OR_PAID_TIER": "reported a billing or paid-tier access requirement; check the Gemini project's billing/access",
    "CONSENT_VERIFICATION": "reported a consent verification problem; check that the same adult speaker clearly recorded the required statement",
    "SPEAKER_MISMATCH": "reported a speaker-match problem between the reference and consent recordings",
    "AUDIO_REJECTED": "rejected the audio format or quality; check the reference and consent recordings",
    "SYNTHETIC_AUDIO_REJECTED": "reported synthetic/watermarked input; authentic human recordings are required",
    "REQUEST_SCHEMA": "rejected an API request field/schema; the integration needs correction before another attempt",
    "MODEL_ACCESS": "reported that this model/resource does not support or permit the requested operation",
    "REGION_ACCESS": "reported an unsupported location or regional access restriction",
    "AUTHENTICATION": "rejected authentication; check the backend Gemini credentials",
    "PERMISSION": "denied access to this operation",
    "QUOTA": "reported exhausted quota or a rate limit",
    "INVALID_REQUEST_UNSPECIFIED": "rejected the request without a recognized safe reason category; this does not establish a schema or consent problem",
    "PROVIDER_UNAVAILABLE": "reported a provider service failure",
    "NETWORK_OR_TIMEOUT": "could not complete the connection or request; its remote outcome may be unknown",
}
REASONS = {
    "BILLING_DISABLED": "BILLING_OR_PAID_TIER",
    "BILLING_NOT_ACTIVE": "BILLING_OR_PAID_TIER",
    "PAID_TIER_REQUIRED": "BILLING_OR_PAID_TIER",
    "API_KEY_INVALID": "AUTHENTICATION",
    "SERVICE_DISABLED": "PERMISSION",
    "ACCESS_TOKEN_SCOPE_INSUFFICIENT": "PERMISSION",
    "CONSENT_VERIFICATION_FAILED": "CONSENT_VERIFICATION",
    "INVALID_CONSENT": "CONSENT_VERIFICATION",
    "SPEAKER_MISMATCH": "SPEAKER_MISMATCH",
}
STATUSES = {
    "INVALID_ARGUMENT",
    "PERMISSION_DENIED",
    "UNAUTHENTICATED",
    "RESOURCE_EXHAUSTED",
    "NOT_FOUND",
    "UNAVAILABLE",
    "INTERNAL",
    "FAILED_PRECONDITION",
}
FIELDS = {
    "model",
    "store",
    "voice",
    "replicated",
    "source_audio",
    "consent_audio",
    "mime_type",
    "input",
    "response_format",
    "generation_config",
    "speech_config",
}


def diagnostic(stage, response=None, error=None):
    status = (
        response.status_code
        if response is not None
        else getattr(error, "status_code", None) or getattr(error, "code", None)
    )
    status = status if isinstance(status, int) else None
    category = {
        400: "INVALID_REQUEST_UNSPECIFIED",
        401: "AUTHENTICATION",
        403: "PERMISSION",
        404: "MODEL_ACCESS",
        429: "QUOTA",
    }.get(status, "PROVIDER_UNAVAILABLE" if status else "NETWORK_OR_TIMEOUT")
    result = {
        "stage": stage,
        "provider_http_status": status,
        "category": category,
        "reason_source": "http_status_only",
        "voice_replication_accepted": stage == "speech_synthesis",
    }
    if response is None:
        response = getattr(error, "raw_response", None)
    try:
        if response is None or len(response.content) > 65536:
            return result
        payload = response.json()
        body = payload.get("error", {})
        if not isinstance(body, dict):
            return result
        if body.get("status") in STATUSES:
            result["provider_status"] = body["status"]
        details = body.get("details", [])
        if not isinstance(details, list):
            details = []
        for detail in details:
            if isinstance(detail, dict) and detail.get("reason") in REASONS:
                result.update(
                    category=REASONS[detail["reason"]],
                    provider_reason=detail["reason"],
                    reason_source="recognized_reason_code",
                )
                return result
        # Messages are inspected only for fixed categories, never copied or logged.
        message = body.get("message", "")
        message = message.casefold() if isinstance(message, str) else ""
        candidates = [
            (
                "REQUEST_SCHEMA",
                any(
                    x in message
                    for x in (
                        "unknown name",
                        "unknown field",
                        "invalid json",
                        "unrecognized field",
                        "cannot find field",
                    )
                ),
            ),
            (
                "BILLING_OR_PAID_TIER",
                any(x in message for x in ("billing", "paid tier", "paid-tier", "free tier", "free-tier")),
            ),
            (
                "SPEAKER_MISMATCH",
                "speaker" in message
                and any(
                    x in message for x in ("mismatch", "does not match", "different speaker", "same speaker")
                ),
            ),
            (
                "SYNTHETIC_AUDIO_REJECTED",
                any(x in message for x in ("synthid", "watermark", "synthetic audio", "synthetic speech")),
            ),
            (
                "CONSENT_VERIFICATION",
                "consent" in message
                and any(
                    x in message
                    for x in (
                        "fail",
                        "invalid",
                        "verify",
                        "verification",
                        "mismatch",
                        "missing",
                        "statement",
                        "phrase",
                    )
                ),
            ),
            (
                "REGION_ACCESS",
                any(
                    x in message
                    for x in ("location is not supported", "unsupported location", "region is not supported")
                ),
            ),
            (
                "MODEL_ACCESS",
                "model" in message
                and any(
                    x in message
                    for x in ("not supported", "does not support", "not available", "unsupported")
                ),
            ),
            (
                "AUDIO_REJECTED",
                any(
                    x in message
                    for x in (
                        "invalid audio",
                        "audio format",
                        "sample rate",
                        "sample_rate",
                        "audio quality",
                        "audio is too",
                        "audio duration",
                    )
                ),
            ),
        ]
        for label, matched in candidates:
            if matched:
                result.update(category=label, reason_source="recognized_message_category")
                break
        if result["category"] == "REQUEST_SCHEMA":
            # Only fixed API field names can escape; arbitrary provider paths cannot.
            result["request_fields"] = sorted(
                field for field in FIELDS if f'"{field}"' in message or f"'{field}'" in message
            )
    except (ValueError, TypeError, AttributeError, KeyError):
        pass
    return result


class VoiceProviderFailure(HTTPException):
    def __init__(self, detail):
        self.diagnostic = detail
        stage = {"voice_replication": "voice replication", "speech_synthesis": "speech synthesis"}.get(
            detail["stage"], "voice processing"
        )
        status = (
            f" (provider HTTP {detail['provider_http_status']})" if detail.get("provider_http_status") else ""
        )
        reason = MESSAGES.get(detail["category"], MESSAGES["INVALID_REQUEST_UNSPECIFIED"])
        fields = (
            "; request fields: " + ", ".join(detail["request_fields"]) if detail.get("request_fields") else ""
        )
        action = (
            " Review GEMINI_VOICE_REPLICATION_MODEL and provider operation access before starting a new request."
            if detail["stage"] == "voice_replication" and detail["category"] == "MODEL_ACCESS"
            else ""
        )
        super().__init__(
            502,
            f"Gemini {stage} {reason}{status}{fields}.{action} No fixture fallback was used. This saved request will not be automatically repeated.",
        )
