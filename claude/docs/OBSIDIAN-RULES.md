# Obsidian 문서 작성 규칙

이 문서는 모든 Obsidian 관련 명령어에서 **반드시** 준수해야 하는 규칙을 정의합니다.

## 필수 Frontmatter 규칙

### created_at 필드 (필수)

**모든 Obsidian 문서에는 반드시 `created_at` frontmatter 필드가 포함되어야 합니다.**

```yaml
---
created_at: 2026-01-11
---
```

#### 왜 필수인가?

- iCloud 동기화 시 파일 시스템의 생성일(`file.cday`)이 변경될 수 있음
- Dataview 쿼리에서 `date(created_at)`를 사용하여 안정적인 생성일 추적 가능
- 파일 수정 시에도 원래 생성일 유지

#### 형식

- **날짜만**: `created_at: 2026-01-11`
- **날짜+시간**: `created_at: 2026-01-11 14:30`

### 체크리스트

문서 생성 시 다음을 확인하세요:

- [ ] `created_at` 필드가 frontmatter에 포함되어 있는가?
- [ ] 날짜 형식이 `YYYY-MM-DD` 또는 `YYYY-MM-DD HH:mm`인가?
- [ ] 실제 문서 생성 시점의 날짜인가?

## Frontmatter 템플릿

### 최소 필수 템플릿

```yaml
---
created_at: {{date}}
---
```

### 권장 템플릿

```yaml
---
created_at: {{date}}
tags: []
---
```

### 아티클 요약 템플릿

```yaml
---
id: 원본 제목
article_id: hash_title-words
aliases: 한국어 번역 제목
tags: []
author: author-name
created_at: 2026-01-11 14:30
related: []
source: https://example.com/article
---
```

## Dataview 쿼리 예시

### 특정 날짜에 생성된 문서 목록

```dataview
LIST WHERE date(created_at) = this.file.day AND file.path != this.file.path SORT file.ctime desc
```

### 최근 7일간 생성된 문서

```dataview
LIST WHERE date(created_at) >= date(today) - dur(7 days) SORT created_at desc
```

## 명령어별 적용

모든 Obsidian 관련 명령어는 이 규칙을 준수해야 합니다:

- `/obsidian:summarize-article` - 아티클 요약 시 `created_at` 필수
- `/obsidian:summarize-youtube` - YouTube 요약 시 `created_at` 필수
- `/obsidian:add-tag` - 태그 추가 시 `created_at` 없으면 추가
- `/obsidian:move-file` - 파일 이동 시 `created_at` 보존
- 기타 모든 문서 생성/수정 명령어
