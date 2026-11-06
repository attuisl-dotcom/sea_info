# 설정 및 배포

환경별 비밀이 아닌 설정은 `config/settings.toml`과 프로필 파일에 둡니다.

- `config/development.toml`: 샘플 데이터와 mock 모드
- `config/production.toml`: 운영 모드 선택, 외부 연동 사용 예정 표시
- `.env`: 로컬 비밀값. 저장소에 커밋하지 않습니다.
- 배포 Secret/Environment Variables: GEMINI, Supabase, Redis, Jira 자격 정보
- `.streamlit/config.toml`: Streamlit 테마 및 서버 기본값

`SEA_INFO_ENV=development` 또는 `SEA_INFO_ENV=production`으로 프로필을 고릅니다. 환경변수는 TOML 값보다 우선합니다. 프로덕션 Secret 예시는 `.env.example`에 이름만 나열되어 있고 값은 비어 있습니다.

## 로컬 실행

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
if (!(Test-Path -LiteralPath .env)) { Copy-Item .env.example .env }
.\.venv\Scripts\python.exe -m streamlit run streamlit_app.py
```

개발 프로필은 `streamlit run`만으로 샘플 게시물과 대시보드를 표시합니다. 데이터베이스 파일은 첫 실행 시 `data/sea_info.sqlite3`에 생성됩니다.

## 컨테이너

```sh
docker build -t sea-info-agent .
docker run --rm -p 8501:8501 -e SEA_INFO_ENV=development sea-info-agent
```

영구 저장소가 필요한 경우 컨테이너 외부 볼륨에 SQLite 파일을 두고 `SQLITE_PATH`로 지정합니다. 배포 플랫폼의 secret manager에 자격 값을 설정합니다.

## 현재 연동 단계

Production 프로필은 실제 인증/Gemini/Jira 연결 완료 상태를 뜻하지 않습니다. 이 구현은 화면별 정의와 샘플 동작을 제공하며, 운영 인증·외부 API·분산 rate limit·캐시 서버를 연결하기 전에는 운영 배포에 사용할 수 없습니다. 운영 모드에서는 데모 로그인과 mock 분석을 막습니다.
