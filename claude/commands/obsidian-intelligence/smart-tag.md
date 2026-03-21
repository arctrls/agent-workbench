---
description: "임베딩 기반 시맨틱 태그 자동 생성 및 적용"
argument-hint: "<파일 또는 폴더 절대경로>"
---

# Smart Tag - $ARGUMENTS

지정된 파일 또는 폴더에 시맨틱 분석 기반 태그를 자동으로 생성/적용합니다.

## 필수 규칙

- **반드시 `~/.claude/docs/OBSIDIAN-RULES.md` 규칙을 준수하세요.**
- 모든 파일 경로는 **절대경로**로 전달하세요.
- `$ARGUMENTS`가 파일이면 `tag-document`, 폴더이면 `batch-tag-folder`를 사용합니다.

## 작업 프로세스

### 파일인 경우

1. `tag-document` 도구를 `dryRun: true`로 먼저 호출하여 미리보기합니다.
2. 생성된 태그를 사용자에게 보여주고 확인을 받습니다.
3. 확인 후 `tag-document`를 `dryRun: false`로 호출하여 적용합니다.

### 폴더인 경우

1. `batch-tag-folder` 도구를 `dryRun: true`, `recursive: true`로 먼저 호출합니다.
2. 영향받는 파일 목록과 생성될 태그를 요약하여 사용자에게 보여줍니다.
3. 확인 후 `batch-tag-folder`를 `dryRun: false`로 호출하여 적용합니다.

## 출력 형식

```
## 태그 미리보기: $ARGUMENTS

### [파일명]
- 기존 태그: #existing/tag1, #existing/tag2
- 생성 태그: #new/tag1, #new/tag2, #new/tag3
- 카테고리: Topic(N), Document Type(N), Patterns(N)

### 요약
- 대상 파일: N개
- 신규 태그: N개
- [적용하시겠습니까?]
```
