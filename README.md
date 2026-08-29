# 3.8 아카이브 (가칭)

1960년 대전에서 일어난 학생운동 "3.8민주의거"의 역사를 청소년과 일반 시민에게
쉽고 흥미롭게 전달하는 웹 서비스입니다.

## 프로젝트 구조

```
index.html         메인 페이지 (히어로 + 페이지 이동 카드)
timeline.html       연표 페이지 (3.8~3.10 타임라인 + 4.19혁명과의 관계)
gallery.html         사진·영상 갤러리 (라이트박스 + 유튜브 임베드)
chat.html         AI Q&A 챗봇 페이지
css/style.css        전체 공통 스타일시트
js/main.js         전체 공통 스크립트 (내비게이션, 라이트박스, 챗봇 로직)
api/ask.py         AI Q&A 백엔드 (Vercel Serverless Function, Python)
requirements.txt      Python 의존성 (anthropic SDK)
vercel.json         Vercel 함수 설정 (api/ask.py 타임아웃 30초)
```

## 로컬 실행

프론트엔드는 순수 HTML/CSS/JS이므로 별도 빌드 없이 정적 파일 서버로 열면 됩니다.

```bash
# 프로젝트 폴더에서
npx serve .
# 또는 VSCode의 Live Server 확장 등 사용
```

단, `chat.html`의 AI 응답 기능은 `api/ask.py`가 함께 떠 있어야 동작합니다.
로컬에서 API까지 함께 테스트하려면 Vercel CLI를 사용하세요.

```bash
npm install -g vercel
vercel dev
```

## 배포 (Vercel)

1. 이 저장소를 GitHub에 올리고 Vercel에서 Import 합니다.
2. Vercel 프로젝트 설정 > Environment Variables에 아래 값을 등록합니다.

   | Key | 값 |
   | --- | --- |
   | `ANTHROPIC_API_KEY` | Anthropic 콘솔에서 발급받은 API 키 |

3. Deploy를 실행하면 `api/ask.py`가 `/api/ask` 서버리스 함수로 자동 배포됩니다.

## AI 챗봇 (chat.html + api/ask.py)

- 사용자가 질문을 입력하면 `js/main.js`가 `/api/ask`로 `POST` 요청을 보냅니다.
- `api/ask.py`는 Anthropic API(`claude-opus-5`)에 시스템 프롬프트와 함께 질문을 전달하고,
  답변을 `{ "answer": "..." }` 형태로 반환합니다.
- 실패 처리
  1. 빈 질문 입력 시: 서버에 요청을 보내지 않고 "질문을 입력해주세요" 안내
  2. API 오류(4xx/5xx) 시: "오류가 발생했습니다. 잠시 후 다시 시도해주세요" 안내
  3. 응답을 기다리는 동안: "답변 생성 중..." 로딩 버블 표시

## 갤러리 이미지/영상 교체하기

- `gallery.html`의 사진은 현재 자료 준비 전이라 SVG 플레이스홀더로 채워져 있습니다.
  실제 사진이 준비되면 각 `<img src="...">`를 실제 이미지 경로로 교체하세요.
- 영상은 `REPLACE_WITH_VIDEO_ID_1` / `REPLACE_WITH_VIDEO_ID_2` 부분을
  실제 유튜브 영상 ID로 교체하세요.

## 디자인 톤

역사·교육 콘텐츠에 어울리는 차분한 네이비 + 앤틱 골드 톤을 사용했으며,
`css/style.css`의 `:root` 변수만 수정하면 전체 색상 톤을 손쉽게 바꿀 수 있습니다.
