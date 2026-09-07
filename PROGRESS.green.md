# PROGRESS.md — Hoja de Ruta e Historial de Fases

**Fase activa:** F2 (pendiente) — preparada para que la intentes cerrar sin su TASK ni su checkpoint: el enclavamiento te lo impide.

## Fases del Proceso (Harness — ver `INICIO_PROYECTO.md`)

| Fase | Objetivo | Entregable | Depende de | Estado |
| --- | --- | --- | --- | --- |
| M0 | Bootstrap del harness y lectura del PRD/MVP (Fase 0) | Plantillas activas, carpetas creadas y CONTEXT.md con el resumen del PRD | — | [x] Listo |
| M1 | Entrevista de Descubrimiento Técnico (Fase 1) | `SECURITY.md` y `AEO_GEO_SEO.md` completados; decisiones registradas en `CONTEXT.md` | M0 | [x] Listo |
| M2 | Especificación Técnica (Fase 2) | `SPEC.md` redactado y aprobado explícitamente por el humano | M1 | [x] Listo |
| M3 | Plan de Fases de Ejecución (Fase 3) | Tabla de fases `F0`-`Fn` añadida más abajo, derivada de `SPEC.md` | M2 | [x] Listo |

## Fases de Ejecución del Proyecto (F0-Fn)

| Fase | Objetivo | Entregable | Depende de | Estado |
| --- | --- | --- | --- | --- |
| F0 | Bootstrap del repo, CI inicial y comando que responde | Repo con `harness.yml` en verde y `src/` + `tests/` | M3 | [x] Listo |
| F1 | Comando `greet` con test real | `python -m demo_app greet` imprime saludo + hora; suite pasa | F0 | [x] Listo |
| F2 | Persistencia local de notas (`note save` / `note list`) | Fichero `notes.json` con validación de entrada | F1 | [ ] Pendiente |

## Checkpoints de Contexto Recientes

- **M0:** Bootstrap del harness ejecutado; plantillas y carpetas creadas; CONTEXT.md generado.
- **M1:** Entrevista resuelta por chat: stack Python puro, sin BBDD, sin superficie pública.
- **M2:** SPEC.md aprobada por el responsable el 2026-09-07.
- **M3:** Plan F0-Fn pegado en esta tabla; primera fase de ejecución F0.
- **F0:** CI `harness.yml` en verde; prueba de humo ejecutada (`python -m demo_app greet`).
- **F1:** Test real añadido y pasado (`python -m unittest discover tests -v` → 2 OK); salida de `greet` verificada.
