# SPEC.md — Especificación Técnica (fia-demo-app)

**Estado:** Aprobada por el responsable (2026-09-07).

## Resumen

CLI en Python puro con dos comandos (`greet`, `note`). Cero dependencias.
La razón de existir de este repositorio es demostrar la validación de estado
del kit FIA Harness, no la aplicación en sí.

## Criterios de aceptación

- F0: el repo tiene CI (`harness.yml`) y `src/` + `tests/`; la suite pasa.
- F1: `python -m demo_app greet` imprime un saludo con la hora; hay test real.
- F2: `note save "texto"` escribe `notes.json` validado y `note list` lo lee.

## Fuera de alcance

Cualquier autenticación, red, persistencia compleja o despliegue.
