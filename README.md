# 🚀 파이썬 코딩 챌린지

Supabase + Streamlit으로 구현한 코딩 챌린지 플랫폼입니다.

## 📁 파일 구조

```
coding_challenge/
├── app.py                  ← 메인 (로그인)
├── pages/
│   ├── student.py          ← 학생 화면
│   ├── teacher.py          ← 교사 채점 화면
│   └── leaderboard.py      ← 실시간 랭킹
├── .streamlit/
│   └── secrets.toml        ← Supabase 키 (GitHub에 올리지 마세요!)
├── requirements.txt
└── supabase_setup.sql      ← DB 초기 설정
```

## ⚙️ 설치 및 배포

### 1. Supabase 설정
1. [supabase.com](https://supabase.com) 에서 새 프로젝트 생성
2. SQL Editor에서 `supabase_setup.sql` 내용 실행
3. Settings → API 에서 `URL`과 `anon key` 복사

### 2. secrets.toml 설정
`.streamlit/secrets.toml` 파일에 Supabase 정보 입력:
```toml
[supabase]
url = "https://xxxxxxxxxxx.supabase.co"
key = "eyJxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
```

### 3. GitHub 업로드
```bash
git init
git add .
git commit -m "initial commit"
git remote add origin https://github.com/your-id/coding-challenge.git
git push -u origin main
```

> ⚠️ `.streamlit/secrets.toml`은 `.gitignore`에 추가하세요!

### 4. Streamlit Cloud 배포
1. [streamlit.io](https://streamlit.io) 로그인 (GitHub 연동)
2. "New app" → GitHub 레포 선택
3. Main file: `app.py`
4. Advanced settings → Secrets에 secrets.toml 내용 붙여넣기
5. Deploy!

## 🎓 사용법

| 역할 | 기능 |
|------|------|
| 학생 | 로그인 → 문제 선택 → 코드 제출 → 내 점수 확인 |
| 교사 | 로그인 → 제출 목록 조회 → 채점 → 삭제 |
| 전체 | 랭킹 페이지 (로그인 불필요) |

## 📊 채점 기준

| 영역 | 배점 |
|------|------|
| 기능 | 40점 |
| 이해도 | 30점 |
| 도전 | 20점 |
| 제출시간 | 10점 |
