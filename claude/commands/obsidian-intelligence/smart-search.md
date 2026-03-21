---
description: "시맨틱/하이브리드 검색으로 vault 문서 탐색"
argument-hint: "<검색어>"
---

# Smart Search - $ARGUMENTS

Obsidian vault에서 시맨틱 검색을 수행하여 관련 문서를 찾습니다.

## 필수 규칙

- 모든 파일 경로는 **절대경로**로 출력하세요.

## 작업 프로세스

1. `search-documents` 도구를 호출합니다:
   - `query`: "$ARGUMENTS"
   - `searchType`: "HYBRID" (시맨틱 + 키워드 결합으로 최적 결과)
   - `topK`: 15
2. 검색 결과를 아래 형식으로 정리합니다.
3. 결과가 부족하면 `searchType`을 "SEMANTIC"으로 변경하여 재검색합니다.

## 출력 형식

```
## 검색 결과: "$ARGUMENTS"

### 상위 결과
1. **문서 제목** (유사도: 0.xx)
   - 경로: /absolute/path/to/file.md
   - 태그: #tag1 #tag2
   - 스니펫: 관련 내용 미리보기...

### 요약
- 총 N건의 관련 문서를 찾았습니다.
- 가장 관련성 높은 문서: [제목]
- 주요 관련 태그: #tag1, #tag2, #tag3
```
