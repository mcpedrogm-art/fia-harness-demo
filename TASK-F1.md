# TASK-F1 — Comando `greet` con test real

**Objetivo (desde PROGRESS.md):** Comando `greet` con test real / `python -m demo_app greet` imprime saludo + hora; suite pasa
**Dependencias:** F0

## Qué se hizo

- A. Auditoría: F0 dejó `src/` + `tests/` vacíos con `.gitkeep`.
- B. Diseño: módulo `src/demo_app.py` con `greet()` puro (sin I/O) y `main()`.
- E. Implementación: comando `greet`; entrada `--name` validada (longitud > 0).
- F. Edge cases: nombre vacío → mensaje de error claro y exit code != 0.
- I. Tests: `tests/test_demo_app.py` con 2 casos reales.

## Validación (Fase K)

- [x] `python -m unittest discover tests -v` → 2 tests OK.
- [x] Salida real verificada por terminal (no inventada): imprime saludo y hora.
- [x] `python task_generator.py --check` → estado válido, aprobaciones íntegras (cita APPROVAL-001).

## Informe final (Fase L)

- Resultado: **TAREA COMPLETADA**. Comando `greet` funcionando, con test real y aprobación APPROVAL-001 registrada.
