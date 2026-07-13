# ESM 작업 로그

> 모바일·데스크톱 어디서나 볼 수 있는 세션 요약. 상세 이력은 [`vibe_context.md`](./vibe_context.md) 참고.

| 항목 | 값 |
|------|-----|
| Repository | `shaiger79/Code` |
| Branch | `esm-r0-cellru-mapping` (ESM 전용, trafficgen과 분리) |
| Active File | `ESM/esm_r17.py` |
| 로컬 클론 | `C:\Users\shaia\Code` |

---

## 프로젝트 연결
- 실제 작업처는 GitHub **shaiger79/Code**의 **ESM/** 폴더, 브랜치 `esm-r0-cellru-mapping`에 최신 `esm_r17.py`.
- 이 브랜치엔 ESM만 있고 trafficgen 파일 없음 → main과 병합하지 않는 것으로 **프로젝트 분리** 달성.
- Google Drive `G:\내 드라이브\VibeCoding\ESM`는 **백업본** — 작업은 클론 리포에서만.

## 변경 — RU Model ↔ Spec 스마트 매칭 (2026-07-13, commit `6a648af`)
**문제**: ES 절감율 계산 시 CM의 RU Model이 RU/MMU Spec DB의 board-type과 대소문자·`-` 이후 접미어 표기 차이로 매칭 실패 → spec 미매칭(-1) → 절감율 0.

**규칙** (`_rupt_match_ru_spec_row`, 모두 대소문자 무시):
1. **완전일치** — `RF4431t-660` == `rf4431t-660`. 있으면 항상 우선.
2. **family(head) 일치 + 우선순위** — `-` 앞 head가 같은 행만 후보로 모으고, 그중 **전체 모델명**(`660`만이 아니라 `rf4431t-660` 전체) 우선순위가 가장 높은 행 선택.
3. **fallback** — head로 시작하는 첫 값. 셋 다 실패면 미매칭(None).

**우선순위** (앞자리부터): 숫자 > 문자 · 숫자끼리는 큰 값 · 문자끼리는 큰 코드.

| DB 후보 (같은 family) | 선택 |
|---|---|
| 660 / 66d / 600 | **660** |
| 66d / 60d | **66d** |
| aau-999 / rf4431t-660 (query rf4431t-*) | **rf4431t-660** (다른 family 제외) |

**검증**: 18/18 단위 테스트 통과(RF4431t·RRU3971·AAU-Q·XMU·dash 없는 AAU5613 + head-gating). `py_compile` 통과.

## 정리 커밋 (commit `5514b91`)
- `.gitignore` 추가 → `Output/`·`Input/`·`esm_settings.json`·`__pycache__/` 제외.
- 잘못 추적되던 `.pyc` 3개 untrack (로컬 파일은 유지).

---

## 로컬 실행
```powershell
cd C:\Users\shaia\Code\ESM
python .\esm_r17.py
```
- 데이터: `ESM\Input`에 CM/Traffic/Energy Stat/학습데이터 CSV → 자동 인식, 또는 드래그앤드롭/찾기.
- 결과: `ESM\Output\<타임스탬프>\`.
- 패키지: pandas·numpy·tkinterdnd2·scipy 확인됨. scikit-learn은 선택(미설치 시 numpy 폴백).

## VS Code 개발 루프
1. `git switch esm-r0-cellru-mapping` → `git pull`
2. Claude에게 수정 요청 (매번 vibe_context 먼저 읽고 → 수정 → 검증)
3. `python .\ESM\esm_r17.py` 로 로컬 확인
4. `git diff` 로 검토
5. "커밋해줘" / "푸시해줘" — 요청 시에만 실행

**맥락 보존**: `vibe_context.md`(git) · Claude 메모리 · 웹 아티팩트. 새 세션은 "vibe_context.md 읽고 이어서 하자" 한마디로 복원.

## 다음 확인 필요
- 로컬 실데이터로 절감율 정상 계산 확인.
- 같은 head인데 실제로 다른 HW인 family가 있는지.
- "완전일치보다도 항상 정식 표기 우선" 필요 여부.

---
*Last Updated: 2026-07-13 · esm_r17.py v17.10*
