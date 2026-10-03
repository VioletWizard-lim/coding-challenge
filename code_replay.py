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


def show_replay(row: dict, height: int = 520):
    """교사용 재생기. row에는 code, init_code, edit_log가 있어야 함."""
    data = {"init": row.get("init_code") or "", "code": row.get("code") or "", "log": row.get("edit_log") or []}
    payload = json.dumps(data, ensure_ascii=False).replace("</", "<\\/")
    components.html(_REPLAY_HTML.replace("__DATA__", payload), height=height, scrolling=True)
