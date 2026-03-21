---
argument-hint: "[youtube video url]"
description: "Youtube 영상의 트랜스크립트를 입력받아 번역, 정리해서 obsidian 문서로 저장"
color: yellow
---

# summarize youtube - $ARGUMENTS

제공된 YouTube URL의 메타데이터/자막을 기반으로 Obsidian 요약 문서를 생성합니다.

## 필수 규칙

- `~/.claude/docs/OBSIDIAN-RULES.md`를 반드시 준수
- `created_at` frontmatter 필드 **필수** (`YYYY-MM-DD HH:mm`)
- YAML이 깨지지 않도록 문자열 필드는 항상 큰따옴표(`"`) 사용
  - `id`, `aliases`, `author`, `created_at`, `source`, `article_id`
- 제목/별칭에 `: # [ ] { } ' "` 포함 가능하므로 quoted scalar 강제
- 저장 전 frontmatter YAML 파싱 검증 필수

## 작업 프로세스

1. `yt` CLI로 메타데이터/자막 추출
2. 내용 번역/요약 (기술 용어 첫 등장 시 영문 병기)
3. hierarchical tag 생성
4. 파일명 생성: `{영문제목} - {한국어번역}.md`
5. 문서 저장
6. YAML 검증

```bash
ruby - <<'RB'
path = "생성한_파일.md"
text = File.read(path, encoding: "utf-8")
parts = text.split("---", 3)
raise "frontmatter 구분자(---)가 올바르지 않습니다." if parts.length < 3

require "yaml"
YAML.safe_load(parts[1], permitted_classes: [Time], aliases: true)
puts "YAML frontmatter OK"
RB
```

## yaml frontmatter 예시

```yaml
id: "The Simplest Way to Make Your Architecture Testable and Reproducible (Works Every Time)"
aliases: "아키텍처를 테스트 가능하고 재현 가능하게 만드는 가장 단순한 방법"
tags:
  - architecture/evolutionary-architecture/deterministic-systems
  - architecture/testability/reproducibility
  - architecture/patterns/deterministic-core
author: "modern-software-engineering"
created_at: "2026-03-05 09:01"
related: []
source: "https://www.youtube.com/watch?v=uHatwKrYY_c"
```

## 결과 문서 구조

- `## Highlights`
- `## Detailed Summary`
- `## Conclusion and Personal Views`
- 불확실한 부분은 명시적으로 표시
- 원문 코드 예제가 있으면 누락 없이 포함

