# 🚦 FIA Harness — Demo: watch the interlock catch the agent

> Real output captured from this repository on 2026-09-15 (FIA Harness v3.0).
> Nothing here is simulated: run the same commands and you get the same lines.

This is a small, real project ([`fia-harness`](https://github.com/mcpedrogm-art/fia-harness)
applied to itself) whose only job is to show what **machine-validated state** and
**verifiable evidence** feel like: a `PROGRESS.md` table that the harness compiles
into `progress.json`, and evidence records (`EV-NNN`) whose artifacts are hashed.
A phase is "done" only when the mechanism agrees — not when the agent says so.

**The cheat that this demo reproduces:** an AI agent tries to close phase `F2`
by editing `PROGRESS.md` to `[x] Listo`, with **no `TASK-F2.md`** and **no
checkpoint**. Watch who wins.

---

## Try it in 60 seconds

Requires Python 3.8+ and the v3 kit (`fia-harness>=3`).

```bash
git clone https://github.com/mcpedrogm-art/fia-harness-demo.git
cd fia-harness-demo
pip install "fia-harness>=3"

# 1. Green: state valid, evidence chains verified, approvals intact
fia verify
```

```text
FIA Verification Report

STATE          PASS
DEPENDENCIES   PASS
EVIDENCE       PASS
PROVENANCE     PASS — 2 con procedencia (0 trusted) · 0 solo existencia
SEALS          PASS
SPEC SNAPSHOT  PASS

RESULT
  PASS — merge eligible
```

The same command is the CI gate.
[![Harness status](https://github.com/mcpedrogm-art/fia-harness-demo/actions/workflows/harness.yml/badge.svg)](https://github.com/mcpedrogm-art/fia-harness-demo/actions/workflows/harness.yml)

## Now try to cheat

The repository ships a `PROGRESS.md` where an agent already tried to close `F2`
without evidence (`PROGRESS.F2_tampered.md`). Overwrite the real one and verify:

```bash
cp PROGRESS.F2_tampered.md PROGRESS.md    # Windows: copy PROGRESS.F2_tampered.md PROGRESS.md
fia verify
echo $?                                   # 1 → the merge is blocked
```

```text
STATE          FAIL
DEPENDENCIES   PASS
EVIDENCE       PASS
PROVENANCE     PASS — 2 con procedencia (0 trusted) · 0 solo existencia
SEALS          PASS
SPEC SNAPSHOT  PASS

RESULT
  FAIL — merge blocked

Reasons:
  [STATE] PROGRESS.md y progress.json están desincronizados (deriva)
```

A contract alone would not stop anyone. Here the merge is blocked before code
review even starts.

## The interlock is fail-closed

What if the agent "fixes" the desync by compiling the state? `fia sync` validates
first and **refuses to write** an invalid state:

```bash
fia sync
echo $?                                   # 1 → progress.json was NOT overwritten
```

```text
❌ F2 está cerrada sin checkpoint de contexto en PROGRESS.md (Definition of Done; añade '- **F2:** resumen' en la sección de checkpoints)
❌ F2 está cerrada pero no existe TASK-F2.md — nunca ejecutar una fase sin su TASK (Regla de Oro nº7)
❌ Estado inválido: corrige PROGRESS.md/DECISIONS.md y vuelve a ejecutar --sync. progress.json NO se ha escrito.
```

`progress.json` still says `F2 → pending`. The honest close would be: open `F2`
as a real phase, generate `TASK-F2.md` with `fia task`, execute it, and then mark
it done with its checkpoint and its evidence (`fia run` → `Evidencia: EV-NNN`).

Restore the green state:

```bash
cp PROGRESS.green.md PROGRESS.md          # Windows: copy PROGRESS.green.md PROGRESS.md
fia verify                                # ✅ green again
```

## Evidence with provenance (v3)

The closed phases carry real evidence records, not pasted prose:

```bash
fia evidence
```

```text
EV-001   test   local-run   exit=0 ...  python src/demo_app.py greet --name Ada
EV-002   test   local-run   exit=0 ...  python -m unittest discover tests -v
```

Each record is bound to hashed artifacts (`evidence/EV-*.stdout.txt`,
`evidence/EV-*.stderr.txt`). `fia verify` recomputes those hashes: edit an
artifact and `PROVENANCE` turns red. In CI, the platform's artifact digest anchors
the evidence as `trusted` (`fia evidence --ingest <manifest>`).

## The demo app really works

This is not a toy about nothing: the closed phases (`F0`, `F1`) have real,
tested code behind them.

```bash
python -m unittest discover -s tests -p "test_*.py" -v   # 2 tests OK
python src/demo_app.py greet --name Ada
# Hola, Ada. Son las 12:13:08.
```

## How to read this repository

| File | What it is |
|---|---|
| `PROGRESS.md` | The editable surface: process phases `M0-M3` (done) and execution phases `F0-F2`. |
| `progress.json` | The compiled, machine-validated state (schema `3.0`). CI compares it to `PROGRESS.md` on every push. |
| `evidence/` | Evidence records `EV-NNN` + raw hashed artifacts; `fia verify` validates the chain. |
| `TASK-F0.md`, `TASK-F1.md` | Task files of the phases that are closed. A phase cannot be `done` without its task file. |
| `DECISIONS.md` | ADRs and human approvals (`APPROVAL-001`) that tasks cite; the check verifies the citation exists. |
| `CONTEXT.md` / `SPEC.md` | The living context and the approved spec (the harness method in 2 files). |
| `.github/workflows/harness.yml` | The generated CI: `fia verify` + gitleaks + tests. Your own projects get the same file from `bootstrap.py`. |
| `task_generator.py`, `bootstrap.py` | Thin facades: the implementation lives in the installed `fia-harness` package (ADR-001). |
| `src/demo_app.py`, `tests/test_demo_app.py` | A minimal CLI with a real test — proof the closed phases are not decoration. |

The full control files the kit ships for a real project (`/docs` templates,
`INICIO_PROYECTO.md`, `SECURITY.md`, `AEO_GEO_SEO.md`, …) are intentionally
omitted here to keep the demo small. The kit itself lives in
[`mcpedrogm-art/fia-harness`](https://github.com/mcpedrogm-art/fia-harness).

## License

MIT — like the kit it demonstrates.
