# Sea-Info Agent

화면별 상세 기능 정의서 v2.5를 기준으로 구성한 Streamlit 데모입니다. 비회원은 홈·생물 탐구(세션의 한국 시간 기준 하루 3회 데모 한도)·공개 게시판·게임·뉴스·제보 화면을 둘러볼 수 있습니다. 게시물 작성·수족관·개인 대시보드·프로필은 회원 전용이며, 운영자 화면은 운영자 역할에서만 표시합니다.

## 실행

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
if (!(Test-Path -LiteralPath .env)) { Copy-Item .env.example .env }
.\.venv\Scripts\python.exe -m streamlit run streamlit_app.py
```

기본 개발 프로필은 샘플 데이터와 mock 분석을 사용하며, 외부 서비스에 요청을 보내지 않습니다. 사이드바의 권한 미리보기에서 비회원/회원/운영자 화면을 바꿀 수 있습니다. 로그인 화면은 데모 세션만 만듭니다.

## 환경 설정

- 공통 값: [`config/settings.toml`](config/settings.toml)
- 개발: [`config/development.toml`](config/development.toml)
- 운영: [`config/production.toml`](config/production.toml)
- 비밀값 이름: [`.env.example`](.env.example)
- Sea-Info 테마: [`.streamlit/config.toml`](.streamlit/config.toml)
- 배포 절차: [`docs/deployment.md`](docs/deployment.md)
- 단계별 실행: [`docs/execution-manual.md`](docs/execution-manual.md)

`SEA_INFO_ENV=development|production`으로 설정 프로필을 선택합니다. 비밀값은 TOML 파일이나 코드에 넣지 않고 환경변수 또는 배포 플랫폼의 Secret 설정에 보관합니다. 실제 키를 `.env.example`에 넣지 마세요.

## 기능

- PDF의 SCR-01~SCR-18, ADM-01~ADM-03 화면 경로와 상호작용
- 사진·카메라 입력, 파일 검사, Pillow 리사이즈, EXIF 제거 및 Gemini 동의 흐름
- SQLite 관찰·댓글·공감·제보·AI 로그·동의 이력·게임 기록
- 게시물 공개/비공개, 위치 노출, 사진 공개, 운영자 사진 활용 동의 분리
- 게시 성공 시 종 중복을 방지하며 개인 수족관에 자동 추가
- 작성자 수정·삭제 권한과 운영자 관리 화면

화면 목록과 구현 대응은 [`docs/screen-design.md`](docs/screen-design.md), SQLite DDL은 [`data/schema.sql`](data/schema.sql)에 있습니다. 실행 시 데이터베이스가 없으면 샘플 관찰을 자동으로 채웁니다.

## 연결 범위

PDF의 화면 시안에 미구현으로 표기된 인증, 실제 Gemini 요청, GPS 자동 추출, 해양 관측 API, Jira, 뉴스 수집은 이 데모에서도 외부 연결하지 않습니다. 분석·뉴스·운영 통계는 샘플 결과이고, 로그인은 브라우저 세션 데모입니다. 운영 설정은 파일로 분리해 두었으며, `production` 프로필은 실제 통합을 완료한 상태를 의미하지 않습니다.

업로드 이미지의 EXIF를 제거하고 크기를 줄여 SQLite에 저장하지만, 공개 사진 저장은 게시물 공개 동의가 확인된 경우에만 수행합니다. 사람 얼굴이나 개인정보가 보이는 사진은 올리지 마세요.

## 컨테이너

```sh
docker build -t sea-info-agent .
docker run --rm -p 8501:8501 -e SEA_INFO_ENV=development sea-info-agent
```

영구 저장이 필요하면 `SQLITE_PATH`를 영구 볼륨 경로로 지정하세요.
