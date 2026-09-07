# TASK-F0 — Bootstrap del repo, CI inicial y comando que responde

**Objetivo (desde PROGRESS.md):** Bootstrap del repo, CI inicial y comando que responde / Repo con `harness.yml` en verde y `src/` + `tests/`
**Dependencias:** M3

## Qué se hizo

- A. Auditoría: carpeta vacía; se aplicó el protocolo de arranque del kit.
- E. Implementación: creados `src/`, `tests/`, `.github/workflows/harness.yml`,
  `CONTEXT.md`, `PROGRESS.md`, `DECISIONS.md`, `SPEC.md`.
- I. Tests: humo manual (`python -m demo_app greet`) antes de escribir la suite real.

## Validación (Fase K)

- [x] `python task_generator.py --sync` → estado compilado y validado.
- [x] `.github/workflows/harness.yml` presente (enforcement en cada push/PR).

## Informe final (Fase L)

- Resultado: **TAREA COMPLETADA**. Repo con CI de reglas de oro y estructura del proyecto.
