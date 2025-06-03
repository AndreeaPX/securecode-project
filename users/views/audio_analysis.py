import os
import io
import webrtcvad
import numpy as np
import tempfile
import subprocess
from datetime import timedelta
from django.utils import timezone
from django.http import JsonResponse
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from users.models.tests import TestAssignment, StudentActivityLog, TempFaceEventState
from scipy.signal import resample
import soundfile as sf
from django.db.models import Q
from django.db import IntegrityError

FFMPEG_PATH = r"C:\ffmpeg\bin\ffmpeg.exe"

def convert_webm_to_wav(audio_bytes):
    if len(audio_bytes) < 5000 or not audio_bytes.startswith(b'\x1a\x45\xdf\xa3'):
        print("[WARN] Audio file too short or malformed")
        raise RuntimeError("Audio too short")

    if not audio_bytes.startswith(b'\x1a\x45\xdf\xa3'):
        print("[ERROR] Not a valid EBML header - likely not a proper WebM file")
        raise RuntimeError("Invalid WebM header")

    with tempfile.NamedTemporaryFile(delete=False, suffix=".webm") as in_file:
        in_file.write(audio_bytes)
        in_file.flush()
        webm_path = in_file.name

    # DEBUG: keep file for inspection
    print(f"[DEBUG] Saved WebM file at: {webm_path}")

    wav_file = tempfile.NamedTemporaryFile(delete=False, suffix=".wav")
    wav_file.close()

    print(f"[DEBUG] Running ffmpeg on: {webm_path}")
    result = subprocess.run(
        [FFMPEG_PATH, "-y", "-i", webm_path, "-ar", "16000", "-ac", "1", "-f", "wav", wav_file.name],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )

    if result.returncode != 0:
        print("[ERROR] ffmpeg stderr:", result.stderr.decode())
        print("[ERROR] ffmpeg failed with WebM file at:", webm_path)
        raise RuntimeError("ffmpeg conversion failed")

    try:
        os.remove(webm_path)
    except Exception as e:
        print(f"[WARN] Couldn't delete temp .webm file: {e}")

    with open(wav_file.name, "rb") as f:
        wav_bytes = f.read()

    try:
        os.remove(wav_file.name)
    except Exception as e:
        print(f"[WARN] Couldn't delete temp .wav file: {e}")

    return wav_bytes


from django.db import transaction

def log_event(user, assignment, attempt_no, event_type, debounce_seconds=10):
    now = timezone.now()

    with transaction.atomic():  # AICI adaugi contextul necesar
        try:
            event = TempFaceEventState.objects.select_for_update().get(
                user=user,
                assignment=assignment,
                attempt_no=attempt_no,
                event_type=event_type,
            )
            if now - event.first_seen > timedelta(seconds=debounce_seconds):
                event.delete()
                return True
            else:
                event.last_seen = now
                event.save(update_fields=["last_seen"])
                return False
        except TempFaceEventState.DoesNotExist:
            TempFaceEventState.objects.create(
                user=user,
                assignment=assignment,
                attempt_no=attempt_no,
                event_type=event_type,
            )
            return False


def get_mouth_state(user, assignment):
    now = timezone.now()
    mouth_event = TempFaceEventState.objects.filter(
        Q(user=user) & 
        Q(assignment=assignment) & 
        Q(event_type__in=["mouth_open", "mouth_closed"])
    ).order_by('-last_seen').first()

    if mouth_event and now - mouth_event.last_seen < timedelta(seconds=15):
        return mouth_event.event_type == "mouth_open"
    return None

def analyze_voice(audio_bytes):
    vad = webrtcvad.Vad(2)
    wav_bytes = convert_webm_to_wav(audio_bytes)

    waveform, sample_rate = sf.read(io.BytesIO(wav_bytes))
    print(f"[DEBUG] Sample rate: {sample_rate}, Shape: {waveform.shape}")

    if waveform.ndim > 1:
        waveform = waveform.mean(axis=1)

    if sample_rate != 16000:
        print(f"[DEBUG] Resampling from {sample_rate} Hz to 16000 Hz")
        num_samples = int(len(waveform) * 16000 / sample_rate)
        waveform = resample(waveform, num_samples)

    waveform = np.clip(waveform, -1, 1)
    pcm_waveform = (waveform * 32768).astype(np.int16)

    frame_ms = 30
    frame_len = int(16000 * frame_ms / 1000)
    voiced_frames = 0
    total_frames = 0

    for i in range(0, len(pcm_waveform) - frame_len, frame_len):
        frame = pcm_waveform[i:i + frame_len]
        if vad.is_speech(frame.tobytes(), 16000):
            voiced_frames += 1
        total_frames += 1

    if total_frames == 0:
        raise RuntimeError("No usable audio frames")

    voiced_ratio = voiced_frames / total_frames
    voiced_seconds = voiced_frames * frame_ms / 1000

    print(f"[DEBUG] Voiced ratio: {voiced_ratio:.2f}, Voiced secs: {voiced_seconds:.2f}")
    return voiced_ratio, voiced_seconds

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def live_audio_check(request):
    user = request.user
    assignment_id = request.data.get("assignment_id")
    audio_file = request.FILES.get("audio_file")

    print(f"[DEBUG] Received audio check for assignment {assignment_id}")

    if not assignment_id or not audio_file:
        return JsonResponse({"error": "Missing data"}, status=400)

    audio_bytes = audio_file.read()

    # SALVARE TEMPORARA PENTRU DEBUG
    import os
    os.makedirs("debug_logs", exist_ok=True)
    with open("debug_logs/received_audio.webm", "wb") as f:
        f.write(audio_bytes)
    print("[DEBUG] Saved audio input to debug_logs/received_audio.webm")

    if len(audio_bytes) < 5000:
        print(f"[WARN] Skipped: file too short ({len(audio_bytes)} bytes)")
        return JsonResponse({"error": "Audio too short"}, status=200)

    try:
        assignment = TestAssignment.objects.get(id=assignment_id, student=user)
    except TestAssignment.DoesNotExist:
        return JsonResponse({"error": "Invalid assignment"}, status=404)

    try:
        voiced_ratio, voiced_secs = analyze_voice(audio_bytes)
    except Exception as e:
        print(f"[ERROR] Failed to analyze voice: {e}")
        return JsonResponse({"error": "Audio analysis failed"}, status=200)

    total_talk_time = request.session.get("talk_time", 0)
    total_talk_time += voiced_secs
    request.session["talk_time"] = total_talk_time

    mouth_open = get_mouth_state(user, assignment)
    print(f"[DEBUG] Mouth open: {mouth_open}, Voiced ratio: {voiced_ratio:.2f}, Voiced secs: {voiced_secs:.2f}, Total talk: {total_talk_time:.2f}")

    if mouth_open is None:
        print("[WARN] No mouth state available for current user – skipping mouth detection check.")

    elif voiced_ratio > 0.1 and mouth_open is False:
        if log_event(user, assignment, assignment.attempt_no, "voice_no_mouth", debounce_seconds=10):
            StudentActivityLog.objects.create(
                assignment=assignment,
                attempt_no=assignment.attempt_no,
                focus_lost_count=1,
                anomaly_score=0.85,
                event_type="voice_no_mouth",
                event_message="Voice detected but student's mouth appears closed."
            )

    if total_talk_time >= 45:
        if log_event(user, assignment, assignment.attempt_no, "too_much_talking", debounce_seconds=20):
            StudentActivityLog.objects.create(
                assignment=assignment,
                attempt_no=assignment.attempt_no,
                focus_lost_count=1,
                anomaly_score=0.6,
                event_type="too_much_talking",
                event_message="Student talked excessively during test (audio-only)."
            )
            request.session["talk_time"] = 0 

    if voiced_ratio > 0.05 and voiced_secs > 0.5:
        if log_event(user, assignment, assignment.attempt_no, "voice_detected", debounce_seconds=20):
            StudentActivityLog.objects.create(
                assignment=assignment,
                attempt_no=assignment.attempt_no,
                focus_lost_count=1,
                anomaly_score=0.4,
                event_type="voice_detected",
                event_message="Voice activity detected (single speaker assumed)."
            )

    return JsonResponse({"success": True})

