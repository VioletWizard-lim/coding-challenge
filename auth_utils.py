"""비밀번호 확인·암호화 (V2와 같은 bcrypt `$2a$10$` 형식)."""
import bcrypt

SENSITIVE_KEYS = ("password", "password_hash")


def _pw_bytes(password: str) -> bytes:
    # bcrypt는 앞 72바이트만 씀. 길면 잘라서 다른 bcrypt 구현과 같은 결과가 나오게 함
    return password.encode("utf-8")[:72]


def check_password(user_row: dict, password: str) -> bool:
    """password_hash(bcrypt)가 있으면 그걸로 확인. 없을 때만 예전 평문 password와 비교."""
    if not password:
        return False
    hashed = user_row.get("password_hash")
    if hashed:
        try:
            return bcrypt.checkpw(_pw_bytes(password), hashed.encode("utf-8"))
        except ValueError:  # 형식이 잘못된 해시
            return False
    legacy = user_row.get("password")
    return bool(legacy) and legacy == password


def hash_password(password: str) -> str:
    """기존 계정과 같은 형식($2a$, 강도 10)으로 암호화."""
    return bcrypt.hashpw(_pw_bytes(password), bcrypt.gensalt(rounds=10, prefix=b"2a")).decode("utf-8")


def strip_secrets(user_row: dict) -> dict:
    """세션에 보관할 사용자 정보에서 비밀번호 관련 값을 뺌."""
    return {k: v for k, v in user_row.items() if k not in SENSITIVE_KEYS}
