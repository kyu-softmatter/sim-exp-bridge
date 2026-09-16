# bridge — agentic-microscope ↔ Brownian-Dynamics-Agent

A schema and two worked round-trips for handing a **question** between the two
agents, so each one re-derives its own plan through its own gates instead of
importing the other's numbers.

```
python3 validate.py --selftest      # CI entry point: the rules still bite
python3 validate.py --all           # every document, warnings included
```

## What crosses, and what does not

Neither `plan.md` nor `plan.json` crosses. Each repository keeps its own plan as
a **local** artefact (`plan_experiment_<title>.*`, `plan_simulation_<title>.*`),
and only a small question card moves:

```
plan_experiment_<title>.md/.json        ← AM's gates produced this. Stays home.
        │
        ▼  ask_simulation.md + .json    ← the only thing that crosses
        │
plan_simulation_<title>.md/.json        ← BD's gates produced this. Stays home.
        │
        ▼  ask_experiment.md + .json    ← back the other way
```

`.md` is the human face and `.json` is the machine face of the **same** document.
They are not independent: on the AM side the JSON is authoritative and the prose
cites it; on the BD side the pipeline is authoritative and both files are
generated (`bdbot/report.py` already writes prose). Drift is possible in only one
direction, and only on the side where a person types numbers.

## Three wire rules

**W1 · Only BD nondimensionalises — in both directions.** AM never emits or
consumes a dimensionless group. AM sends dimensional primitives; BD parses them
with `pint`, reduces with `nondim.py`, and **inverse-maps its answer back into
SI ranges** with `scales.py` before sending. `ask_experiment.requirements[]` is
therefore something AM's gates check directly; `regime[]` rides along for a
human to audit the map. The capability is asymmetric, so the protocol is too.

**W2 · Send the number in the unit it was measured in.** No hand-normalisation
to SI: that is a conversion, and a conversion is an error opportunity on the
side that has no unit library. `pN/um`, `mPa*s`, `g/cm^3` all travel as typed.
Unparseable ⇒ the receiver **refuses** (rule R2); it never guesses.

**W3 · Send primitives, not composites.** `d`, `eta`, `T`, `k_t` — not `gamma`,
`tau_k`, `f_c`. `3πηd` and `6πηa` are the same formula, so shipping the product
is where a factor of two enters with nobody lying; BD's own intake already hit
this as ambiguity `A1` ("is R = 5 µm the radius or the diameter?"). Derived
values may travel in `reference_only`, explicitly **non-binding**, to be read
only *after* the receiver has derived its own.

## The one block that is not a number

`assumptions[]`. "No Faxén wall correction", "`dimensions: 2`", "no detector
model", "1000 non-interacting replicas" — none of these follows from any value,
so they must cross explicitly, each marked `shared | differs | unknown` with a
`worth` (how much it moves the answering quantity). While anything is `unknown`
the document is a **draft** (rule R4).

Two systems may differ freely in SI values as long as the regime brackets and the
assumptions are declared: agreement across *different realisations of the same
regime* is stronger evidence than agreement between identical ones. The failure
this guards against is the other kind — an undeclared assumption difference,
which looks like agreement and is not.

## T1 · evidence → tier

The sender declares how a number came to exist; the importer derives BD's tier.
Never guessed, because `provenance.py`'s own header names inherited tier 1 as the
dangerous case.

| `evidence` | BD tier | note |
|---|:-:|---|
| `measured` | 0 | on the sending instrument |
| `handbook` | 0 | |
| `computed` | 1 | …from measured inputs. **Inherits** the worst tier of its inputs — AM's `eta` is tier 3 here because it is computed from an assumed `T`. |
| `assumed` | 3 | a standing choice, a default, a placeholder |
| `simulated` | — | not admissible as a tier-0 input; lands as an external KB entry |
| `round_trip` | — | this number originated in the receiving repository |

## The seven rules

Only R1 is a shape rule. The others are about provenance, which no schema
expresses.

| | rule | what it prevents |
|---|---|---|
| R1 | JSON Schema | malformed document |
| R2 | every `unit` parses | `pN/µm` with the micro sign silently becoming something else |
| R3 | no composites in `system_primitives` | the `3πηd` / `6πηa` factor of two |
| R4 | an `unknown` assumption forces `status: draft` | an undeclared assumption difference reading as agreement |
| R5 | a **hard** requirement may not rest on the consumer's own number | circular evidence: three rounds and both KBs agree with nothing measured twice |
| R6 | cited hashes match `hashes.json` | a stale import, after upstream was corrected |
| R7 | `confirmed_by` is never a machine name | the bridge signing off on itself |

R5 is deliberately narrow. After two rounds the other repository *always* appears
in your ancestry — that is a round trip working. What it catches is a number
coming **home** and being read as independent: soft and disclosed is allowed and
warned about, hard is refused.

## Where an imported number comes to rest

`kb/external/bd/<thread>.r<N>.md` on the AM side,
`knowledge/external/am/<thread>.r<N>.md` on the BD side. The **path** carries the
foreign origin, because both repositories cite by path and a frontmatter field
would not show at the citation site. A simulated `f_c` must never sit in
`kb/calibrations/`, which means "measured on this instrument" — rule R9 refuses
it.

Two properties matter more than the file format:

- **`may_be_gate_threshold: false`** by default. An imported number may motivate
  a design or set a target; a gate that *clears* against it emits a margin that
  reads as locally measured, which is the disease AM hard rule 3 already names.
- **Lifecycle is supersession, not deletion.** "Temporary" imports do not stay
  temporary — a plan cites one, the plan graduates into `kb/decisions/`, and now
  the import is load-bearing in a permanent record. Deleting it dangles the
  citation. Both repositories already have supersession machinery
  (`superseded_by` / `corrected_by`); use it.

## 이 스레드의 실제 헤드라인: 싸게 측정할 수 있는 것을 추정했다

여덟 라운드가 물리에 대해 알아낸 것보다, **네 번 반복된 한 가지 실패**가 더 옮겨갈 만하다.
매번 형태가 같다 — 값이 하나 추정되고, 조심스러운 문서들에 실려 전파되고, 누군가
**실제로 측정하자 무너졌다.** 그리고 매번 측정 비용이 낮았다.

| # | 추정된 것 | 측정했을 때 | 며칠/라운드 생존 |
|---|---|---|---|
| 1 | r2 의 `f_c` 정밀도 +1.17 % — "물리" | 추정기 편향. 정확한 OU 를 같은 추정기에 넣으면 +0.8–1.2 % | 2라운드 |
| 2 | r1 의 blur `2 D t_exp/3` | OU 의 정확한 boxcar 인수는 `u/3`. 2배 차이, `2u/3` 는 16–358σ 로 기각 | 3라운드 |
| 3 | r1 의 rung 당 3 % — numpy 토이 모델 | 단일 비드 29.1 %. 그리고 주 경로의 slope 정밀도는 **아직 아무도 측정하지 않았다** | 7라운드, 진행 중 |
| 4 | 검증기 경고 부피 — "아직 조치할 필요 없음" | 이미 11회 반복, 출력 11,787자 | 즉시 |
| 5 | r8 의 `rev: 07d1048` — 커밋됐다고 가정된 파일 | 그 리비전에 파일이 없다. 해시는 옳고 `rev` 가 아무것도 가리키지 않았다 | 여러 커밋, 푸시된 상태로 |

5번도 BD 가 스스로 지적했다. 그리고 **`rev` 가 해석되는지는 아무것도 검사하지 않는다** —
R6 은 해시를 검증하고 만족한다. 그게 옳은 분업이다(해시가 내용을 고정하고 `rev` 는 사람이
가서 보기 위한 것). 다만 `rev` 는 조용히 틀릴 수 있고, 한 번 그랬다. **한 사례는 규칙이
아니므로 만들지 않는다** — 두 번째를 알아볼 수 있게 여기 적어둔다. 재발하면 싼 형태는
`--selftest` 가 `bd:` rev 를 BD 리포의 실제 객체와 대조하는 것이지만, 검증기를 리포 배치에
묶는 비용이 얻는 것보다 클 수 있다.

4번은 BD 세션이 스스로 지적했고, **자기가 그 실패를 한 첫 사례**라는 점까지 적었다.
1–3 번을 찾아낸 쪽이 같은 형태에 걸린 것이 요점이다 — 이 실패는 부주의가 아니라
**추정이 그 순간에는 항상 충분해 보인다**는 데서 온다.

그래서 이 리포가 규칙을 늘려온 방향도 같다: R8·R11·R12·R13 은 전부 "숫자가 검사 없이
문서 사이를 이동했다" 를 잡는다. **측정 비용이 낮은데 추정했다면, 그것이 다음에 무너질
것이다.**

## 고칠 수 없는 문서에 발화하는 규칙은 자기 메시지에 그렇게 적어야 한다

R8·R12·R13 세 규칙이 옛 문서에 **영구 경고**를 낸다. 세 개 다 같은 이유다 — 그 문서들은
해당 필드/규약이 없던 시절에 쓰였고, 경고가 서 있는 것이 **어휘가 언제 바뀌었는지를
기록하는 유일한 장치**다. 부채가 아니다.

그런데 경고가 그 사실을 말하지 않으면 **첫 독자가 과제로 읽고 봉인된 파일을 고친다 —
그게 cascade 다, 한 층 위에서.** 실제로 그 경로로 발생했다: R12 는 "`gaps[]` 에 `kind` 가
없다" 고만 말했고, 브리지 소유자가 그것을 읽고 r2 에 백필했다.

**변종 하나가 더 있고, 저항하기가 더 어렵다.** 경고가 과제로 읽히는 것이 아니라,
**문서가 사실과 다른 것을 담고 있으므로 고쳐야 한다** 고 느껨지는 경우다. BD 의 r8 이
존재하지 않는 리비전에서 파일을 인용하고 있었다 — 해시는 내내 옳았고 `rev` 가 아무것도
가리키지 않았다. 거짓을 그대로 두는 것이 태만한 선택처럼 보이므로, 첫 변종보다 강하게
편집을 밀어붙인다. 그리고 r8 은 이미 AM 의 수입본이 인용하고 있었다.

**봉인된 문서에 거짓이 있어도 봉인은 유지된다.** 다만 구제 수단은 **두 단계**이고, 이
구분이 빠지면 규칙이 스스로 무너진다 — **구제가 유혹보다 비싸면 다음 사람은 그냥
편집한다.**

판별 질문 하나: **하류의 결론이 하나라도 움직이는가?**

| | 거짓의 위치 | 구제 | 비용 |
|---|---|---|---|
| **움직인다** | 주장(claims). r2 의 `achieved_precision` — 하중을 받고 의존물 6개 | `corrects[]` 를 담은 **새 문서** | 라운드 문서 하나. 그만한 값이 있다 |
| **안 움직인다** | 인용 장치(citation apparatus). r8 의 잘못된 `rev` — 토큰 하나, 결론 이동 없음 | 매니페스트에 **두 리비전 등록** (접미사 없는 키는 기존 인용이 가리키는 곳에, `@r<N>` 에 현재 것) | 한 줄 |

둘 다 봉인을 유지한다. 다른 것은 **발행 비용뿐**이다. 잘못된 `rev` 하나에 전체
`ask_experiment` 를 발행하라고 요구하면 그 규칙은 지켜지지 않는다.

**이 결론에 도달한 순서를 정직하게 적어둔다** (BD 세션의 요청): BD 는 먼저 편집했고,
R6 에 걸렸고, **그 수리가 결과적으로 올바른 구제였다.** 교훈은 "싼 경로를 알고 있었다"
가 아니라 **싼 경로가 서 있던 자리에서 보이지 않았다** 는 것이다 — `rev` 가 AM 과 BD
양쪽에게 보이지 않아서 둘이 독립적으로 `@r<N>` 를 발명한 것과 같은 형태다.

## 두 번째 패턴: 검사가 존재하는데 자기가 서술하는 것에 연결되어 있지 않다

"싸게 측정할 수 있는 것을 추정했다" 와는 다른 실패이고, 이제 세 사례다.

| 검사 | 서술한 것 | 실제로 읽은 것 |
|---|---|---|
| 브리지 `chain` | "R5 가 요구한다" | `validate.py` 에 그 문자열이 0회 등장 |
| AM `plan-check` | plan 의 형태 | 링크를 하나도 해석하지 않음 — `kb/decisions/` 인용 3개가 다른 브랜치에만 있는 엔트리를 가리켰고, 그게 ROI·노출·520 fps 의 출처였다 |
| BD `health.gate()` | (BD 리포 기록) | 서술한 대상에 연결되지 않음 |

BD 세션의 `CLAUDE.md` 가 자기 리포에서 이미 세 개를 들고 있었다 — `bd-intake` §2.1 의
빈-goal 차단(두 번 쓰이고 0번 집행, 8사례 중 2개가 그냥 지나가 85런을 생산), `A4` 의
grep(거짓 일치 7건, 실제 검사 0건), `health.gate()`(형제 도구에서만 도달 가능해서 어떤
런도 자기를 gate 하지 않음). 거기에 브리지의 `chain` 과 AM 의 `plan-check` 을 더하면
**세 코드베이스에 다섯 개, 같은 사람이 독립적으로 만든 것**이다.

그래서 주장이 바뀐다: 한 프로젝트가 우연히 가진 기록이 아니라 **기본값**이다. 다음 사람은
자기가 걸렸다고 느낄 필요가 없고, **예상해야 한다.**

세 경우 다 **검사가 통과했고 통과가 아무것도 의미하지 않았다.** 추정 패턴은 숫자를
겨냥하고 누군가 측정하는 순간 무너진다. 이 패턴은 **검사 자체**를 겨냥하고,
**통과하기 때문에 보이지 않는다** — 스스로를 드러내는 순간이 없다. 그래서 방어가 다르다:
앞의 것은 누군가 측정을 돌려야 하고, 뒤의 것은 **누군가 규칙을 일부러 실패시켜야** 한다.

### 일반형

1. **규칙당 음성 픽스처 하나.** 그 규칙만 발화해야 한다.
2. **경로가 둘 이상인 규칙에는 인라인 분기 검사.** R6 의 다섯 개는 철저함이 아니라
   **최소치**였다 — 리비전 분기는 BD 가 자기 우회책을 제거할 때까지 라이브 트리에서
   도달 불가능했고, 다섯 중 넷이 멀쩡해 보이는 동안 하나가 죽어 있었다.
3. **음성 픽스처는 실패가 *일어났다*가 아니라 실패의 *정체*를 주장해야 한다.** BD 의
   harness 가 `12 fired, 0 did NOT` 을 출력했고 그중 7개가 자기 호출 시그니처가 틀려서
   난 `TypeError` 였다 — **잘못된 이유로 통과하는 검사기를 찾으려고 쓴 스크립트가 바로 그
   상태였다.** 이 리포도 한 단계 미세한 수준에서 같았다: `--selftest` 는 올바른 *규칙*을
   요구했고, **분기가 넷인 R6 이 엉뚱한 분기로 옮겨가도 통과**했다.
   `fixtures/invalid/expected.json` 이 픽스처별 메시지 조각을 고정하고, 조각을 일부러
   틀리게 바꾸면 `R6 fired for the WRONG reason` 으로 실패하는 것을 확인했다.

세 번째 절이 가장 늦게 왔고 가장 중요하다. 1과 2는 **죽은** 검사를 잡고, 3은
**살아 있으면서 엉뚱한 것을 확인하는** 검사를 잡는다. 후자가 더 나쁘다 — 통과가 증거처럼
보이기 때문이다. 그리고 ad-hoc 형태(개별 호출 12개)가 절차를 적용하는 사람이 **처음
집어드는 형태**이며, 그것이 공허하게 통과할 수 있는 형태다.

**그리고 이 일반형이 이 리포에서 네 개를 더 찾았다.** `chain` 은 읽어서 발견됐고
(BD 의 지적대로 *발견*의 방어는 검사가 될 수 없다), 그 다음은 절차가 했다: 에러를 내는
규칙 중 픽스처도 라이브 발화도 없는 것을 열거하니 **R0·R1·R9·R10** 이 나왔다. 넷 다
픽스처를 만들자 통과했다 — 즉 죽어 있던 게 아니라 **아무도 본 적이 없었다.** 발견은
읽기에 의존하지만, 일반형은 그것을 **절차로 바꾼다.**

그리고 실무적으로: **편집 전에 그 문서가 인용되고 있는지 확인하는 것은 명령 한 줄이다.**

그래서 규칙 문구의 요건: **발화 대상이 고칠 수 없는 문서라면, 메시지가 "봉인된 문서는
그대로 두고 새 문서에만 적용하라" 를 직접 말한다.** R13 이 처음부터 그렇게 쓰였고,
R8·R12 는 뒤늦게 맞췄다.

## 특정 리비전을 인용하는 정식 방법

R13 이 필요했던 이유는 우회책 하나가 그것을 필요하게 만든 제약보다 오래 살았다는 것이고,
**두 세션이 서로 베끼지 않고 같은 우회책에 독립적으로 도달했다**는 것이다. 둘 다 그것을
우회책이 아니라 규약처럼 적었다. 같은 잘못된 모양에 둘이 도달한 것은 그 아이디어가
나쁘다는 증거로는 약하고, **올바른 모양이 발견 불가능했다**는 증거로는 강하다. 그래서
여기에 한곳에 적는다:

```json
{ "ref":  "am:kb/plans/2026-09-15-drag-calibration-stiffness-vs-size.md",
  "rev":  "9f971a8",
  "hash": "sha256:58cfc405231a2970" }
```

- `ref` 는 **경로일 뿐이다.** `@r<N>` 를 넣지 않는다 (R13).
- `rev` 가 리비전을 말한다 — 커밋 sha 가 최선, 브랜치명도 가능.
- `hash` 가 그 리비전의 내용을 고정한다.
- 매니페스트(`hashes.json`)에서만 `<ref>@r<N>` 키 형태를 쓴다. R6 가 등록된 **어느**
  리비전과 일치해도 통과하므로, 나중 라운드는 키를 **추가**하고 접미사 없는 키를 **갱신하지
  않는다.**

## 봉인된 문서는 메타데이터조차 고치지 않는다

R6 는 **살아있는 매니페스트**를 **얼어붙은 인용**과 대조한다. 그래서 이미 인용된 문서의
해시가 움직이면 그 아래 모든 인용이 깨지고, **명백한 대응인 "해시 갱신" 이 정확히
틀린 수다.** 갱신은 다음 인용을 무효화하고, 그게 무한히 번진다.

실제로 일어났고, 두 사람이 각자 몫을 했다. `4652273`(브리지 소유자)이 r2 에
`gaps[].kind` 를 붙였다 — 내용은 쓰인 대로 보존했지만 해시가 움직였다. r8 이 깨졌다.
여기서 BD 세션이 접미사 없는 `bd:` 키를 갱신했고 r2 를 인용하는 r4 가 깨졌다. r4 를
갱신했더니 r5 와 r7 이 깨졌다. **세 번째에서 형태가 드러났다 — 즉 명백한 수정이 실패하는
것을 보면서 반복해서 시도됐다.** 그게 이 예시가 경고할 가치가 있는 이유다. 편집이 원인을
만들었고, 갱신이 그것을 전파했으며, 두 실수 중 어느 하나만으로는 cascade 가 되지
않는다.

**이것은 이 사건에 국한되지 않는다.** `gaps[].kind`, `assumptions_resolved`,
`corrects[]` 는 모두 **살아있는 스레드**에 추가됐고, 앞의 둘은 그 필드가 없던 시절의
문서에 소급 적용됐다. 옛 문서에 R12·R13 이 영구히 경고하는 것은 흠이 아니라 **어휘가
언제 바뀌었는지를 기록하는 유일한 장치**다 — 소급 백필은 그 사실을 지운다. r2 편집은
내용이 보존되어서 소급 적용이 공짜처럼 보인 유일한 경우였고, 그게 깨진 경우였다.

두 겹으로 막는다:

1. **인용된 문서는 고치지 않는다 — 메타데이터도 포함.** 새 필드가 생기면 새 문서에만
   쓴다. R12 가 옛 문서에 영구히 경고하는 것이 옳고, 그 경고가 "이 문서는 그 필드가
   없던 시절에 쓰였다" 는 사실을 보존한다. 내가 r2 를 건드린 것이 실수였다.
2. **R6 는 등록된 어느 리비전과 일치해도 통과한다.** 매니페스트의 `@r<N>` 규약을 R6 가
   읽는다. 접미사 없는 키는 옛 인용을 계속 검증하고, `@r<N>` 는 나중 문서가 대조한
   리비전이다. **접미사 없는 키를 갱신하지 말 것.**

`fixtures/valid/` 를 R6 에서 면제한 것이 한 층 아래의 같은 통찰이었다. 이쪽이 라운드
문서 버전이다.

## 대화로 전달된 결론은 출처가 아니다

**이 브리지가 존재하는 이유가 그것이다.** 그런데 세 세션이 서로 메시지를 보낼 수 있게
되자 브리지 소유자(나)가 발견을 채팅으로 중계하기 시작했고, 그게 편리한 만큼 정확히
브리지를 무용하게 만든다. 해시도 ref 도 리비전도 없는 주장은 나중에 감사할 수 없다.

AM 세션이 이 선을 먼저 그었다. BD 의 벽 발견과 동일한 결론에 도달한 뒤, plan 의 D-6 을
**자기 리포의 독자 도출로 쓰고 그 문장에 그렇게 명시했으며**, `k*` 의 정의를 인용했다 —
나도 BD 도 인용하지 않았다. 물리를 의심한 게 아니라, **provenance chain 에 "동료가
말해줬다" 가 들어간 plan 은 감사 불가능**하기 때문이다.

규약:

- **세션 간 메시지는 조정(coordination)과 프로토콜용이다.** 누가 무엇을 소유하는지,
  무엇이 푸시됐는지, 어느 규칙이 왜 바뀌었는지.
- **발견은 라운드 문서로 건너간다.** `ask_*.json` + 해시 + `rev`. 그게 감사 가능한
  유일한 형태다.
- **중계된 발견은 출처가 아니라 "가서 보라"는 신호로 취급한다.** 받은 쪽은 직접
  도출하거나 문서가 도착할 때까지 기다린다. AM 이 `k*` 산술을 직접 다시 해본 것이
  올바른 반응이다 (21219 대 r2 표의 21221, 그리고 그 식이 `k_t`·`d`·`kT` 를 나르고
  **drag 를 나르지 않는다**는 확인).

브리지 소유자도 예외가 아니다. 이 문서의 규칙 변경 근거를 메시지에 적는 것은 조정이고,
스레드의 물리적 결론을 메시지로 옮기는 것은 우회다.

## 블록마다 독자가 다르다 — `gaps[]` 는 운영자에게 닿지 않는다

`gaps[]` 를 `ask_simulation` 에 추가한 근거는 "체크리스트 항목으로 쓴 precondition 은
닫을 수 있어 보인다" 였다. AM 이 그 논거를 더 정확히 썼다: **닫을 수 있어 보이는 그
자리를 고쳐야 하고**, `gaps[]` 는 상대 에이전트가 읽는 블록이지 장비 앞에서 plan 을 펴는
**운영자**가 읽는 곳이 아니다.

그러니 둘 중 하나가 아니다. 같은 사실이 두 집을 갖는다: 브리지의 `gaps[]` 에
`kind: needs_data_transfer` 로, 그리고 행동하는 리포의 precondition 자리에 *분석 시간이
아니라 데이터 전송에 막혀 있다*로. AM 의 P7 이 그 형태다 (`af68322`).

## 공유 클론 위생 — 세 가지

세 세션이 한 클론을 쓴다. 모든 커밋의 git author 가 같은 사람이므로 **이력만으로는
어느 쪽이 썼는지 구분되지 않는다.** 라운드 기록의 저자가 모호해지면 소유권 표가
사후적으로 검증 불가능해진다.

1. **`git commit -am` 을 쓰지 않는다.** 상대가 스테이징해 둔 미완성 작업이 같이
   올라간다. `git commit --only <경로>` 로 자기 경로만 커밋한다. 실제로 발생했다:
   `hashes.json` 과 `r5/kb_entry_for_am.md` 가 AM 에 의해 스테이징된 상태에서 브리지
   소유자가 커밋하려던 순간.
2. **상대의 untracked 파일은 방해가 되더라도 건드리지 않는다.** `git add -A` 가
   쓸어담는다. 실제로 발생했다: `84b1530` 이 AM 의 `r4/kb_entry_for_am.md` 를 함께
   커밋했다 — 내용은 동일해서 잃은 것은 없었지만, 그 라운드 기록의 저자가 모호해졌다.
3. **커밋 메시지에 어느 쪽인지 적는다.** author 로는 구분되지 않으므로 트레일러로
   남긴다:

       Bridge-Session: am | bd | owner

`--selftest` 는 이것을 검사하지 않는다. 검사할 수 있는 성질이 아니고, 규약으로 두는
것이 맞다.

## R5 의 soft 경고가 값을 했다 — 기록

r2 의 `sigma_gamma_per_rung <= 3 %` 는 AM 자신의 400회 numpy 추정치가 되돌아온
것이어서 R5 가 경고를 냈고, `hard: false` + `gaps[]` 공개라서 통과했다. **네 라운드 뒤에
그 숫자가 이 실험의 주 경로 전체를 받치고 있다는 것이 드러났다** — r5 의 29.1 % 는
교차검증 경로이고, plan 의 주 경로는 drag slope `alpha = gamma*v/x_eq` 인데 그 rung 당
정밀도는 **양쪽 누구도 측정한 적이 없다.** 오차 예산이 기대고 있는 ~3 % 가 바로 그
미검증 numpy 값이다.

즉 R5 가 지목한 것은 사소한 라벨 문제가 아니라 **스레드에서 가장 중요한 미검증
숫자**였다.

기록할 것은 그 라벨을 붙인 쪽의 판단이 아니다 — `hard: false` 는 **강제된** 것이고(그러지
않으면 R5 가 에러다), `gaps[]` 는 남은 유일하게 정직한 자리였다. 기록할 것은 **형태**다:
규칙은 `sigma_gamma_per_rung` 이 하중을 받는다는 것을 알 수 없었고, 그것이 **선언 없이
집으로 돌아왔다**는 것만 알 수 있었다. 그런데 4라운드 뒤에 그것으로 충분했다. 숫자를
지목하되 순위를 매기지 않는 경고가 **양쪽의 순위 판단을 이겼다** — 주 경로가 drag slope
인 동안 양쪽 다 4라운드를 `f_c` 에 썼기 때문이다.

이것이 soft 경고를 남겨두는 논거다. 순위를 매길 수 없는 규칙도 지목은 할 수 있고,
지목만으로도 값을 한다.

## R11 — 라운드를 건너 드리프트한 복사본

이 스레드가 실제로 낳은 결함 두 개는 서로 다른 사고가 아니라 **한 가지 형태**다.
`2 D t_exp / 3` 은 r1 에서 틀렸고 세 라운드 뒤에도 틀려 있었다 — 이후 모든 문서가
복사했기 때문이다. r1 의 여섯 `tier` 값은 자기 `evidence` 에서 유도되지 않았고 같은
방식으로 r2·r3·r5 로 번졌다. **각 문서는 조심스러웠고, 문서 사이를 검사하는 것이
아무것도 없었다.** 두 건이면 이 스레드의 우연이라고 부르기 어렵다.

판별자는 `origin` 이다:

| | 뜻 | R11 |
|---|---|---|
| 같은 symbol, **같은 origin** | 뒤의 것은 앞의 것의 **복사본** | 일치해야 한다 — 어기면 **에러** |
| 같은 symbol, **다른 origin** | 양쪽이 **독립 도출** | 보고만 한다. AM 의 `f_c = 9.9 Hz` 대 BD 의 `9.86 Hz` 는 왕복 검사가 통과한 것이고 결함이 아니다 |

어느 문서의 `corrects[]` 가 지목한 불일치는 **선언된 supersession** 이므로 면제된다 —
`corrects[]` 가 존재하는 이유가 그것이다.

**`corrects[].downstream` 이 R11 의 하중을 받는다.** 그 필드는 "의존물을 지목하지 않는
정정은 그것들을 조용히 틀린 상태로 남긴다"는 **논증**만으로 필수화됐고, R11 은 두 커밋
뒤에 따로 설계됐다. 그런데 이제 R11 이 그 논증을 **권고가 아니라 사실로 만드는
메커니즘**이다: r4 는 `downstream` 을 채웠기 때문에 깨끗하고, 채우지 않았다면 지금
`blur_on_var_x` 가 r1↔r4 에서 에러를 낸다. 독립적으로 설계된 두 개가 만났고, 이 문장은
그게 우연이 아니라 같은 요구의 두 얼굴이었다는 기록이다.

`R11_TOL = 1e-3`. 나중 라운드에서 `kT` 를 다시 계산하고 한 자리 더 찍으면 상대 1e-4
움직이고, 이 규칙이 노리는 드리프트는 배수다 (`2u/3` 대 `u/3` 는 2배). 이 스레드가
실제로 만든 잡음보다 두 자리 위, 실제 드리프트보다 세 자리 아래다.

## `evidence` 가 권위이고 `tier` 는 비규범이다

보내는 쪽은 `evidence` 만 쓴다. `tier` 는 **받는 쪽이 유도**하고, 와이어에 실린 값은
무시된다. 일반적으로 유도 자체가 불가능하기 때문이다 — `computed` 는 입력 중 최악
tier 를 상속하는데 와이어는 입력을 나르지 않는다. 그리고 실제로 조용히 갈라졌다:
r1–r5 에서 `computed` 한 클래스가 tier 1·2·3 **세 값 전부**로 실렸고, tier 2 인 것들은
전부 r1 의 여섯 값에서 나와 이후 세 라운드로 복사되어 번졌다. BD 척도의 tier 2 는
"문헌, 미검증" 인데 `trapping/goa.py` 의 모델 출력은 그게 아니다 — **보내는 쪽이 받는
쪽의 어휘를 다른 뜻으로 쓰고 있었고 아무도 검사하지 않았다.**

R8 이 유도 불가능한 tier 에 경고한다. 새 문서에는 `tier` 를 넣지 말 것. T1 은
`validate.py` 의 `T1` 딕셔너리가 유일한 사본이고, `computed` 가 `{1, 3}` 인 것은
범위가 실제로 범위이기 때문이다.

## 한 엔트리에 증거가 여러 종류인 것이 정상이다

`evidence_class` 하나로는 거짓말이 된다. r1 의 수입 엔트리는 `d`·`pixel_size`(진짜
측정)와 `T`(가정 — AM 자신의 P3 이 온도계를 기다리며 막고 있다), `eta`(그 가정에서
계산), `k_t`(모델 출력)를 **같이** 담고 있었는데 frontmatter 는 `measured` 라고 적혀
있었다. 본문 표는 맞게 적혀 있었지만, **인용이 표면에 드러내는 것은 경로와
frontmatter 이고 본문 표가 아니다.**

`evidence_classes: {symbol: evidence}` 맵을 쓰고, `evidence_class` 는 그 맵의 **최악**을
적는다 (R10, 순서: measured = handbook < computed < simulated = round_trip < assumed).
최악만 남기고 맵을 버리면 `d` 와 `pixel_size` 가 진짜 측정이라는 사실이 사라진다.

## R4 는 status 를 보지 않는다

미해결 가정은 **미해결이라고 선언**되어야 한다 — "문서가 draft 여야 한다"가 아니다.
둘은 다른 주장이고, 합쳐 놓으면 정정이 막힌다: `supersedes_prior` 는 정정이 순번을
기다리지 않게 하려고 있는데, 거기에 `draft` 를 같이 요구하면 **정정 문서가 새로 발견한
unknown 을 실을 수 없다.** 실제로 2026-09-15 r4 에서 일어났고, BD 는 내용을 약화시키는
대신 그 항목을 `findings[]` 로 옮겼다 — 선언되지 않은 가정을 불일치로 접수한 것이고,
R4 가 존재하는 이유가 바로 그 둘이 다르다는 것이다.

원인은 carve-out 이 필요한 게 아니라 **`status` 가 직교하는 두 사실을 나르고 있었던**
것이다: 문서의 수명주기 위치와, 가정이 모두 선언되었는지. 이제 분리되어 있다.

    assumptions_resolved: false     # 어떤 status 와도 함께 쓸 수 있다
    status: draft                   # 예전 방식, 여전히 유효 (하위호환)

`fixtures/valid/c6-correction-with-unknown.json` 이 이 완화의 회귀 가드다.
`fixtures/invalid/` 는 규칙이 아직 무는지를 증명하고, `fixtures/valid/` 는 규칙이 허용해야
할 것을 물지 않는지를 증명한다.

## 스킵된 규칙은 통과한 규칙이 아니다

`--selftest` 에서는 `jsonschema` / `referencing` / `PyYAML` 의 부재가 **경고가 아니라
에러**다. BD 의 simulation_bot 인터프리터에는 jsonschema 가 없어서 거기서 돌린
`--selftest` 가 R1 을 한 번도 실행하지 않은 채 "selftest clean" 을 출력했다. 규칙 하나가
꺼진 상태로 clean 을 보고하는 검사기는 두 리포가 계속 적어두고 있는 바로 그 실패다.
selftest 는 이제 첫 줄에 인터프리터 경로를 찍는다.

## 정정은 순번을 따르지 않는다

라운드 순번(홀수 = 실험, 짝수 = 시뮬)은 **새 질문**에만 적용된다. 자기가 앞서 낸
답이 틀렸다는 걸 발견한 쪽은 순번을 기다리지 않고 말한다 — 그걸 말할 수 있는 쪽은
그 한 쪽뿐이다. `corrects[]`를 싣고 `status: supersedes_prior`로 보내며, 정정된
문서는 `status: corrected`가 된다.

`corrects[].downstream`은 비워두지 않는다. **의존물을 지목하지 않는 정정은 그것들을
조용히 틀린 상태로 남긴다.** 2026-09-15에 실제로 일어난 일이 그 형태였다: BD가 r2의
+1.17 %가 물리가 아니라 추정기 편향이라는 것을 찾았고, r2의 `T_obs >= 32.3 s`
요구사항은 *그 1.17 %가 `T_obs/tau_k = 2000`에서 측정됐다는 근거로* 존재했다. 편향은
`T_obs`로 줄지 않으므로 그 요구사항의 근거가 사라졌는데, 같은 시각 AM은 이미 r3를
그 위에 쓰고 있었다.

## 리비전 없는 ref는 ref가 아니다

`ref`에 `rev`(커밋 sha, 없으면 브랜치명)를 같이 싣는다. 경로만 있는 참조는 브랜치마다
다른 답을 준다 — 이 스레드의 plan 파일이 실제로 그랬다: `main`에서 `58cfc405`,
`worktree-work-2026-09-16`에서 `514da4a0`, `version2`에는 **아예 없다**. 하나의 ref에
세 가지 답이 나오면 R6의 해시 검사는 무엇을 검사하는지 모르는 상태가 된다.

## Layout

```
schema/
  common.defs.json              quantity · requirement · group · assumption · ref
  ask_simulation.schema.json    AM → BD
  ask_experiment.schema.json    BD → AM
  kb_external_entry.schema.json frontmatter of an imported entry
threads/trap-stiffness-recovery/
  r1/ ask_simulation.{md,json}  AM asks: does the height ladder return h0?
      kb_entry_for_bd.md        …as it lands in BD's knowledge/external/am/
  r2/ ask_experiment.{md,json}  BD answers f_c to 1.17 %, refuses h0
      kb_entry_for_am.md        …as it lands in AM's kb/external/bd/
fixtures/invalid/               one file per rule; see its README
hashes.json                     upstream hashes, for R6
validate.py                     the seven rules
```

Threading is `<thread>/r<N>`, not by title. Titles collide or drift by round 3,
and the commonest failure in a round-trip loop is not that a step was wrong — it
is that after three rounds nobody is asking the original question any more.

## The worked thread

`trap-stiffness-recovery` is real on both sides:
AM's `kb/plans/2026-09-15-drag-calibration-stiffness-vs-size.md` and BD's
`runs/trap-2d-5um__a5ef4f45d589`. Every number in the fixtures is copied from one
of those two, and `hashes.json` holds their actual SHA-256 prefixes.

r1 asks whether a six-rung height ladder recovers `h0` to ±0.195 µm — a figure
AM produced with a toy numpy model that omitted finite `T_obs`, motion blur and
localisation noise. r2 **refuses the headline question** (BD has no wall and one
height) and answers the largest honest sub-question instead, with four findings
that neither repository would have produced alone:

1. The two sampling conventions differ by exactly **2π** — AM's gate wants
   `f_s ≥ 10 f_c` = 99 Hz, BD's convention wants `10/tau_k` = 620 Hz.
2. At the assumed `epsilon = 10 nm` the localisation budget is **already spent**:
   ~8 % on `alpha`, and it is a bias, not a variance.
3. 5 s per rung is `T_obs/tau_k = 310` against the 2000 the 1.17 % was measured
   at — **6.4× short**.
4. Every BD error bar is an **ensemble** error bar over 1000 replicas. One bead
   would scatter ~32× more, so comparing the 1.17 % against a single-bead
   measurement is invalid as stated.

Finding 4 is the one to note: it is BD reporting against its own result.

## Transport — what is actually needed to move a file

Nothing. Both agents are Claude Code sessions with shell and file tools, so a
shared path is the whole mechanism. What needs deciding is *who triggers a
round*, not how bytes move.

| | when it is the right answer |
|---|---|
| **shared directory** | same machine, one operator. Zero new code. Start here. |
| **a third git repo** ← recommended | gives R6 its hashes for free, survives two machines, and makes every round reviewable as a diff |
| **direct call** | **asymmetric and only one way works.** `python cli.py run` is LLM-free, so an AM session can execute BD's simulator directly. The reverse cannot exist: AM ends at hardware and human preconditions. |
| **MCP** | different machines, or when you want a declared tool interface. AM already ships `mcp_server/`. Overkill for file movement alone. |

**Do not load both `CLAUDE.md` files into one session.** AM boots on 416 lines of
`SAFETY.md` plus five hard rules; BD has its own ten principles and a
transcribe-before-interpret intake protocol. Merged, each set dilutes the other
and the refusals that make both repositories trustworthy stop firing. Separate
sessions, shared directory.

And because `confirmed_by` is human-only in both repositories (rule R7), a fully
autonomous loop is not on the table anyway. The bridge's job is to make each
round small enough to review.

## What to build next, per repository

**AM** — emit `plan_experiment_<title>.json` beside the plan (the parsers in
`knowledge/plans.py`, `_section()` and `_table_rows()`, already do most of the
work), add `kb/external/bd/` as a namespace, and extend `plan-check` with one
rule: every number in a prose table must exist in the structured block. That rule
is hard rule 2 made mechanical, so it pays for itself.

**BD** — an adapter `ask_simulation.json → observation.yaml + system.yaml`
(beside `bdbot/intake.py`), the reverse `metrics.json → ask_experiment.json`
using the `groups` and `back_transform` blocks `spec.json` already carries, and
the two cheap gaps from r2: a sampling layer (integrate over `t_exp`, add
Gaussian `epsilon`) and a run at `n_replicas = 1` for per-realisation scatter.
