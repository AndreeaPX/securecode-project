from collections import defaultdict
import time

SESSION_STATS = defaultdict(lambda: defaultdict(lambda: [0, 0]))

def log_attention(session_id, face_data_list):
    ts = int(time.time() // 5 * 5)
    stats = SESSION_STATS[session_id][ts]

    for face in face_data_list:
        stats[1] += 1
        if face.get("attentive"):
            stats[0] += 1

def get_session_stats(session_id):
    return SESSION_STATS.get(session_id, {})

def clear_session(session_id):
    SESSION_STATS.pop(session_id, None)
