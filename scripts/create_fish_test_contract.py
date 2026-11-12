"""Create an original fictional PDF test agreement; no app/provider/database writes."""

from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.platypus import (
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "output/pdf/fairmodel-fish-voice-license-20261111.pdf"
NAVY = colors.HexColor("#142B36")
TEAL = colors.HexColor("#087F77")
SLATE = colors.HexColor("#435865")
LIGHT = colors.HexColor("#EEF5F4")
STYLES = {
    "title": ParagraphStyle(
        "title",
        fontName="Helvetica-Bold",
        fontSize=27,
        leading=32,
        textColor=NAVY,
        spaceAfter=12,
    ),
    "section": ParagraphStyle(
        "section",
        fontName="Helvetica-Bold",
        fontSize=11,
        leading=15,
        textColor=TEAL,
        spaceBefore=14,
        spaceAfter=7,
    ),
    "body": ParagraphStyle(
        "body",
        fontName="Helvetica",
        fontSize=10,
        leading=14,
        textColor=NAVY,
        spaceAfter=7,
        alignment=TA_LEFT,
    ),
    "small": ParagraphStyle(
        "small",
        fontName="Helvetica",
        fontSize=8.5,
        leading=12,
        textColor=SLATE,
        spaceAfter=7,
    ),
}


def p(text, kind="body"):
    return Paragraph(text, STYLES[kind])


def footer(canvas, doc):
    width, height = A4
    canvas.setStrokeColor(colors.HexColor("#C9DAD8"))
    canvas.line(44, height - 38, width - 44, height - 38)
    canvas.setFont("Helvetica-Bold", 8)
    canvas.setFillColor(TEAL)
    canvas.drawString(44, height - 28, "FAIRMODEL / VOICE RIGHTS")
    canvas.setFont("Helvetica", 7.5)
    canvas.setFillColor(SLATE)
    canvas.drawRightString(width - 44, height - 28, "FM-FISH-DEMO-20261111-02")
    canvas.line(44, 42, width - 44, 42)
    canvas.drawString(
        44, 28, "FICTIONAL DEMO ONLY / UNSIGNED / NO REAL PAYMENT OBLIGATION"
    )
    canvas.drawRightString(width - 44, 28, f"Page {doc.page}")


def build():
    if OUTPUT.exists():
        raise SystemExit("The new contract already exists; it was not overwritten.")
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    story = [
        p("Synthetic voice<br/>advertising license", "title"),
        p(
            "An original fictional agreement for FairModel workflow testing. Prepared November 11, 2026.",
            "small",
        ),
        p(
            "<b>Demonstration only.</b> This unsigned document uses fictional participants. It does not itself grant rights in a real person's voice, establish real consent or create a real payment obligation.",
            "small",
        ),
        p("01 / Parties and license term", "section"),
        p(
            "<b>Voice artist:</b> Amara Reed (fictional demo persona).<br/><b>Production studio:</b> Northstar Studio (fictional demo persona).<br/><b>License start date:</b> 2026-01-01.<br/><b>License end date:</b> 2027-12-31."
        ),
        p("02 / Permitted commercial scope", "section"),
        p(
            "<b>Permitted media:</b> online advertising. Online commercial advertisements mean online advertising under this agreement. Television advertising, radio advertising and podcasts are not permitted media."
        ),
        p(
            "<b>Permitted territories:</b> US (United States).<br/><b>Permitted languages:</b> English.<br/><b>Allowed campaigns:</b> Cedar Everyday Launch."
        ),
        p(
            "The licensed use is synthetic-voice advertising for ordinary consumer products within the permitted campaign, medium, territory, language and dates."
        ),
        p("03 / Included allowance and additional usage", "section"),
        p(
            "<b>Included voiced duration:</b> 30 seconds per asset.<br/><b>Billing basis:</b> per asset.<br/><b>Additional usage permitted:</b> yes.<br/><b>Additional usage rate:</b> 2.00 USD per spoken second above the included allowance.<br/><b>Currency:</b> USD."
        ),
        p(
            "Billable duration is measured spoken duration, not total recording length; silence and non-speech music are excluded."
        ),
        p(
            "Fractional spoken seconds are billed proportionally. The final monetary amount is rounded to two decimal places using HALF_UP rounding."
        ),
        p("04 / Prohibited content", "section"),
        p(
            "<b>Restricted content categories:</b> political advertising, gambling, adult content. Additional royalty payments do not authorize prohibited content or expand the permitted licensing scope."
        ),
        PageBreak(),
        p("Review and royalty terms", "title"),
        p(
            "Continuation of FM-FISH-DEMO-20261111-02. The parties and commercial terms on page 1 apply.",
            "small",
        ),
        p("05 / Campaign metadata condition", "section"),
        p("Campaign category must be consumer products."),
        p("06 / Review before publication", "section"),
        p(
            "The studio must submit each generated advertisement for licensing compliance review before publication."
        ),
        p("07 / Artist charge approval", "section"),
        p("The artist must approve additional royalties before an invoice is issued."),
        p("08 / Worked examples", "section"),
        p(
            "The examples below illustrate the agreed per-asset allowance and additional rate. They assume permitted use and accepted measured spoken duration; the actual recording measurements determine the result."
        ),
    ]
    rows = [
        [
            p("<b>Spoken duration</b>"),
            p("<b>Additional seconds</b>"),
            p("<b>Additional royalty</b>"),
        ]
    ]
    rows += [
        [p(a), p(b), p(c)]
        for a, b, c in [
            ("20.00 seconds", "0.00", "USD 0.00"),
            ("23.52 seconds", "0.00", "USD 0.00"),
            ("30.00 seconds", "0.00", "USD 0.00"),
            ("45.00 seconds", "15.00", "USD 30.00"),
            ("58.77 seconds", "28.77", "USD 57.54"),
        ]
    ]
    table = Table(rows, colWidths=[174, 165, 168], hAlign="LEFT")
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), LIGHT),
                ("LINEBELOW", (0, 0), (-1, 0), 0.7, TEAL),
                ("LINEBELOW", (0, 1), (-1, -1), 0.4, colors.HexColor("#DDE6E5")),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 10),
                ("RIGHTPADDING", (0, 0), (-1, -1), 10),
                ("TOPPADDING", (0, 0), (-1, -1), 9),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
            ]
        )
    )
    story += [
        table,
        Spacer(1, 20),
        p("Execution status", "section"),
        p(
            "<b>Unsigned fictional test document.</b> No artist signature, studio signature, independent identity verification or provider processing consent is represented by this PDF."
        ),
        p(
            "For local testing, review and approve the extracted terms in FairModel. The actual recording owner must separately grant the selected provider permission in the application. Provider privacy terms and payment-provider notices are displayed separately in that workflow.",
            "small",
        ),
    ]
    SimpleDocTemplate(
        str(OUTPUT),
        pagesize=A4,
        rightMargin=44,
        leftMargin=44,
        topMargin=60,
        bottomMargin=59,
        title="FairModel - Fictional Synthetic Voice Advertising License",
        author="FairModel demo",
        subject="Cedar Everyday Launch - original unsigned testing agreement",
    ).build(story, onFirstPage=footer, onLaterPages=footer)
    print(OUTPUT)


if __name__ == "__main__":
    build()
