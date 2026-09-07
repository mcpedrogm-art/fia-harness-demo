# PROGRESS.md â€” Hoja de Ruta e Historial de Fases

**Fase activa:** F2 (pendiente) â€” preparada para que la intentes cerrar sin su TASK ni su checkpoint: el enclavamiento te lo impide.

## Fases del Proceso (Harness â€” ver `INICIO_PROYECTO.md`)

| Fase | Objetivo | Entregable | Depende de | Estado |
| --- | --- | --- | --- | --- |
| M0 | Bootstrap del harness y lectura del PRD/MVP (Fase 0) | Plantillas activas, carpetas creadas y CONTEXT.md con el resumen del PRD | â€” | [x] Listo |
| M1 | Entrevista de Descubrimiento TÃ©cnico (Fase 1) | `SECURITY.md` y `AEO_GEO_SEO.md` completados; decisiones registradas en `CONTEXT.md` | M0 | [x] Listo |
| M2 | EspecificaciÃ³n TÃ©cnica (Fase 2) | `SPEC.md` redactado y aprobado explÃ­citamente por el humano | M1 | [x] Listo |
| M3 | Plan de Fases de EjecuciÃ³n (Fase 3) | Tabla de fases `F0`-`Fn` aÃ±adida mÃ¡s abajo, derivada de `SPEC.md` | M2 | [x] Listo |

## Fases de EjecuciÃ³n del Proyecto (F0-Fn)

| Fase | Objetivo | Entregable | Depende de | Estado |
| --- | --- | --- | --- | --- |
| F0 | Bootstrap del repo, CI inicial y comando que responde | Repo con `harness.yml` en verde y `src/` + `tests/` | M3 | [x] Listo |
| F1 | Comando `greet` con test real | `python -m demo_app greet` imprime saludo + hora; suite pasa | F0 | [x] Listo |
| F2 | Persistencia local de notas (`note save` / `note list`) | Fichero `notes.json` con validaciÃ³n de entrada | F1 | [x] Listo |

## Checkpoints de Contexto Recientes

- **M0:** Bootstrap del harness ejecutado; plantillas y carpetas creadas; CONTEXT.md generado.
- **M1:** Entrevista resuelta por chat: stack Python puro, sin BBDD, sin superficie pÃºblica.
- **M2:** SPEC.md aprobada por el responsable el 2026-09-07.
- **M3:** Plan F0-Fn pegado en esta tabla; primera fase de ejecuciÃ³n F0.
- **F0:** CI `harness.yml` en verde; prueba de humo ejecutada (`python -m demo_app greet`).
- **F1:** Test real aÃ±adido y pasado (`python -m unittest discover tests -v` â†’ 2 OK); salida de `greet` verificada.
