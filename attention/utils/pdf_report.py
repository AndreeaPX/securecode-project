from django.template.loader import render_to_string
from django.conf import settings
from weasyprint import HTML
from pathlib import Path

def render_attention_pdf(report_data, session_id):
    html = render_to_string("attention/pdf_template.html", {
        "avg_attention": report_data["avg_attention"],
        "timeline": report_data["timeline"],
        "advice": report_data["advice"],
    })

    out_dir = Path(settings.MEDIA_ROOT) / "attention_reports"
    out_dir.mkdir(parents=True, exist_ok=True)

    filename = f"attention_{session_id}.pdf"
    pdf_path = out_dir / filename

    HTML(string=html).write_pdf(pdf_path)

    return Path("attention_reports") / filename
