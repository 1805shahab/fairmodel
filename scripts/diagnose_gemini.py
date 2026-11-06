"""Diagnose a real Gemini extraction without printing credentials or raw exceptions."""

import json
import logging
import re
import sys
from pathlib import Path

logging.disable(logging.CRITICAL)
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend"))


def main():
    from google import genai
    from google.genai import types
    from pydantic import ValidationError
    from pypdf import PdfReader

    from app.ai import SYSTEM, validate_evidence
    from app.config import settings
    from app.schemas import Terms

    if "--list-models" in sys.argv:
        with genai.Client(
            api_key=settings.gemini_api_key.get_secret_value(), http_options=types.HttpOptions(timeout=30000)
        ) as client:
            available = []
            for model in client.models.list(config={"page_size": 100}):
                name = model.name or ""
                if re.fullmatch(r"models/gemini-[a-zA-Z0-9._-]+", name):
                    available.append(name)
            configured = settings.gemini_model
            print(
                json.dumps(
                    {
                        "configured_model": configured
                        if re.fullmatch(r"gemini-[a-zA-Z0-9._-]+", configured)
                        else "invalid_model_setting",
                        "available_gemini_models": available,
                    }
                )
            )
        return

    reader = PdfReader("fixtures/sample-license.pdf")
    pages = [{"page": i + 1, "text": p.extract_text() or ""} for i, p in enumerate(reader.pages)]
    try:
        with genai.Client(
            api_key=settings.gemini_api_key.get_secret_value(), http_options=types.HttpOptions(timeout=60000)
        ) as client:
            response = client.models.generate_content(
                model=settings.gemini_model,
                contents=json.dumps(
                    {
                        "task": "Extract all licensing terms with exact supporting page quotes.",
                        "untrusted_data": {"pages": pages},
                    }
                ),
                config=types.GenerateContentConfig(
                    system_instruction=SYSTEM,
                    response_mime_type="application/json",
                    response_json_schema=Terms.model_json_schema(),
                    temperature=0,
                ),
            )
        terms = Terms.model_validate_json(response.text)
        checked = validate_evidence(terms, pages)
        print(
            json.dumps(
                {
                    "status": "passed",
                    "verified_citations": len(checked.evidence),
                    "review_flags": len(checked.ambiguities),
                }
            )
        )
    except ValidationError as error:
        print(
            json.dumps(
                {
                    "status": "failed",
                    "category": "response_schema_validation",
                    "error_types": sorted({item["type"] for item in error.errors()}),
                }
            )
        )
    except Exception as error:
        # Read the exception only in memory to map to fixed safe categories. Never print its text/body/URL.
        message = str(error).casefold()
        known = {
            "api key not valid": "invalid_api_key",
            "api_key_invalid": "invalid_api_key",
            "quota": "quota_exhausted",
            "billing": "billing_configuration",
            "not found": "model_or_resource_not_found",
            "not_found": "model_or_resource_not_found",
            "permission": "permission_denied",
            "response_json_schema": "request_schema_rejected",
            "json schema": "request_schema_rejected",
            "additionalproperties": "request_schema_rejected",
            "unsupported": "request_feature_unsupported",
            "connection": "network_connection_failure",
            "timeout": "request_timeout",
        }
        categories = sorted({value for key, value in known.items() if key in message})
        code = getattr(error, "code", None)
        print(
            json.dumps(
                {
                    "status": "failed",
                    "exception_type": type(error).__name__,
                    "provider_http_status": code if isinstance(code, int) else None,
                    "categories": categories or ["unclassified_provider_error"],
                }
            )
        )


if __name__ == "__main__":
    try:
        main()
    except Exception:
        print(json.dumps({"status": "failed", "category": "local_setup_error"}))
