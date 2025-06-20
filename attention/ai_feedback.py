import json, requests
from decouple import config
from .utils.rate_limit import rate_limited

HF_API_TOKEN = config("HF_API_TOKEN")

HF_MODEL_REALTIME = "HuggingFaceH4/zephyr-7b-beta"
HF_MODEL_REPORT   = "HuggingFaceH4/zephyr-7b-beta"

HF_URL_REALTIME = f"https://api-inference.huggingface.co/models/{HF_MODEL_REALTIME}"
HF_URL_REPORT   = f"https://api-inference.huggingface.co/models/{HF_MODEL_REPORT}"

SYSTEM_PROMPT = (
    "You are an expert AI assistant that analyses student-attention timelines "
    "and returns 3–15 short, actionable tips as a JSON list of strings only."
)


def _timeline_lines(tl):
    return "\n".join(f"{i*5}s: {p['attention_pct']:.1f}%" for i, p in enumerate(tl))


def _extract_json(text: str):
    # 1) fenced block
    if "```json" in text:
        try:
            return json.loads(text.split("```json")[1].split("```")[0].strip())
        except Exception:
            pass
    # 2) raw JSON
    try:
        return json.loads(text)
    except Exception:
        pass
    # 3) fallback: extract lines
    lines = []
    in_json = False
    for line in text.splitlines():
        line = line.strip()
        if not line:
            continue
        if line.startswith("["):
            in_json = True
        if in_json:
            line = line.lstrip("-•💡").strip()
            if line.endswith(","):
                line = line[:-1]
            if line and not line.lower().startswith("output the"):
                lines.append(line.strip('"'))
    return [l for l in lines if l and not l.lower().startswith("you are an expert")]


def generate_ai_feedback(timeline, avg):
    prompt = (
        f"{SYSTEM_PROMPT}\n\n"
        f"Average attention: {avg:.1f}%\n\n"
        f"Timeline:\n{_timeline_lines(timeline)}\n\n"
        f"Output the JSON list now:"
    )

    try:
        res = requests.post(
            HF_URL_REPORT,
            headers={"Authorization": f"Bearer {HF_API_TOKEN}"},
            json={"inputs": prompt, "parameters": {"max_new_tokens": 300}},
            timeout=60,
        )
        res.raise_for_status()
        raw = res.json()[0].get("generated_text", "").strip()
        tips = _extract_json(raw)
        return tips if tips else [f" Could not parse AI output:\n{raw}"]
    except Exception as e:
        return [f" AI feedback error: {e}"]

@rate_limited(1.5)
def generate_realtime_feedback(avg: float) -> str:
    prompt = (
        "You are helping a college professor monitor student engagement during a live lecture.\n"
        f"Current average student attention level: {avg:.1f}%.\n"
        "Give ONE short, practical tip the professor can apply immediately to improve or maintain classroom engagement.\n"
        "Do NOT suggest student self-help techniques like Pomodoro, note-taking, or breaks.\n"
        "Avoid explanations. Output ONLY the tip, starting with 'TIP:'.\n"
        "TIP:"
    )

    try:
        res = requests.post(
            HF_URL_REALTIME,
            headers={"Authorization": f"Bearer {HF_API_TOKEN}"},
            json={
                "inputs": prompt,
                "parameters": {
                    "max_new_tokens": 60,
                    "temperature": 0.75,
                    "do_sample": True,
                    "top_p": 0.9,
                    "stop": ["\n", "<end>"]
                },
            },
            timeout=30,
        )
        res.raise_for_status()
        raw = res.json()[0].get("generated_text", "").strip()

        if "TIP:" in raw:
            tip = raw.split("TIP:", 1)[1].strip(" -•💡\"'\n")
        else:
            tip = next((l.strip(" -•💡\"'") for l in raw.splitlines() if l.strip()), "")

        tip = " ".join(tip.split()[:25])
        return tip if tip else "( No usable tip extracted)"
    except Exception as e:
        return f"( AI error: {e})"
