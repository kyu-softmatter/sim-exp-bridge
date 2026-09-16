# 이 세션(agentic-microscope, branch `version2`)에 붙여넣을 요청문

---

## 목적

이 리포(실험/현미경 에이전트)와 `~/Desktop/Brownian-Dynamics-Agent`(시뮬레이션
에이전트)를 **양방향으로** 잇는 작업이다. 목표는 두 가지 흐름을 모두 성립시키는
것이다.

- **실험 → 시뮬**: 이 리포의 plan/결과를 근거로 BD가 시뮬레이션 계획을 세운다.
- **시뮬 → 실험**: BD의 plan/결과를 근거로 이 리포가 실험 계획을 세운다.

핵심 원칙 하나만 기억하면 된다. **숫자를 운반하는 게 아니라 질문을 넘긴다.**
상대의 plan을 복사하거나 번역하지 않는다. 상대가 보낸 것은 "주장 + 답을 낼 단일
관측량 + 필요 정밀도 + 계를 정의하는 primitive + 가정 선언"이고, **이 리포의 plan은
그것을 입력으로 삼아 이 리포의 게이트를 처음부터 다시 통과해서** 나와야 한다.
상대가 도출한 파생값은 비구속 참조값이며, **먼저 직접 도출한 다음에** 비교한다.

두 계가 동일한 물리계일 필요는 없다. SI 값이 달라도 무차원 영역이 겹치고 가정이
선언되어 있으면 충분하고, 그게 오히려 더 강한 증거다. 막아야 하는 건 **선언되지
않은 가정 차이**다 — 그건 일치처럼 보이지만 일치가 아니다.

## 먼저 읽을 것

공유 저장소가 이미 있다. **먼저 이것부터 읽고, 코드를 건드리기 전에 검토 결과를
보고할 것.**

    BRIDGE=~/Desktop/sim-exp-bridge

1. `$BRIDGE/README.md` — 와이어 규칙 W1–W3, evidence→tier 매핑표 T1, 검증기 7규칙,
   파일 배치, 그리고 "무엇이 건너가고 무엇이 안 건너가는지"
2. `$BRIDGE/threads/trap-stiffness-recovery/r1/ask_simulation.{md,json}` — 이 리포가
   **보내는** 문서의 예시. 실제로 `kb/plans/2026-09-15-drag-calibration-stiffness-vs-size.md`
   에서 뽑은 것이고 숫자는 전부 그 파일에서 복사한 것이다.
3. `$BRIDGE/threads/trap-stiffness-recovery/r2/ask_experiment.{md,json}` — 이 리포가
   **받는** 문서의 예시. BD가 `runs/trap-2d-5um__a5ef4f45d589`에서 낸 것이다.
4. `$BRIDGE/threads/trap-stiffness-recovery/r2/kb_entry_for_am.md` — 받은 것이 이
   리포의 KB에 착지하는 형태.
5. `$BRIDGE/schema/*.json` — 스키마 4개.

이 문서들은 **명세이자 예시**다. 새로 설계하지 말고 이 형태를 따르되, 이 리포의
규칙과 충돌하는 지점이 있으면 구현 전에 지적할 것.

## 이 세션의 범위

`~/Desktop/agentic-microscope`, 브랜치 `version2`. **BD 리포의 파일은 읽기만 하고
절대 수정하지 않는다.** BD의 `CLAUDE.md`도 로드하지 않는다 — 이 리포는 SAFETY.md
416줄과 하드룰 5개로 부팅하고 BD는 자기 원칙 10개가 있어서, 섞으면 양쪽을 신뢰할 수
있게 만드는 거부 동작이 서로 희석된다.

## 와이어 규칙 — 이 리포에 적용되는 부분

**W1 · 무차원화는 하지 않는다.** 무차원수 계산 코드를 이 리포에 만들지 말 것.
`k d^2/kT` 같은 것은 BD가 `bdbot/nondim.py`·`scales.py`로 양방향 다 처리한다.
이 리포는 **차원 있는 양을 내보내고 차원 있는 범위를 받는다.** 받는
`ask_experiment.requirements[]`는 이미 SI 범위(`T_obs >= 32.3 s`,
`f_s >= 620 Hz`, `epsilon <= 7.6 nm`)이므로 게이트가 그대로 검사할 수 있다.
같이 오는 `regime[]`은 사람이 역변환을 감사하기 위한 것이고 기계 검사에 구속력이
없다.

**W2 · 측정된 단위 그대로 보낸다.** SI 정규화를 직접 하지 말 것 — 변환은 단위
라이브러리가 없는 쪽에서 오류가 생기는 지점이다. `pN/um`, `mPa*s`, `g/cm^3`을
그대로 싣는다. ASCII만 쓸 것: `um`이고 `µm`이 아니다 (검증기 R2가 거부한다).

**W3 · 합성량이 아니라 primitive를 보낸다.** `d`, `eta`, `T`, `k_t`를 보내고
`gamma`, `tau_k`, `f_c`는 보내지 않는다. `3*pi*eta*d`와 `6*pi*eta*a`는 같은 식이라
곱을 보내는 순간 아무도 거짓말하지 않은 채로 2배가 들어간다. 파생값은
`reference_only`에 **비구속**으로만 싣는다. 검증기 R3가 이걸 강제한다.

**모든 숫자에 `evidence`를 붙인다** (`measured|handbook|computed|assumed`). BD가
그걸로 tier를 유도한다. 측정 안 한 값을 `measured`로 보내면 BD가 tier 0으로
승계한다 — 예시 r1에서 `T = 293.15 K`를 `assumed`로 보내고 precondition P3을
인용하는 이유가 그것이다.

## 파일 소유권 — 충돌 없이 같은 저장소를 쓰는 방법

라운드마다 쓰는 쪽이 정해져 있으므로 두 세션이 같은 파일을 건드리지 않는다.

| 파일 | 쓰는 쪽 |
|---|---|
| `threads/<thread>/r<N>/ask_simulation.{json,md}` | **이 세션** (홀수 라운드) |
| `threads/<thread>/r<N>/ask_experiment.{json,md}` | BD 세션 (짝수 라운드) |
| `threads/<thread>/r<N>/kb_entry_for_am.md` | **이 세션** — 받은 것을 수입한 기록 |
| `threads/<thread>/r<N>/kb_entry_for_bd.md` | BD 세션 |
| `hashes.json` | 각자 **자기 리포 접두사(`am:`)의 항목만** |
| `schema/`, `validate.py`, `README.md` | 변경 제안은 하되 합의 전 수정 금지 |

스레드 경로는 `<thread-id>/r<N>`이다. 제목으로 잇지 않는다 — 3라운드쯤에서 제목이
갈리거나 겹치고, 왕복 루프의 가장 흔한 실패는 각 단계가 틀리는 게 아니라 3번 돌고
나니 원래 질문이 아닌 것이다.

## 저장소 사용법 (git)

공유 저장소는 **private git 리포**이고 두 세션이 같은 리모트를 쓴다.

    https://github.com/kyu-softmatter/sim-exp-bridge
    로컬: ~/Desktop/sim-exp-bridge   (브랜치 main, 이미 clone 되어 있음)

- **쓰기 전에 항상 `git pull --rebase`.** 상대 세션이 라운드를 올려뒀을 수 있다.
- **커밋은 위 소유권 표에서 자기 것인 파일만.** 한 라운드 = 한 커밋으로 묶고,
  메시지에 스레드와 라운드를 적는다 (`r2: BD answers f_c to 1.17 %, refuses h0`).
- **`git push --force`는 쓰지 않는다.** 이력이 라운드 기록이다.
- **자기 소유가 아닌 파일에서 충돌이 나면 멈추고 보고할 것.** 그건 병합 문제가
  아니라 소유권 규약이 깨졌다는 신호다.
- 이 리포는 브랜치를 나누지 않는다. 라운드가 곧 순서이고, `main` 위의 선형 이력이
  왕복 기록 그 자체다. 자기 리포(`version2` / `microscope-link-survey`)의 브랜치
  작업과는 별개다.

## 구현 항목

1. **`plan_experiment_<title>.json` 사이드카 내보내기.** `knowledge/plans.py`에
   이미 `_section()`/`_table_rows()` 파서가 있으니 재사용한다. 숫자는 구조화
   블록이 권위이고 산문 표가 그걸 인용하는 방향으로 한다.
2. **`plan-check`에 규칙 하나 추가**: *산문 표의 모든 숫자는 구조화 블록에 존재해야
   한다.* 이건 하드룰 2("Never originate a physical number")를 기계적으로 집행하는
   것이라 브리지와 무관하게도 이득이다.
3. **`kb/external/bd/` 네임스페이스 신설.** 경로에 외래성을 새긴다 — 이 리포의 plan은
   경로로 인용하므로 frontmatter 필드만으로는 인용 지점에서 보이지 않는다.
   frontmatter는 `$BRIDGE/schema/kb_external_entry.schema.json`을 따른다.
   **`kb/calibrations/`에는 절대 넣지 않는다** — 그 디렉토리는 "이 장비에서 측정됨"을
   뜻하고, 시뮬레이션 `f_c`가 거기 있으면 경로 자체가 거짓말이 된다.
4. **`may_be_gate_threshold: false`를 실제로 집행.** 외래 엔트리는 목표 설정이나
   설계 동기로는 쓸 수 있지만, **게이트가 통과 판정하는 임계값이 될 수 없다.**
   시뮬레이션 숫자를 먹은 게이트는 측정된 것처럼 보이는 margin을 낸다 — 하드룰 3이
   이미 경고하는 병이다. 허용할 거라면 margin이 외래성을 상속해서
   `m = 1.05 (external-derived)`처럼 나와야 한다.
5. **해시 드리프트 검사**를 `python -m knowledge.cli`에 추가. `source_hash`가 상류와
   달라지면 그 엔트리를 인용하는 모든 plan을 짚어준다. 수명주기는 **삭제가 아니라
   supersession**이다 — 임시로 지운 수입품은 이미 `kb/decisions/`로 졸업한 plan의
   인용을 끊는다. 이 리포에는 `superseded_by`/`corrected_by`가 이미 있다.
6. **`ask_simulation.json` writer.** r1 픽스처가 목표 형태다:
   `system_primitives`(primitive만, 측정 단위 그대로, `evidence` 필수),
   `instrument_envelope`(장비가 실제로 할 수 있는 범위 — BD가 "네 카메라로는 불가"를
   답할 수 있게), `assumptions`(8개 항목, `shared|differs|unknown`),
   `reference_only`(비구속), `required_precision`(**반드시 건너가야 하는 유일한 자유
   숫자** — 없으면 BD 게이트가 구속되지 않아 아무 계획이나 통과한다).
7. **r2가 이미 낸 findings 3개에 응답한다.** 이게 이번 라운드의 실질적 산출물이다.
   - 샘플링 규약이 정확히 2π 차이난다. 이 리포 게이트는 `f_s >= 10 f_c` = 99 Hz,
     BD 규약은 `10/tau_k` = 620 Hz. 520 fps는 전자를 5.3배 통과하고 후자에 16 %
     미달한다. **어느 규약을 쓸지는 사람이 결정할 사항**이므로, 양쪽 수치를 plan에
     나란히 적고 결정을 요청하는 형태로 남긴다.
   - `epsilon = 10 nm`에서 정밀도 예산이 이미 소진된다: `alpha`에 ~8 %, 그리고
     분산이 아니라 **편향**이라 rung/분절로 평균되지 않는다. precondition P8을
     보정 항목이 아니라 하드 게이트로 승격할지 검토할 것.
   - rung당 5 s는 `T_obs/tau_k = 310`으로, BD가 1.17 %를 실측한 2000의 6.4분의 1이다.

## 검증

    cd $BRIDGE && python3 validate.py --selftest     # 규칙이 아직 작동하는지
    cd $BRIDGE && python3 validate.py threads/<thread>/r<N>/ask_simulation.json

`--selftest`는 `threads/`가 통과하고 `fixtures/invalid/` 6개가 **각각 파일명이 지목한
규칙 하나만** 발화해야 성공한다. 이 리포 쪽 변경은 여기에 더해
`python -m knowledge.cli plan-check`와 기존 테스트가 통과해야 한다.

## 절대 하지 말 것

- `confirmed_by`를 쓰지 않는다. 양쪽 리포 모두 사람 전용이고, 브리지는 그걸 위조할
  위치에 있는 유일한 구성요소다 (검증기 R7).
- 상대가 준 숫자를 요약·재진술하지 않는다. 수입은 **기계적 복사**여야 한다. 요약하면
  그 파일이 새로운 origination point가 되고, 그건 하드룰 2가 금지하는 것이다.
- 단위 문자열을 추측해서 고치지 않는다. 파싱 안 되면 거부한다.
- 무차원수 계산 코드를 만들지 않는다 (W1).
- BD 리포를 수정하거나 BD의 `CLAUDE.md`를 로드하지 않는다.

## 첫 응답으로 원하는 것

코드를 쓰기 전에, 위 1–7 중 **이 리포의 규칙과 충돌하거나 예상보다 큰 항목**을
짚어서 보고할 것. 특히 4번(외래 엔트리의 게이트 입력 자격)은 게이트 구현에 손을
대야 할 수 있으니, 실제로 어디를 고쳐야 하는지 확인한 뒤 계획을 제시할 것.
