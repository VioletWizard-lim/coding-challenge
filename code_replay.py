"""코드 작성 과정 기록(학생용 에디터)과 재생(교사용) 헬퍼."""
import json
import pathlib

import streamlit.components.v1 as components

_BASE = pathlib.Path(__file__).parent / "components" / "code_replay"
_recorder = components.declare_component("code_recorder", path=str(_BASE / "recorder"))
_REPLAY_HTML = (_BASE / "replay.html").read_text(encoding="utf-8")


def code_recorder(storage_key: str, initial_code: str = "", key: str | None = None):
    """학생용 에디터. 제출 버튼을 누르면 {code, init, log, nonce}를 돌려줌 (그 전엔 None)."""
    return _recorder(storage_key=storage_key, initial_code=initial_code, key=key, default=None)


def summarize_log(log) -> dict | None:
    """작성 기록 요약 (replay.html의 통계와 같은 기준). 기록이 없으면 None.

    active_ms: 이벤트 간격이 30초 미만인 구간만 더한 실제 작업 시간
    typed / pasted: 직접 입력·붙여넣기한 글자 수
    away_count: 창 이탈 횟수
    """
    entries = [e for e in (log or []) if isinstance(e, list) and e and isinstance(e[0], (int, float))]
    if not entries:
        return None
    active = sum(g for g in (b[0] - a[0] for a, b in zip(entries, entries[1:])) if g < 30000)
    edits = [e for e in entries if len(e) > 6 and isinstance(e[6], str)]
    typed = sum(len(e[6]) for e in edits if e[1] == "i")
    pasted = sum(len(e[6]) for e in edits if e[1] == "p")
    away, blurred = 0, False
    for e in entries:
        if e[1] == "b" and not blurred:
            away += 1
            blurred = True
        elif e[1] == "f":
            blurred = False
    return {"active_ms": active, "typed": typed, "pasted": pasted, "away_count": away}


def show_replay(row: dict, height: int = 520):
    """교사용 재생기. row에는 code, init_code, edit_log가 있어야 함."""
    data = {"init": row.get("init_code") or "", "code": row.get("code") or "", "log": row.get("edit_log") or []}
    payload = json.dumps(data, ensure_ascii=False).replace("</", "<\\/")
    components.html(_REPLAY_HTML.replace("__DATA__", payload), height=height, scrolling=True)
