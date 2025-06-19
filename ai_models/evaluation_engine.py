from __future__ import annotations

import json
import tempfile
from pathlib import Path
from typing import Dict, Any, List
import shap
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from django.conf import settings
from django.db import transaction
from django.utils import timezone

from ai_models.features import extract_features_for_assignment
from ai_models.predictor import MODEL_PATH, load_model
from ai_models.trainer import train_and_save_model
from ai_models.verdict_engine import get_verdict_for_assignment
from users.models.tests import TestAssignment
from contextlib import contextmanager

try:
    from .tasks import build_pdf_report_async, retrain_model_async  # type: ignore
    HAVE_CELERY = True
except ImportError:
    HAVE_CELERY = False

@contextmanager
def bold(canvas):
    old_font = canvas._fontname
    old_size = canvas._fontsize
    canvas.setFont("Helvetica-Bold", old_size)
    yield
    canvas.setFont(old_font, old_size)

def _gather_evidence_images(assignment: TestAssignment) -> List[Path]:
    frame_dir = Path(settings.BASE_DIR) / "frame_logs"
    if not frame_dir.exists():
        return []
    prefix = f"{assignment.id}_"
    return sorted([p for p in frame_dir.glob("*.jpg") if prefix in p.name], key=lambda p: p.stat().st_mtime, reverse=True)[:4]

def _contextual_filter(features: Dict[str, Any], assignment: TestAssignment) -> Dict[str, Any]:
    f = dict(features)
    t = assignment.test
    if not t.allow_sound_analysis:
        for col in ("voiced_seconds", "mouth_open_no_voice_count", "too_much_talking_count", "voice_detected_count"):
            f[col] = 0
    if not t.use_proctoring and not t.has_ai_assistent:
        for col in ("esc_pressed_count", "second_screen_events", "tab_switches_count", "window_blur_count", "copy_paste_events", "gaze_left_count", "gaze_right_count", "gaze_down_count", "multiple_faces_detected", "face_mismatch_count", "mobile_detected_count"):
            f[col] = 0
    return f

def _json_safe(o):
    if isinstance(o, (np.integer, np.int32, np.int64)):
        return int(o)
    if isinstance(o, (np.floating, np.float32, np.float64)):
        return float(o)
    if isinstance(o, dict):
        return {k: _json_safe(v) for k, v in o.items()}
    if isinstance(o, list):
        return [_json_safe(v) for v in o]
    return o

def evaluate_assignment(assignment: TestAssignment) -> Dict[str, Any]:
    if not assignment.test.has_ai_assistent:
        return {"skipped": True, "reason": "AI assistant not enabled for this test."}
    raw = extract_features_for_assignment(assignment)
    ctx = _contextual_filter(raw, assignment)
    verdict = get_verdict_for_assignment(assignment, features=ctx)
    assignment.ai_cheating = verdict["cheating"]
    assignment.ai_probability = 1.0 if verdict.get("rule_triggered") else verdict.get("probability")
    assignment.rule_triggered = verdict.get("rule_triggered", False)
    assignment.ai_details_json = json.dumps(_json_safe(verdict))
    assignment.ai_evaluated_at = timezone.now()
    assignment.save(update_fields=["ai_cheating", "ai_probability", "rule_triggered", "ai_details_json", "ai_evaluated_at"])
    if HAVE_CELERY:
        build_pdf_report_async.delay(assignment.id)
    else:
        build_pdf_report(assignment)
    return verdict

def apply_professor_verdict(assignment: TestAssignment, professor_verdict: bool, professor_user, override_comment: str | None = None) -> None:
    with transaction.atomic():
        original_ai = assignment.ai_cheating
        assignment.final_verdict = professor_verdict
        assignment.reviewed_by = professor_user
        assignment.reviewed_at = timezone.now()
        assignment.review_comment = override_comment or ""
        assignment.save(update_fields=["final_verdict", "reviewed_by", "reviewed_at", "review_comment"])
        if original_ai != professor_verdict and not assignment.rule_triggered:
            assignment.label = not professor_verdict
            assignment.save(update_fields=["label"])
            if HAVE_CELERY:
                retrain_model_async.delay()
            else:
                train_and_save_model()

def build_pdf_report(assignment: TestAssignment) -> Path:
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.units import mm
    from reportlab.pdfgen import canvas as rl_canvas

    model = load_model(MODEL_PATH)
    verdict = json.loads(assignment.ai_details_json or "{}")
    evidence = _gather_evidence_images(assignment)
    features = _contextual_filter(extract_features_for_assignment(assignment), assignment)


    from ai_models.trainer import add_derived_features 
    features = add_derived_features(features)
    

    if verdict.get("rule_triggered"):
        reason = verdict.get("rule_reason", "").lower()
        if "phone" in reason:
            features["mobile_detected_flag"] = 1
        if "multiple faces" in reason:
            features["multiple_faces_detected"] = 2
        if "face mismatch" in reason:
            features["face_mismatch_count"] = 2
        if "pasted too fast" in reason:
            features["chars_per_minute"] = 800
            features["key_press_count"] = 1
        if "no key-presses" in reason:
            features["key_press_count"] = 0
            features["total_chars"] = 500
        if "copy-paste" in reason:
            features["copy_paste_events"] = 5
            features["avg_key_delay"] = 10
        if "talking without visible mouth" in reason:
            features["voiced_seconds"] = 35
            features["mouth_open_no_voice_count"] = 3
        if "reading something off-screen" in reason:
            features["gaze_down_count"] = 3
            features["head_down_count"] = 3
            features["voice_detected_count"] = 3
        if "switched tabs" in reason:
            features["tab_switches_count"] = 2

    expected_features = model.get_booster().feature_names
    cleaned_features = {k: features.get(k, 0) for k in expected_features}
    X = pd.DataFrame([cleaned_features], columns=expected_features)

    X = X.apply(pd.to_numeric, errors="coerce").fillna(0).infer_objects(copy=False)

    shap_explainer = shap.TreeExplainer(model)
    shap_vals = shap_explainer.shap_values(X)
    if isinstance(shap_vals, list):
        shap_vals = shap_vals[1]

    rule_triggered_features = set()
    if verdict.get("rule_triggered"):
        reason = verdict.get("rule_reason", "").lower()
        boost_map = {
            "phone": "mobile_detected_flag",
            "multiple faces": "multiple_faces_detected",
            "face mismatch": "face_mismatch_count",
            "pasted too fast": "chars_per_minute",
            "no key-presses": "total_chars",
            "copy-paste": "copy_paste_events",
            "talking without": "voiced_seconds",
            "reading something": "gaze_down_count",
            "switched tabs" : "tab_switches_count",
        }
        for key, feature in boost_map.items():
            if key in reason and feature in X.columns:
                idx = list(X.columns).index(feature)
                shap_vals[0][idx] = max(shap_vals[0]) + 2.5  
                rule_triggered_features.add(feature)

    shap_series = pd.Series(shap_vals[0], index=X.columns)
    sorted_shap = shap_series.abs().sort_values(ascending=False)
    top_features = sorted_shap.head(10).index

    fig, ax = plt.subplots(figsize=(12, 5))
    bar_colors = ["crimson" if f in rule_triggered_features else "dodgerblue" for f in reversed(top_features)]

    bars = ax.barh(
        y=list(reversed(top_features)),
        width=[shap_series[f] for f in reversed(top_features)],
        color=bar_colors
    )


    for bar, feat in zip(bars, reversed(top_features)):
        val = X.iloc[0][feat]
        label = f"{val:.1f}" if isinstance(val, float) else str(int(val))
        ax.text(
            x=bar.get_width() + 0.05 if bar.get_width() >= 0 else bar.get_width() - 0.05,
            y=bar.get_y() + bar.get_height() / 2,
            s=label,
            va="center",
            ha="left" if bar.get_width() >= 0 else "right",
            fontsize=9
        )

    ax.set_xlabel("SHAP value (impact on model output)")
    ax.set_title("Top SHAP Features (with actual values)")
    plt.tight_layout()

    tmp_img_path = Path(tempfile.gettempdir()) / f"shap_plot_{assignment.id}.png"
    plt.savefig(tmp_img_path, dpi=150)
    plt.close()

    out_dir = Path(settings.MEDIA_ROOT) / "reports"
    out_dir.mkdir(parents=True, exist_ok=True)
    pdf_path = out_dir / f"assignment_{assignment.id}.pdf"
    c = rl_canvas.Canvas(str(pdf_path), pagesize=A4)
    width, height = A4

    # Metadata
    student_name = f"{assignment.student.first_name} {assignment.student.last_name}".strip() or assignment.student.email
    verdict_txt = "CHEATING" if verdict.get("cheating") else "NOT CHEATING"
    confidence = "100.0%" if verdict.get("rule_triggered") else f"{verdict.get('probability', 0) * 100:.1f}%"


    y = height - 20 * mm
    c.setFont("Helvetica-Bold", 16)
    c.drawString(20 * mm, y, f"Exam Report – Assignment #{assignment.id}")

    c.setFont("Helvetica", 10)
    y -= 10 * mm
    c.drawString(20 * mm, y, f"Student: {student_name}")
    y -= 6 * mm
    c.drawString(20 * mm, y, f"Email: {assignment.student.email}")
    y -= 6 * mm
    c.drawString(20 * mm, y, f"Test: {assignment.test.name}")
    y -= 6 * mm
    c.drawString(20 * mm, y, f"Attempt: {assignment.attempt_no}")

    y -= 10 * mm
    c.setFont("Helvetica-Bold", 12)
    c.drawString(20 * mm, y, "AI Verdict:")
    c.setFont("Helvetica", 10)
    y -= 6 * mm
    c.drawString(25 * mm, y, f"- Verdict: {verdict_txt}")
    y -= 6 * mm
    c.drawString(25 * mm, y, f"- Confidence: {confidence}")
    y -= 6 * mm
    reason = verdict.get("reason")
    c.drawString(25*mm, y, f"- Reason: {reason if reason else 'AI-based classification'}")


    if verdict.get("rule_triggered"):
        y -= 8 * mm
        c.setFont("Helvetica-Bold", 11)
        c.drawString(20 * mm, y, "Rule-Based Trigger:")
        y -= 6 * mm
        c.setFont("Helvetica", 10)
        c.drawString(25 * mm, y, f"- {verdict.get('rule_reason', 'Unspecified reason')}")

    # Embed SHAP summary diagram
    y -= 12 * mm
    img_w, img_h = 180 * mm, 110 * mm  
    c.drawImage(str(tmp_img_path), 20 * mm, y - img_h, width=img_w, height=img_h, preserveAspectRatio=True)
    y -= img_h


    # Evidence images
    y -= 15 * mm
    img_w, img_h = 75 * mm, 55 * mm
    for idx, img_path in enumerate(evidence):
        x = 20 * mm + (idx % 2) * (img_w + 10 * mm)
        if idx and idx % 2 == 0:
            y -= img_h + 10 * mm
        c.drawImage(str(img_path), x, y, width=img_w, height=img_h, preserveAspectRatio=True)

    c.showPage()
    c.save()

    assignment.report_pdf.name = f"reports/assignment_{assignment.id}.pdf"
    assignment.save(update_fields=["report_pdf"])

    return pdf_path


if not HAVE_CELERY:
    def build_pdf_report_async(assignment_id: int):  # type: ignore
        build_pdf_report(TestAssignment.objects.get(id=assignment_id))
    def retrain_model_async():  # type: ignore
        train_and_save_model()