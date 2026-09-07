# 🛤️ FIA Harness — Demo: watch the interlock catch the agent

> Real output captured from this repository on 2026-09-07. Nothing here is
> simulated: run the same commands and you get the same lines.

This is a small, real project ([`fia-harness`](https://github.com/mcpedrogm-art/fia-harness)
applied to itself) whose only job is to show what **machine-validated state**
feels like: a `PROGRESS.md` table that the harness compiles into
`progress.json`, validated on every push by CI. A phase is "done" only when
the mechanism agrees — not when the agent says so.

**The cheat that this demo reproduces:** an AI agent tries to close phase `F2`
by editing `PROGRESS.md` to `[x] Listo`, with **no `TASK-F2.md`** and **no
checkpoint**. Watch who wins.

---

## Try it in 60 seconds

Requires Python 3.8+ (stdlib only, nothing to install).

```bash
git clone https://github.com/mcpedrogm-art/fia-harness-demo.git
cd fia-harness-demo

# 1. Green: the state is valid, approvals intact
python task_generator.py --check
```

```
✅ Estado del harness válido: 4 fases de proceso, 3 de ejecución, 6 checkpoints, aprobaciones íntegras.
```

The same check is the CI gate. [![Harness status](https://github.com/mcpedrogm-art/fia-harness-demo/actions/workflows/harness.yml/badge.svg)](https://github.com/mcpedrogm-art/fia-harness-demo/actions/workflows/harness.yml)

## Now try to cheat

The repository ships a `PROGRESS.md` where an agent already tried to close `F2`
without evidence (`PROGRESS.F2_tampered.md`). Overwrite the real one and check:

```bash
# 2a. Overwrite PROGRESS.md with the tampered version
copy PROGRESS.F2_tampered.md PROGRESS.md    # Linux/macOS: cp PROGRESS.F2_tampered.md PROGRESS.md

python task_generator.py --check            # what the CI runs on every push
echo $?                                     # 1 → the merge is blocked
```

```
❌ PROGRESS.md y progress.json están desincronizados (¿edición manual sin compilar?). Ejecuta: python task_generator.py --sync
```

A contract alone would not stop anyone. Here the merge is blocked before code
review even starts.

## The interlock is fail-closed

What if the agent "fixes" the desync by running `--sync`? `--sync` validates
first and **refuses to write** an invalid state:

```bash
python task_generator.py --sync
echo $?                                     # 1 → progress.json was NOT overwritten
```

```
❌ F2 está cerrada sin checkpoint de contexto en PROGRESS.md (Definition of Done; añade '- **F2:** resumen' en la sección de checkpoints)
❌ F2 está cerrada pero no existe TASK-F2.md — nunca ejecutar una fase sin su TASK (Regla de Oro nº7)
❌ Estado inválido: corrige PROGRESS.md/DECISIONS.md y vuelve a ejecutar --sync. progress.json NO se ha escrito.
```

`progress.json` still says `F2 → pending`. The honest close would be: open
`F2` as a real phase, generate `TASK-F2.md` with `python task_generator.py`,
execute it, and then mark it done with its checkpoint.

Restore the green state:

```bash
copy PROGRESS.green.md PROGRESS.md          # Linux/macOS: cp PROGRESS.green.md PROGRESS.md
python task_generator.py --check            # ✅ green again
```

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
| `progress.json` | The compiled, machine-validated state. The CI compares it to `PROGRESS.md` on every push. |
| `TASK-F0.md`, `TASK-F1.md` | Task files of the phases that are closed. A phase cannot be `done` without its task file. |
| `DECISIONS.md` | Human approvals (`APPROVAL-001`) that tasks cite; the check verifies the citation exists. |
| `CONTEXT.md` / `SPEC.md` | The living context and the approved spec (the harness method in 2 files). |
| `.github/workflows/harness.yml` | The generated CI: state check + gitleaks + tests. Your own projects get the same file from `bootstrap.py`. |
| `task_generator.py` | The single tool: `--sync` / `--check` / task generation. Stdlib only. |
| `src/demo_app.py`, `tests/test_demo_app.py` | A minimal CLI with a real test — proof the closed phases are not decoration. |

The full control files the kit ships for a real project (`/docs` templates,
`INICIO_PROYECTO.md`, `SECURITY.md`, `AEO_GEO_SEO.md`, …) are intentionally
omitted here to keep the demo small. The kit itself lives in
[`mcpedrogm-art/fia-harness`](https://github.com/mcpedrogm-art/fia-harness).

## License

MIT — like the kit it demonstrates.
