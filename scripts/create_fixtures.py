"""Generate first-party example content. No external AI or voice downloads."""
import hashlib
import json
import sys
from pathlib import Path

from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer

ROOT = Path(__file__).resolve().parents[1] / "backend" / "fixtures"
ROOT.mkdir(parents=True, exist_ok=True)

if "--finalize" in sys.argv:
    manifest = json.loads((ROOT / "manifest.json").read_text(encoding="utf-8"))
    for kind, filename in [("contract", "sample-license.pdf"), ("audio", "sample-narration.wav")]:
        manifest[f"{kind}_sha256"] = hashlib.sha256((ROOT / filename).read_bytes()).hexdigest()
    (ROOT / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print("Demo PDF, stock-TTS narration, and exact-file fixture manifest generated locally.")
    sys.exit(0)

clauses = {
    "artist": "Voice artist: Amara Reed (fictional demo persona).",
    "studio": "Production studio: Northstar Studio (fictional demo persona).",
    "start_date": "License start date: 2026-01-01.",
    "end_date": "License end date: 2027-12-31.",
    "permitted_media": "Permitted media: online advertising.",
    "territories": "Permitted territories: US.",
    "languages": "Permitted languages: English.",
    "campaigns": "All campaigns are allowed, subject to the content restrictions below.",
    "included_seconds": "Included voiced duration: 30 seconds per asset.",
    "billing_basis": "Billing basis: per asset. The allowance resets for each distinct audio asset.",
    "additional_rate": "Additional permitted usage rate: 2.00 USD per voiced second above the allowance.",
    "currency": "Currency: USD.",
    "additional_usage_permitted": "Additional usage is expressly permitted at the stated additional usage rate.",
    "restricted_categories": "Restricted content categories: political advertising, gambling, adult content.",
}
styles = getSampleStyleSheet()
story = [Paragraph("FAIRMODEL | DEMO VOICE LICENSE", styles["Title"]), Spacer(1, 18),
         Paragraph("Local demonstration only. Fictional parties. Not a legal instrument.", styles["Normal"]),
         Spacer(1, 14)]
for clause in clauses.values():
    story.extend([Paragraph(clause, styles["Normal"]), Spacer(1, 9)])
story.extend([Spacer(1, 10), Paragraph("The sample audio uses a Windows stock synthetic voice. "
              "It does not represent Amara Reed's voice or demonstrate speaker identity.", styles["Normal"])])
SimpleDocTemplate(str(ROOT / "sample-license.pdf"), pagesize=A4).build(story)
terms = {
    "artist": "Amara Reed", "studio": "Northstar Studio", "start_date": "2026-01-01", "end_date": "2027-12-31",
    "permitted_media": ["online advertising"], "territories": ["US"], "languages": ["English"], "campaigns": ["*"],
    "included_seconds": "30", "billing_basis": "per_asset", "additional_rate": "2.00", "currency": "USD",
    "additional_usage_permitted": True, "restricted_categories": ["political advertising", "gambling", "adult content"],
    "special_conditions": [], "ambiguities": [],
    "evidence": [{"field": field, "page": 1, "quote": quote} for field, quote in clauses.items()],
}
transcript = (
    "Welcome to Northstar, where everyday ideas become something worth sharing. "
    "Our new collection is designed for the little moments that make a big difference. "
    "From your first cup of coffee to an evening spent with friends, thoughtful design belongs in your day. "
    "Discover simple details, useful features, and products created to last. "
    "Explore the collection online and find a favorite that feels right for you. "
    "Every item tells a story of care, curiosity, and a fresh perspective. "
    "Choose something practical, give something thoughtful, or make room for a new daily ritual. "
    "Our team believes good ideas should be easy to understand and a pleasure to use. "
    "That is why we focus on clear information, honest descriptions, and an experience that puts you first. "
    "Visit Northstar today to learn more about our latest collection. "
    "This original synthetic narration is a FairModel local demonstration. "
    "The recording is used to demonstrate measured speech activity and transparent royalty calculations."
)
(ROOT / "manifest.json").write_text(json.dumps({"terms": terms, "transcript": transcript,
    "notice": "Explicit local fixtures, not live AI responses. Stock TTS; no artist identity claim."}, indent=2), encoding="utf-8")
print("Sample PDF and fixture specification generated. Narration generation is next.")
