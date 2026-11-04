# 오늘의 할 일

## Windows: Python 설치 없이 실행

GitHub의 Actions → Windows executable → 성공한 실행 → Artifacts에서
`SimpleTodo-Windows`를 다운로드하고 ZIP 압축을 푼 뒤 `SimpleTodo.exe`를 실행하세요.
브라우저가 자동으로 열립니다. 실행 중 콘솔 창을 유지하고 종료할 때 창을 닫으세요.
할 일은 `%LOCALAPPDATA%\SimpleTodo\todos.db`에 보관됩니다.
실행 파일은 코드 서명이 없으므로 Windows가 경고를 표시할 수 있습니다.

## Python으로 개발

Python 3.10 이상으로 실행하는 개인용 할 일 웹앱입니다. 외부 패키지 설치가 필요 없습니다.

```bash
cd /workspace/codex_test
python3 app.py
```

자신의 컴퓨터에서 실행할 때 브라우저로 `http://127.0.0.1:8000`에 접속합니다.
종료는 Ctrl+C입니다. 할 일은 `data/todos.db` SQLite 파일에 저장되며 재시작해도 유지됩니다.
`--port 8001`, `--db /원하는/경로/todos.db`로 설정할 수 있습니다.

할 일 추가(최대 200자), 완료/취소, 삭제, 전체/진행 중/완료 필터를 제공합니다.
로그인 없는 개인용 로컬 개발 앱이므로 공개 서버 배포에는 인증 등 추가 구성이 필요합니다.

테스트:

```bash
python3 -m unittest discover -s tests -v
```
