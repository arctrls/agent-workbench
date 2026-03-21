---
description: "관련 문서 탐색 및 '관련 문서' 섹션 자동 업데이트"
argument-hint: "<파일 절대경로>"
---

# Link Related - $ARGUMENTS

지정된 문서와 시맨틱으로 유사한 문서를 탐색하고, `## 관련 문서` 섹션을 업데이트합니다.

## 필수 규칙

- 모든 파일 경로는 **절대경로**로 전달하세요.

## 작업 프로세스

1. `find-related-documents` 도구를 호출합니다:
   - `filePath`: "$ARGUMENTS"
   - `topK`: 10
2. 관련 문서 목록을 사용자에게 보여줍니다.
3. 사용자 확인 후 `update-related-section` 도구를 호출하여 문서에 반영합니다:
   - `filePath`: "$ARGUMENTS"
   - `topK`: 5 (또는 사용자가 지정한 수)

## 출력 형식

```
## 관련 문서 탐색 결과: [문서 제목]

### 유사 문서 (상위 10건)
1. **문서 제목** (유사도: 0.xx)
   - 경로: /absolute/path/to/file.md
   - 태그: #tag1 #tag2
2. ...

### 반영 안내
- 상위 5건을 `## 관련 문서` 섹션에 위키링크로 추가합니다.
- [반영하시겠습니까?]
```
