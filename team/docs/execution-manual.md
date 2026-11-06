# Sea-Info Agent 실행 매뉴얼

## 1. 준비 사항

- Windows PowerShell 기준입니다.
- Python 3.12와 인터넷 연결이 필요합니다. 인터넷은 최초 패키지 설치에 사용합니다.
- 컨테이너 실행에는 Docker가 필요합니다.
- 개발 모드는 SQLite 샘플 데이터만 사용하며 Gemini, Supabase, Redis, Jira, 해양 관측 API에 접속하지 않습니다.

## 2. 최초 로컬 설치

PowerShell에서 프로젝트 폴더로 이동한 뒤 실행합니다.

```powershell
cd C:\KBR\팀프로젝트
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
if (!(Test-Path -LiteralPath .env)) { Copy-Item .env.example .env }
```

이미 가상환경 `.venv`가 있으면 생성 명령은 건너뛰고, 패키지가 바뀐 경우에만 `pip install -r requirements.txt`를 다시 실행합니다. `.env`가 이미 있으면 복사 명령이 기존 값을 덮어쓰지 않습니다.

## 3. 개발 모드 실행

```powershell
$env:SEA_INFO_ENV = "development"
.\.venv\Scripts\python.exe -m streamlit run streamlit_app.py
```

브라우저에서 Streamlit이 출력한 주소를 엽니다. 기본 주소는 보통 `http://localhost:8501`입니다. 서버를 종료하려면 PowerShell 창에서 `Ctrl+C`를 누릅니다.

사이드바의 **화면 권한 미리보기**에서 비회원, 회원 데모, 운영자 데모를 선택할 수 있습니다. 비회원은 공개 화면과 세션 기준 한국 시간 하루 3회 샘플 AI 탐구를 볼 수 있습니다. 이 한도는 데모 브라우저 세션 단위이며 실제 계정 간 서버 제한은 아닙니다. 회원 전용 저장 화면은 회원 데모로 전환해 확인합니다. 운영자 설정은 운영자 데모에서 열립니다.

## 4. 설정 파일

| 파일 | 용도 |
|---|---|
| `config/settings.toml` | 공통 화면, 업로드, AI 한도, 포인트, 저장소 기본값 |
| `config/development.toml` | 개발 샘플 데이터와 mock 분석 모드 |
| `config/production.toml` | 운영 환경 선택값. 실제 외부 서비스 연결을 수행하지 않음 |
| `.env` | 로컬 비밀값 및 환경변수 재정의 |
| `.env.example` | 설정 키 이름 예시. 실제 비밀값은 넣지 않음 |
| `.streamlit/config.toml` | Streamlit 테마와 업로드 크기 설정 |

`SEA_INFO_ENV`는 `development` 또는 `production`으로 선택합니다. 환경변수 값은 TOML 설정값보다 우선합니다. 환경변수는 현재 PowerShell 창에만 지정됩니다. 새 창에서는 다시 지정해야 합니다.

로컬 개발에서는 `.env`를 수정하거나 PowerShell에서 환경변수를 지정합니다. 예를 들어:

```powershell
$env:SEA_INFO_ENV = "development"
$env:SQLITE_PATH = "data/sea_info.sqlite3"
```

비밀값이 필요한 외부 연동은 이 프로젝트에서 아직 구현되지 않았습니다. 키를 설정해도 Gemini·Supabase·Redis·Jira·해양 API 호출이 시작되지 않습니다. `production` 프로필에서는 데모 로그인을 끄며, 실제 인증 연결 전에는 회원 기능을 운영 배포에 사용하지 마세요.

## 5. 데이터 위치와 초기화

기본 데이터베이스는 `data/sea_info.sqlite3`입니다. 첫 화면을 열 때 데이터베이스와 샘플 관찰이 생성됩니다. 게시물, 댓글, 제보, 게임 결과, 동의 기록은 SQLite에 저장됩니다.

다른 위치를 쓰려면 `SQLITE_PATH`를 절대 경로 또는 프로젝트 기준 상대 경로로 지정합니다.

```powershell
$env:SQLITE_PATH = "D:\SeaInfoData\sea_info.sqlite3"
.\.venv\Scripts\python.exe -m streamlit run streamlit_app.py
```

데이터베이스 파일을 삭제하면 저장된 로컬 관찰·댓글·제보·게임 기록이 사라지고, 다음 실행에서 샘플 관찰 데이터가 다시 만들어집니다. 삭제 전에 필요한 데이터를 백업합니다.

## 6. Docker 실행

프로젝트 폴더에서 이미지 생성과 실행을 합니다.

```powershell
docker build -t sea-info-agent .
docker run --rm -p 8501:8501 -e SEA_INFO_ENV=development sea-info-agent
```

브라우저에서 `http://localhost:8501`을 엽니다. 종료는 `Ctrl+C`입니다.

컨테이너를 지워도 데이터베이스가 남도록 하려면 영구 폴더를 마운트하고 경로를 지정합니다.

```powershell
New-Item -ItemType Directory -Force -Path .\runtime-data | Out-Null
docker run --rm -p 8501:8501 -e SEA_INFO_ENV=development -e SQLITE_PATH=/app/runtime-data/sea_info.sqlite3 -v "${PWD}\runtime-data:/app/runtime-data" sea-info-agent
```

운영 배포에서는 호스팅 플랫폼의 환경변수/Secret 저장소를 사용하고, SQLite 파일을 보존할 영구 볼륨을 연결합니다. `.env` 파일은 Docker 이미지에 포함되지 않습니다.

## 7. 자주 확인할 항목

- **`streamlit` 명령을 찾을 수 없음:** 활성 가상환경의 실행 파일을 사용합니다: `.\.venv\Scripts\python.exe -m streamlit run streamlit_app.py`.
- **8501 포트가 이미 사용 중:** `.\.venv\Scripts\python.exe -m streamlit run streamlit_app.py --server.port 8502`로 다른 포트를 지정합니다.
- **설정 변경이 화면에 반영되지 않음:** 실행 중인 서버를 `Ctrl+C`로 종료한 뒤 다시 실행합니다. TOML을 바꾼 경우 새 앱 세션을 시작합니다.
- **이미지 업로드가 거부됨:** JPG, JPEG, PNG, WebP 형식과 10MB 제한을 확인합니다. 실제 이미지 파일인지도 검사합니다.
- **운영자 화면이 보이지 않음:** 개발 모드에서 사이드바의 화면 권한 미리보기를 운영자 데모로 바꿉니다.
- **운영 설정인데 로그인/분석이 안 됨:** 이 프로젝트의 실제 인증 및 Gemini 연동은 미구현 상태입니다. 운영 모드는 데모 기능을 비활성화합니다.

## 8. 범위와 보안

로그인·회원가입은 데모 세션만 만들고 계정을 인증하지 않습니다. AI 결과, 뉴스, 운영 통계는 예시 데이터입니다. 업로드 사진은 EXIF를 제거하고 축소한 뒤 동의가 확인된 관찰 게시물에 한해 로컬 SQLite에 저장합니다. 얼굴이나 개인정보가 보이는 사진은 업로드하지 마세요.
