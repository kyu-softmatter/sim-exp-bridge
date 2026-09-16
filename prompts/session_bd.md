# 이 세션(Brownian-Dynamics-Agent, branch `microscope-link-survey`)에 붙여넣을 요청문

---

## 목적

이 리포(시뮬레이션 에이전트)와 `~/Desktop/agentic-microscope`(실험/현미경
에이전트)를 **양방향으로** 잇는 작업이다. 목표는 두 가지 흐름을 모두 성립시키는
것이다.

- **시뮬 → 실험**: 이 리포의 plan/결과를 근거로 AM이 실험 계획을 세운다.
- **실험 → 시뮬**: AM의 plan/결과를 근거로 이 리포가 시뮬레이션 계획을 세운다.

핵심 원칙 하나만 기억하면 된다. **숫자를 운반하는 게 아니라 질문을 넘긴다.**
상대의 plan을 복사하거나 번역하지 않는다. 상대가 보낸 것은 "주장 + 답을 낼 단일
관측량 + 필요 정밀도 + 계를 정의하는 primitive + 가정 선언"이고, **이 리포의 spec은
그것을 입력으로 삼아 L0→L2→무차원화 파이프라인을 처음부터 다시 통과해서** 나와야
한다. 상대가 도출한 파생값은 비구속 참조값이며, **먼저 직접 도출한 다음에**
비교한다 — 순서가 뒤바뀌면 검증이 아니라 앵커링이 된다.

두 계가 동일한 물리계일 필요는 없다. SI 값이 달라도 무차원 영역이 겹치고 가정이
선언되어 있으면 충분하고, 그게 오히려 더 강한 증거다. 막아야 하는 건 **선언되지
않은 가정 차이**다 — 무차원수를 맞춰도 한쪽에 벽이 있고 한쪽에 없으면 다른 계다.

## 먼저 읽을 것

공유 저장소가 이미 있다. **먼저 이것부터 읽고, 코드를 건드리기 전에 검토 결과를
보고할 것.**

    BRIDGE=~/Desktop/sim-exp-bridge

1. `$BRIDGE/README.md` — 와이어 규칙 W1–W3, evidence→tier 매핑표 T1, 검증기 7규칙,
   파일 배치
2. `$BRIDGE/threads/trap-stiffness-recovery/r1/ask_simulation.{md,json}` — 이 리포가
   **받는** 문서의 예시. AM의 `kb/plans/2026-09-15-drag-calibration-stiffness-vs-size.md`
   에서 뽑은 것이다.
3. `$BRIDGE/threads/trap-stiffness-recovery/r2/ask_experiment.{md,json}` — 이 리포가
   **보내는** 문서의 예시. `runs/trap-2d-5um__a5ef4f45d589`의 `metrics.json`과
   `spec.json`에서 숫자를 전부 복사한 것이다.
4. `$BRIDGE/threads/trap-stiffness-recovery/r1/kb_entry_for_bd.md` — 받은 것이 이
   리포의 KB에 착지하는 형태.
5. `$BRIDGE/schema/*.json` — 스키마 4개.

이 문서들은 **명세이자 예시**다. 새로 설계하지 말고 이 형태를 따르되, 이 리포의
원칙(특히 원칙 1 차원 우선, 원칙 2 무차원 spec 수작성 금지, 원칙 3 provenance)과
충돌하는 지점이 있으면 구현 전에 지적할 것.

## 이 세션의 범위

`~/Desktop/Brownian-Dynamics-Agent`, 브랜치 `microscope-link-survey`. **AM 리포의
파일은 읽기만 하고 절대 수정하지 않는다.** AM의 `CLAUDE.md`도 로드하지 않는다 —
AM은 SAFETY.md 416줄과 하드룰 5개로 부팅하고 이 리포는 자기 원칙 10개가 있어서,
섞으면 양쪽을 신뢰할 수 있게 만드는 거부 동작이 서로 희석된다.

## 와이어 규칙 — 이 리포가 양방향 변환을 **독점**한다

**W1 · 무차원화는 양방향 모두 이 리포가 한다.** AM에는 무차원화 능력이 없고, 억지로
만들게 하면 실수 지점이 하나 더 생긴다. 그래서 프로토콜이 비대칭이다.

- **받을 때**: AM이 준 차원 있는 primitive를 `bdbot/units.py`(pint)로 파싱하고
  `nondim.py`로 축약한다.
- **보낼 때**: 무차원 결과를 `scales.py`로 **역변환해서 AM의 단위로 된 SI 범위**로
  만들어 보낸다. `ask_experiment.requirements[]`가 그것이고, AM 게이트는 그것만
  보면 된다 (`T_obs >= 32.3 s`, `f_s >= 620 Hz`, `epsilon <= 7.6 nm`).
  `regime[]`은 사람이 역변환을 감사하기 위해 같이 싣되, AM의 기계 검사에는 구속력이
  없다고 명시한다. 형태는 `spec.json`의 `groups[]`와 일치시켜 뒀으니 어댑터는 거의
  복사다.

**W2 · 받은 단위를 추측하지 않는다.** AM은 `pN/um`, `mPa*s`, `g/cm^3`을 측정된 형태
그대로 보낸다. pint로 파싱되지 않으면 **거부한다** — 추측한 단위는 조용한 배수다.
그리고 **수입 시점에 변환하지 말고 사용 시점에 변환한다**: 외래 KB 엔트리에는 AM의
단위가 그대로 들어가고, 무차원화는 파이프라인이 그 값을 쓸 때 한다.

**W3 · 합성량은 이 리포가 만든다.** AM은 `d`, `eta`, `T`, `k_t`만 보내고 `gamma`,
`tau_k`, `f_c`는 보내지 않는다. `3*pi*eta*d`와 `6*pi*eta*a`는 같은 식이라 곱을
받는 순간 아무도 거짓말하지 않은 채로 2배가 들어간다 — 이 리포의 intake가 이미
ambiguity `A1`("R = 5 µm가 반지름인가 지름인가")로 한 번 걸린 바로 그 지점이다.

**T1 · tier는 유도하고 추측하지 않는다.** AM이 각 숫자에 `evidence`를 붙여 보낸다.

| `evidence` | tier | 비고 |
|---|:-:|---|
| `measured` | 0 | AM 장비에서 측정 |
| `handbook` | 0 | |
| `computed` | 1 | 단, **입력 중 최악 tier를 상속한다.** r1의 `eta`는 assumed인 `T`에서 계산됐으므로 tier 3이다 |
| `assumed` | 3 | 기본값·placeholder·standing choice |

`provenance.py` 헤더가 경고하는 "tier 1 by inheritance"가 정확히 이 지점이다.
승계는 정당하지만 측정된 것처럼 기록하는 건 아니다.

**단위 왕복 되읽기가 필수다.** 이 리포가 양방향 변환을 독점하므로 아무도 이 리포의
변환을 검산하지 않는다. 물리는 못 잡아도 단위는 잡을 수 있으니, 파싱한 primitive를
**AM이 보낸 단위로 다시 써서** `parsed_back.received`에 싣고, 직접 만든 합성량을
`parsed_back.derived_here`에 싣는다. r2 픽스처에서 `a = d/2 = 2.475 um`를 명시적으로
적고 AM의 9.9 Hz와 자기 9.86 Hz를 대조하는 게 그 장치다.

## 파일 소유권 — 충돌 없이 같은 저장소를 쓰는 방법

| 파일 | 쓰는 쪽 |
|---|---|
| `threads/<thread>/r<N>/ask_experiment.{json,md}` | **이 세션** (짝수 라운드) |
| `threads/<thread>/r<N>/ask_simulation.{json,md}` | AM 세션 (홀수 라운드) |
| `threads/<thread>/r<N>/kb_entry_for_bd.md` | **이 세션** — 받은 것을 수입한 기록 |
| `threads/<thread>/r<N>/kb_entry_for_am.md` | AM 세션 |
| `hashes.json` | 각자 **자기 리포 접두사(`bd:`)의 항목만** |
| `schema/`, `validate.py`, `README.md` | 변경 제안은 하되 합의 전 수정 금지 |

스레드 경로는 `<thread-id>/r<N>`이고 제목으로 잇지 않는다. 왕복 루프의 가장 흔한
실패는 각 단계가 틀리는 게 아니라 3번 돌고 나니 원래 질문이 아닌 것이다.

## 구현 항목

1. **수입 어댑터: `ask_simulation.json → intake/<case>/observation.yaml + system.yaml`.**
   `bdbot/intake.py` 옆에 둔다. `observation.yaml`은 전사 층이므로 받은 문서를
   출처로 기록하고, `system.yaml`은 L2로서 `derived_from`을 유지한다. tier는 위 T1
   표로 **유도**한다. 받은 `assumptions`는 값이 아니므로 유도할 수 없다 — 그대로
   싣고, 이 리포 쪽 대응을 채워 `shared|differs|unknown`을 확정한다.
2. **송출 어댑터: `metrics.json` + `spec.json` → `ask_experiment.json`.**
   `spec.json`이 이미 들고 있는 `groups[]`와 `back_transform`을 재사용한다.
   `achieved_precision`은 `observables[].err_pct`에서 가져온다(목표치가 아니라
   달성치다). `requirements[]`는 역변환 결과이고, 각 항목의 `from`에 도출 근거를
   산문으로 적는다.
3. **`knowledge/external/am/` 네임스페이스 신설.** 경로에 외래성을 새긴다.
   frontmatter는 `$BRIDGE/schema/kb_external_entry.schema.json`을 따르고,
   `may_be_gate_threshold: false`가 기본이다. 수명주기는 **삭제가 아니라
   supersession**이다 — 임시로 지운 수입품은 그걸 인용한 기록을 끊는다.
4. **해시 드리프트 검사.** `source_hash`가 상류와 달라지면 그 엔트리에 기대는 spec을
   짚어준다. `$BRIDGE/hashes.json`의 `bd:` 항목은 이 세션이 관리한다.
5. **r2가 스스로 남긴 gaps 중 싼 것 2개.** 이게 다음 라운드를 실질적으로 진전시킨다.
   - **샘플링 층**: 위치를 `t_exp`에 대해 적분한 뒤 Gaussian `epsilon`을 더한다.
     물리 변경이 아니라 후처리 층이라 싸고, 이것이 있으면 r2가 미룬 질문(블러와
     localisation noise가 `h0` 복원에 미치는 영향)을 다음 라운드가 답할 수 있다.
   - **`n_replicas = 1` + 다중 seed**: 현재 1.17 %는 N=1000 앙상블 오차다. 실험은
     rung당 비드 1개이므로 ~32배 흔들린다. 라운드당 오차막대의 의미를 맞추는 게
     r2의 findings 중 가장 중요한 항목이었다.
6. **벽 러너는 별도 카드로.** `gamma(h) = gamma_0/(1 - 9a/(16h))` 계열을 다루려면
   `RUNNERS`에 새 카드가 필요하다. **트랩 러너로 조용히 돌리지 않는다** — 그러면
   틀린 계를 계산한다. 이번 라운드에서 만들지 않아도 되고, 못 한다면 `gaps[]`에
   그렇게 적으면 된다. **거부는 유효한 결과다.**
7. **`plan_simulation_<title>.md`는 생성물로 둔다.** `bdbot/report.py`가 이미 산문을
   뽑으니 손으로 쓰지 않는다. 파이프라인이 권위이고 md는 그 산물이므로 이 리포
   쪽에서는 md↔json 드리프트가 구조적으로 불가능하다.

## 검증

    cd $BRIDGE && python3 validate.py --selftest     # 규칙이 아직 작동하는지
    cd $BRIDGE && python3 validate.py threads/<thread>/r<N>/ask_experiment.json

`--selftest`는 `threads/`가 통과하고 `fixtures/invalid/` 6개가 **각각 파일명이 지목한
규칙 하나만** 발화해야 성공한다. 이 리포 쪽 변경은 여기에 더해 기존 테스트와
`python cli.py` 경로가 깨지지 않아야 한다.

검증기 규칙 중 이 리포가 직접 걸릴 수 있는 것은 **R5(순환 증거)**다: AM의 숫자를
`requirements[]`의 근거로 되돌려주면서 `hard: true`로 두면 거부된다. AM 자기 숫자가
독립 증거로 읽히는 상황이기 때문이다. r2 픽스처의 `sigma_gamma_per_rung`이 실제로
그 경우이고, `hard: false` + `gaps[]`에 공개로 두어서 경고로만 뜨게 해 놨다.

## 절대 하지 말 것

- `confirmed_by`를 쓰지 않는다. 양쪽 리포 모두 사람 전용이고, 브리지는 그걸 위조할
  위치에 있는 유일한 구성요소다 (검증기 R7).
- 받은 숫자를 요약·재진술하지 않는다. 수입은 **기계적 복사**여야 한다. LLM이 요약하면
  그 파일이 새로운 origination point가 되고, 원칙 3이 금지하는 것이 된다.
- 단위를 추측해서 고치지 않는다. 파싱 안 되면 거부한다.
- AM의 `assumptions`를 값에서 유추하지 않는다. "Faxén 보정이 적용되는 계"는 어떤
  숫자에서도 유도되지 않으므로, 선언되지 않았으면 `unknown`이고 문서는 draft다.
- 러너 없는 카드를 트랩 러너로 돌리지 않는다.
- AM 리포를 수정하거나 AM의 `CLAUDE.md`를 로드하지 않는다.

## 첫 응답으로 원하는 것

코드를 쓰기 전에, 위 1–7 중 **이 리포의 원칙과 충돌하거나 예상보다 큰 항목**을 짚어서
보고할 것. 특히 1번에서 외래 문서가 `observation.yaml`(전사 층)과
`system.yaml`(L2)에 각각 어떻게 들어가야 원칙 1·3을 깨지 않는지 — 그게 이 작업의
가장 미묘한 지점이니 먼저 확인하고 계획을 제시할 것.
