# CONTEXT.md — Resumen Vivo del Proyecto

**Proyecto:** fia-demo-app
**Estado:** Activo · Proyecto de ejemplo que usa el kit FIA Harness

## 1. Visión del Negocio

### Problema que resuelve:
Un CLI mínimo que da la hora y guarda notas locales, usado como *cobaya* para
demostrar el enclavamiento del harness: lo importante no es la app, es que su
estado está validado por máquina.

### Usuario Objetivo:
Desarrolladores que quieren ver el kit funcionando en un proyecto real pequeño.

## 2. Alcance del MVP (Must-Have)

*  [x] F0: Bootstrap del repo, CI inicial y un comando que responde.
*  [x] F1: `fia-demo-app greet` imprime un saludo y la hora (con test real).
*  [ ] F2: `fia-demo-app note` persiste una nota en un JSON local validado.

## 3. Fuera de Alcance (Out of Scope)

*  Auth, roles, base de datos, despliegue. (Si apareciera: promoción a proceso completo.)

## 4. Decisiones Confirmadas (Fase 1)

*   **Stack:** Python 3.8+ estándar (cero dependencias, como el propio kit).
*   **Base de datos:** Ninguna; JSON local en el directorio del usuario.
*   **Seguridad / Auth:** No aplica al MVP; validación de entrada sí.
*   **Visibilidad:** Sin superficie pública — no aplica SEO/AEO/GEO.
*   **Modo de trabajo:** Completo.
