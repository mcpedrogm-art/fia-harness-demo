# DECISIONS.md — Registro de Decisiones de Arquitectura (ADR)

## Registro

*   **ADR-000:** Uso del kit FIA Harness (control por fases, estado validado por
    máquina, enforcement en CI) para gobernar este proyecto de ejemplo.
*   **ADR-001:** CLI en Python 3.8+ de la librería estándar, sin dependencias,
    para que el ejemplo sea auditable y reproducible igual que el propio kit.

## Aprobaciones

*Registra aquí cada aprobación humana con:*
`python task_generator.py --approval "acción aprobada" --phase F2 --ref "chat/PR"`.
Cada TASK que use capacidades externas debe citar su identificador APPROVAL-NNN
en el informe final (Fase L, punto 18); `task_generator.py --check` verifica que
todo identificador citado exista aquí.

- **APPROVAL-001** (2026-09-07) · Fase: F1 · Acción: Aprobar el alcance del MVP (F0-F2) y el stack Python puro · Aprobado por: Responsable del proyecto · Ref: entrevista M1
