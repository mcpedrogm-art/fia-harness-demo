#!/usr/bin/env python3
"""
TASK GENERATOR CLI v2 — Automatizador de Tareas para el Harness de Ingeniería de IA
Lee el estado del proyecto (PROGRESS.md, CONTEXT.md) y genera automáticamente el
archivo TASK-Fx.md correspondiente a la fase activa, inyectando los checklists de
seguridad, visibilidad y UI/UX reales según el tipo de fase detectada.

v2 corrige un problema de la v1: el parser asumía una posición fija de columnas y
una comparación de texto exacta (asteriscos, comillas invertidas, espacios) contra
`PROGRESS.md`/`TASK_TEMPLATE.md`. Cualquier variación de formato (p. ej. el código
de fase en negrita `**F1**`, que es justamente lo que genera `bootstrap.py`) hacía
que la extracción devolviera campos vacíos y que la inyección de checklists nunca
se disparara, todo ello SIN avisar de que había fallado.

v2 soluciona esto:
1. Detecta las columnas de la tabla de `PROGRESS.md` por su cabecera, no por su
   posición ni por si el texto está en negrita/código.
2. Inyecta los checklists en marcadores explícitos (`<!-- INJECT:X --> ... <!-- /INJECT -->`)
   colocados en `TASK_TEMPLATE.md`, en vez de intentar reconocer literalmente la
   prosa de la plantilla.
3. Si algo esperado no aparece (marcador ausente, fase no encontrada, PROGRESS.md
   sin fases pendientes...) el script avisa explícitamente por stderr y, cuando
   corresponde, se detiene — nunca rellena con un valor por defecto en silencio.

v3 añade el recorte de la cabecera meta de la plantilla ("# TASK_TEMPLATE.md —
Propósito / Cómo usar esta plantilla"): esas instrucciones son para quien GENERA
la tarea, no para el agente que la ejecuta. El TASK-Fx.md final empieza
directamente en su encabezado "# TASK-...", sin ruido de documentación de
generación (coherente con el principio de ahorro de contexto del harness).

v4 (kit v2 — enforcement) añade la máquina de estado validada: PROGRESS.md sigue
siendo la superficie de edición humana/agente, pero ahora se compila y valida en
`progress.json` (estados de un enum, dependencias existentes, una fase no puede
estar cerrada con dependencias abiertas, cierre de fase F exige su TASK-Fx.md y
su checkpoint, aprobaciones APPROVAL citadas en TASKs deben existir en
DECISIONS.md). Nuevos comandos:
  --sync      compila y valida PROGRESS.md -> progress.json
  --check     valida el estado sin modificar nada (es lo que ejecuta el CI)
  --approval  registra una aprobación humana con sello APPROVAL-NNN en DECISIONS.md
"""

import datetime
import json
import re
import sys
import argparse
from pathlib import Path

STATE_FILE = "progress.json"
SCHEMA_NAME = "harness-state/1"
STATUS_VALUES = ("pending", "in_progress", "blocked", "done")
STATUS_SYMBOLS = {"x": "done", "X": "done", "~": "in_progress", "!": "blocked"}
PHASE_ID_RE = re.compile(r"^[MF]\d+$")
APPROVAL_REF_RE = re.compile(r"APPROVAL-(\d+)")
APPROVAL_ENTRY_RE = re.compile(r"\*\*APPROVAL-(\d+)\*\*")
CHECKPOINT_LINE_RE = re.compile(
    r"^\s*-\s*\*{0,2}([MF]\d+)\*{0,2}(?:\s*\([^)]*\))?\s*:?\s*\*{0,2}\s*(.+)$"
)

DEFAULT_FILES = {
    "context": "CONTEXT.md",
    "progress": "PROGRESS.md",
    "spec": "SPEC.md",
    "security": "SECURITY.md",
    "aeo_geo_seo": "AEO_GEO_SEO.md",
    "ui_ux": "UI_UX_EXCLUSIVA.md",
    "template": "TASK_TEMPLATE.md",
    "template_lite": "TASK_LITE_TEMPLATE.md",
}

# Marcadores de inyección esperados dentro de TASK_TEMPLATE.md.
# El bloque completo <!-- INJECT:X --> ... <!-- /INJECT --> se sustituye entero.
INJECT_MARKERS = {
    "visibility": "VISIBILITY_CHECKLIST",
    "security": "SECURITY_CHECKLIST",
    "ui_ux": "UIUX_CHECKLIST",
}

NOT_APPLICABLE_TEXT = {
    "visibility": "No aplica: esta tarea no toca superficie pública ni contenido indexable.",
    "security": "No aplica: esta tarea no toca auth, datos de usuario, secretos ni infraestructura.",
    "ui_ux": "No aplica: esta tarea no toca UI/UX ni assets visuales.",
}

# Palabras clave para el análisis semántico (heurístico, no sustituye la revisión humana)
SEC_KEYWORDS = ["bbdd", "database", "migracion", "migración", "auth", "login", "password",
                "seguridad", "permisos", "permiso", "rls", "secret", "secreto", "token",
                "api", "servidor", "vps", "infra", "deploy", "despliegue", "credencial"]
VIS_KEYWORDS = ["frontend", "landing", "blog", "docs", "public", "seo", "aeo", "geo",
                "web", "contenido", "despliegue", "deploy"]
UI_KEYWORDS = ["frontend", "ui", "ux", "pantalla", "interfaz", "diseño", "componente",
               "animacion", "animación", "motion", "formulario", "vista", "page"]


def warn(msg: str):
    print(f"   [!] {msg}", file=sys.stderr)


def fail(msg: str):
    print(f"❌ {msg}", file=sys.stderr)
    sys.exit(1)


def strip_md(text: str) -> str:
    """Quita marcado Markdown básico (negrita, cursiva, código) para poder comparar
    texto de forma robusta, independientemente de cómo esté formateado el original."""
    text = re.sub(r"[`*_]", "", text)
    return text.strip()


def load_file(path: Path, required: bool = True) -> str:
    if not path.exists():
        if required:
            fail(f"No se encontró el archivo obligatorio: {path.name}")
        return ""
    return path.read_text(encoding="utf-8")


def strip_template_meta_header(template: str, template_name: str) -> str:
    """Recorta la cabecera meta de la plantilla ('# TASK_..._TEMPLATE.md — Propósito /
    Cómo usar esta plantilla'). Ese bloque documenta CÓMO RELLENAR la plantilla: si
    viaja dentro de cada TASK-Fx.md, el agente ejecutor recibe instrucciones de
    generación que no le aplican. El corte se hace en el primer encabezado '# TASK-'
    (el '_TEMPLATE' de la cabecera meta nunca coincide porque usa guion bajo)."""
    match = re.search(r"^# TASK-", template, re.MULTILINE)
    if not match:
        warn(f"La plantilla {template_name} no contiene ningún encabezado '# TASK-': "
             f"se copia íntegra, incluida su cabecera meta. Revísala a mano.")
        return template
    return template[match.start():]


# ---------------------------------------------------------------------------
# Parsing robusto de la tabla de fases de PROGRESS.md
# ---------------------------------------------------------------------------

def _is_separator_row(line: str) -> bool:
    inner = line.strip().strip("|")
    return bool(inner) and set(inner.replace(" ", "").replace(":", "")) <= {"-"}


def _split_table_blocks(content: str):
    """Divide el documento en bloques de líneas consecutivas que empiezan por '|'.
    Permite que PROGRESS.md tenga varias tablas (p. ej. la de fases M0-M3 del
    proceso y, más abajo, la de fases F0-Fn de ejecución) sin que una tabla
    contamine el mapeo de columnas de la otra."""
    blocks, current = [], []
    for line in content.split("\n"):
        if line.strip().startswith("|"):
            current.append(line)
        else:
            if current:
                blocks.append(current)
                current = []
    if current:
        blocks.append(current)
    return blocks


def parse_progress_table(progress_content: str):
    """Extrae todas las filas de fase (`F<N>` o `M<N>`) de todas las tablas
    presentes en PROGRESS.md, detectando columnas por cabecera en cada tabla por
    separado. Tolera negrita/código y columnas Objetivo/Entregable separadas o
    combinadas en una sola celda."""
    rows = []
    for block in _split_table_blocks(progress_content):
        if len(block) < 2:
            continue
        header_cells = [strip_md(c).lower() for c in block[0].strip().strip("|").split("|")]

        def find_col(*keywords, _headers=header_cells):
            for i, h in enumerate(_headers):
                if any(k in h for k in keywords):
                    return i
            return None

        col = {
            "phase": find_col("fase"),
            "title": find_col("tarea", "hito", "titulo", "título"),
            "status": find_col("estado"),
            "objective": find_col("objetivo"),
            "deliverable": find_col("entregable"),
            "deps": find_col("depend"),
        }
        if col["phase"] is None:
            continue  # este bloque de '|' no es una tabla de fases (p. ej. otra tabla del documento)
        if col["objective"] is not None and col["objective"] == col["deliverable"]:
            col["deliverable"] = None  # misma celda combinada ("Entregable / Objetivo"): no duplicar

        for line in block[1:]:
            if _is_separator_row(line):
                continue
            raw = [c.strip() for c in line.strip().strip("|").split("|")]
            clean = [strip_md(c) for c in raw]
            if col["phase"] >= len(clean):
                continue
            phase_code = clean[col["phase"]]
            if not re.fullmatch(r"[A-Za-z]+\d+", phase_code):
                continue  # fila de cabecera repetida, separador atípico, etc. — se ignora

            def get(colname, cells):
                idx = col.get(colname)
                return cells[idx] if idx is not None and idx < len(cells) else ""

            objective = " / ".join(x for x in (get("objective", clean), get("deliverable", clean)) if x)
            rows.append({
                "phase": phase_code,
                "title": get("title", clean),
                "status_raw": get("status", raw),
                "objective": objective,
                "dependencies": get("deps", clean) or "Ninguna",
            })
    return rows


def is_row_done(row: dict) -> bool:
    return bool(re.search(r"\[\s*[xX]\s*\]", row["status_raw"]))


def detect_next_phase(rows):
    """Solo se auto-detectan fases de EJECUCIÓN (`F<N>`). Las fases de proceso
    (`M<N>`: lectura de PRD, entrevista, SPEC.md, plan de fases) son pasos de
    descubrimiento/documentación de INICIO_PROYECTO.md, no tareas de código —
    generarles un TASK-Mx.md desde TASK_TEMPLATE.md no tendría sentido."""
    for row in rows:
        if re.fullmatch(r"F\d+", row["phase"]) and not is_row_done(row):
            return row["phase"]
    return None


def get_phase_row(rows, phase: str):
    for row in rows:
        if row["phase"] == phase:
            return row
    return None


# ---------------------------------------------------------------------------
# Extracción de secciones completas (listas, tablas, párrafos) por encabezado
# ---------------------------------------------------------------------------

def extract_section(file_content: str, section_title: str) -> str:
    """Devuelve el contenido íntegro (tablas incluidas) bajo el primer encabezado que
    contenga `section_title`, hasta el siguiente encabezado de igual o mayor nivel.
    A diferencia de un filtro por viñeta/checkbox, esto no descarta tablas ni notas."""
    lines = file_content.split("\n")
    captured, capture, header_level = [], False, None
    needle = section_title.lower()

    for line in lines:
        header_match = re.match(r"^(#+)\s+(.*)", line)
        if header_match:
            level = len(header_match.group(1))
            title = strip_md(header_match.group(2)).lower()
            if capture and level <= header_level:
                break
            if not capture and needle in title:
                capture, header_level = True, level
                continue
        if capture:
            captured.append(line)

    return "\n".join(captured).strip()


# ---------------------------------------------------------------------------
# Análisis semántico (heurístico) de requisitos por fase
# ---------------------------------------------------------------------------

def _compile_keyword_regex(keywords):
    # \b exige límite de palabra real: evita falsos positivos como "vista" dentro de
    # "entrevista", o "api" dentro de "rápido" (aunque en ese caso ni coincidiría, es
    # el mismo tipo de error que sí ocurría por subcadena simple).
    return re.compile(r"\b(?:" + "|".join(re.escape(k) for k in keywords) + r")\b", re.IGNORECASE)


_SEC_RE = _compile_keyword_regex(SEC_KEYWORDS)
_VIS_RE = _compile_keyword_regex(VIS_KEYWORDS)
_UI_RE = _compile_keyword_regex(UI_KEYWORDS)


# ---------------------------------------------------------------------------
# Estado del harness: PROGRESS.md (superficie de edición) <-> progress.json
# (artefacto compilado y validado, el que verifica el CI)
# ---------------------------------------------------------------------------

def phase_status(status_raw: str) -> str:
    """Traduce la casilla Markdown ([x], [~], [!], [ ]) a un estado del enum."""
    match = re.search(r"\[\s*([xX~!])\s*\]", status_raw or "")
    return STATUS_SYMBOLS[match.group(1)] if match else "pending"


def _split_dependencies(raw: str):
    """Separa la celda 'Depende de' en identificadores de fase validables y notas
    de texto libre ('SPEC aprobado' es una nota, no una fase)."""
    tokens = [t.strip() for t in re.split(r"[/,;]", raw or "") if t.strip()]
    ids = [t.upper() for t in tokens if PHASE_ID_RE.match(t.upper())]
    notes = [t for t in tokens if t.upper() not in {i.upper() for i in ids}]
    return ids, notes


def _extract_checkpoints(md_text: str):
    """Extrae los checkpoints de contexto (- **F1 (...):** resumen) de las secciones
    de checkpoints de PROGRESS.md. Son la evidencia del Definition of Done."""
    checkpoints, in_section = [], False
    for line in md_text.split("\n"):
        header = re.match(r"^(#+)\s+(.*)", line)
        if header:
            in_section = "checkpoint" in header.group(2).lower()
            continue
        if not in_section:
            continue
        match = CHECKPOINT_LINE_RE.match(line)
        if match:
            checkpoints.append({"phase": match.group(1).upper(),
                                "summary": match.group(2).strip()})
    return checkpoints


def compile_state_from_md(md_text: str, updated: str = None) -> dict:
    """Compila PROGRESS.md al modelo de estado validable."""
    process, execution, seen = [], [], set()
    for row in parse_progress_table(md_text):
        phase_id = row["phase"].upper()
        if phase_id in seen:
            continue  # duplicados: los detecta validate_state sobre el MD recompilado
        seen.add(phase_id)
        ids, notes = _split_dependencies(row["dependencies"])
        entry = {
            "id": phase_id,
            "title": row["title"],
            "objective": row["objective"],
            "depends_on": ids,
            "depends_on_notes": " / ".join(notes),
            "status": phase_status(row["status_raw"]),
        }
        (process if phase_id.startswith("M") else execution).append(entry)
    state = {
        "schema": SCHEMA_NAME,
        "process_phases": process,
        "execution_phases": execution,
        "checkpoints": _extract_checkpoints(md_text),
    }
    if updated:
        state["updated"] = updated
    return state


def state_fingerprint(state: dict) -> str:
    """Huella canónica del estado, ignorando metadatos volátiles ('updated')."""
    relevant = {k: v for k, v in state.items() if k != "updated"}
    return json.dumps(relevant, sort_keys=True, ensure_ascii=False)


def validate_state(state: dict, project_dir: Path):
    """Devuelve la lista de violaciones de las reglas de oro detectables por máquina.
    Lista vacía = estado coherente. Nunca modifica nada."""
    errors = []
    if state.get("schema") != SCHEMA_NAME:
        errors.append(f"'schema' debe ser '{SCHEMA_NAME}' (encontrado: {state.get('schema')!r})")

    phases = {}
    for key in ("process_phases", "execution_phases"):
        for phase in state.get(key, []):
            phase_id = phase.get("id", "")
            if not PHASE_ID_RE.match(phase_id):
                errors.append(f"Identificador de fase inválido: {phase_id!r}")
                continue
            if phase_id in phases:
                errors.append(f"Fase duplicada: {phase_id}")
            phases[phase_id] = phase
            if phase.get("status") not in STATUS_VALUES:
                errors.append(f"{phase_id}: estado {phase.get('status')!r} no válido "
                              f"(valores: {', '.join(STATUS_VALUES)})")

    # Regla de oro nº4/5: no se cierra una fase con dependencias abiertas
    for phase_id, phase in phases.items():
        for dep in phase.get("depends_on", []):
            if dep not in phases:
                errors.append(f"{phase_id} depende de {dep}, que no existe en el estado")
            elif phase.get("status") == "done" and phases[dep].get("status") != "done":
                errors.append(f"{phase_id} está cerrada pero su dependencia {dep} no — "
                              f"nunca cerrar una fase sin cerrar las previas (Regla de Oro nº4)")

    checkpoint_ids = {c.get("phase") for c in state.get("checkpoints", [])}
    for phase_id, phase in phases.items():
        if phase.get("status") == "done" and phase_id not in checkpoint_ids:
            errors.append(f"{phase_id} está cerrada sin checkpoint de contexto en PROGRESS.md "
                          f"(Definition of Done; añade '- **{phase_id}:** resumen' en la sección de checkpoints)")

    # Regla de oro nº7: ninguna fase de ejecución se cierra sin su TASK-Fx.md
    for phase_id, phase in phases.items():
        if phase.get("status") == "done" and phase_id.startswith("F"):
            if not (project_dir / f"TASK-{phase_id}.md").exists():
                errors.append(f"{phase_id} está cerrada pero no existe TASK-{phase_id}.md — "
                              f"nunca ejecutar una fase sin su TASK (Regla de Oro nº7)")

    # Aprobaciones con sello: lo que una TASK cita debe existir en DECISIONS.md,
    # y toda entrada registrada debe estar completa (fecha, acción, aprobador).
    approvals_defined = set()
    decisions_path = project_dir / "DECISIONS.md"
    if decisions_path.exists():
        for line in decisions_path.read_text(encoding="utf-8").splitlines():
            match = APPROVAL_ENTRY_RE.search(line)
            if not match:
                continue
            approvals_defined.add(match.group(1))
            if (not re.search(r"\d{4}-\d{2}-\d{2}", line)
                    or "acción" not in line.lower()
                    or "aprobado por" not in line.lower()):
                errors.append(f"APPROVAL-{match.group(1)} en DECISIONS.md está incompleta: "
                              f"necesita fecha (AAAA-MM-DD), 'Acción:' y 'Aprobado por:'")
    for task_file in sorted(project_dir.glob("TASK-*.md")):
        content = task_file.read_text(encoding="utf-8")
        for ref in APPROVAL_REF_RE.findall(content):
            if ref not in approvals_defined:
                errors.append(f"{task_file.name} cita APPROVAL-{ref}, que no está registrada "
                              f"en DECISIONS.md (regístrala con --approval)")
    return errors


def _print_errors_and_fail(errors, mensaje):
    for error in errors:
        print(f"❌ {error}", file=sys.stderr)
    fail(mensaje)


def cmd_sync(project_dir: Path):
    """--sync: compila PROGRESS.md -> progress.json tras validar. Si el estado es
    inválido, no escribe nada (fail-closed)."""
    md_text = load_file(project_dir / DEFAULT_FILES["progress"])
    state = compile_state_from_md(md_text, updated=datetime.date.today().isoformat())
    errors = validate_state(state, project_dir)
    if errors:
        _print_errors_and_fail(
            errors,
            "Estado inválido: corrige PROGRESS.md/DECISIONS.md y vuelve a ejecutar --sync. "
            f"{STATE_FILE} NO se ha escrito.")
    state_path = project_dir / STATE_FILE
    state_path.write_text(json.dumps(state, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"✅ Estado compilado y validado: {state_path}")
    print(f"   {len(state['process_phases'])} fases de proceso · "
          f"{len(state['execution_phases'])} de ejecución · {len(state['checkpoints'])} checkpoints")


def cmd_check(project_dir: Path):
    """--check: valida el estado sin modificar nada. Es el comando que ejecuta el CI
    generado por bootstrap.py (.github/workflows/harness.yml)."""
    md_text = load_file(project_dir / DEFAULT_FILES["progress"])
    compiled = compile_state_from_md(md_text)
    state_path = project_dir / STATE_FILE
    if state_path.exists():
        try:
            stored = json.loads(state_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            fail(f"{STATE_FILE} no es JSON válido ({exc}). Ejecuta: python task_generator.py --sync")
        if state_fingerprint(stored) != state_fingerprint(compiled):
            fail(f"PROGRESS.md y {STATE_FILE} están desincronizados (¿edición manual sin compilar?). "
                 "Ejecuta: python task_generator.py --sync")
        state = stored
    else:
        state = compiled
        warn(f"{STATE_FILE} no existe; validando solo sobre PROGRESS.md. "
             "Ejecuta --sync para generar el artefacto que verifica el CI.")
    errors = validate_state(state, project_dir)
    if errors:
        _print_errors_and_fail(errors, f"Estado del harness inválido: {len(errors)} problema(s).")
    print(f"✅ Estado del harness válido: {len(state.get('process_phases', []))} fases de proceso, "
          f"{len(state.get('execution_phases', []))} de ejecución, "
          f"{len(state.get('checkpoints', []))} checkpoints, aprobaciones íntegras.")


def cmd_approval(project_dir: Path, action: str, phase: str, ref: str, approved_by: str):
    """--approval: registra una aprobación humana con sello rastreable en DECISIONS.md."""
    decisions_path = project_dir / "DECISIONS.md"
    if not decisions_path.exists():
        fail("DECISIONS.md no existe en este proyecto; ejecuta bootstrap.py primero.")
    text = decisions_path.read_text(encoding="utf-8")
    existing = [int(n) for n in APPROVAL_ENTRY_RE.findall(text)]
    new_id = (max(existing) + 1) if existing else 1
    today = datetime.date.today().isoformat()
    parts = [f"**APPROVAL-{new_id:03d}**", f"({today})"]
    if phase:
        parts.append(f"Fase: {phase}")
    parts.append(f"Acción: {action}")
    parts.append(f"Aprobado por: {approved_by}")
    if ref:
        parts.append(f"Ref: {ref}")
    entry_line = "- " + " · ".join(parts)

    lines = text.splitlines()
    heading_index = next((i for i, l in enumerate(lines) if re.match(r"^##\s*Aprobaciones\b", l)), None)
    if heading_index is None:
        lines += ["", "## Aprobaciones", "", entry_line]
    else:
        section_end = next((i for i in range(heading_index + 1, len(lines))
                            if lines[i].startswith("## ")), len(lines))
        lines.insert(section_end, entry_line)
    decisions_path.write_text("\n".join(lines).rstrip("\n") + "\n", encoding="utf-8")
    print(f"✅ Aprobación registrada en DECISIONS.md: APPROVAL-{new_id:03d} ({today})")
    print("   Cita este ID en el informe de la TASK (Fase L, punto 18); --check verifica que exista.")


def analyze_phase_requirements(row: dict) -> dict:
    text = f"{row['title']} {row['objective']}"
    return {
        "security": bool(_SEC_RE.search(text)),
        "visibility": bool(_VIS_RE.search(text)),
        "ui_ux": bool(_UI_RE.search(text)),
    }


# ---------------------------------------------------------------------------
# Inyección basada en marcadores (robusta a cambios de redacción en la plantilla)
# ---------------------------------------------------------------------------

def inject(template: str, marker_key: str, replacement_lines: str):
    """Sustituye el bloque <!-- INJECT:marker_key --> ... <!-- /INJECT --> completo
    por `replacement_lines`. Devuelve (texto_resultante, encontrado)."""
    marker = INJECT_MARKERS[marker_key]
    pattern = re.compile(
        rf"<!--\s*INJECT:{marker}\s*-->.*?<!--\s*/INJECT\s*-->",
        re.DOTALL,
    )
    if not pattern.search(template):
        return template, False
    safe_repl = replacement_lines.replace("\\", "\\\\")
    return pattern.sub(lambda _m: safe_repl, template, count=1), True


def build_security_block(security_content: str) -> str:
    sections = [
        ("Autenticación (AuthN)", "Autenticación"),
        ("Autorización y control de acceso a datos (AuthZ)", "Autorización"),
        ("Gestión de secretos", "Secretos"),
        ("Protección de datos", "Protección de Datos"),
        ("Seguridad de infraestructura", "Infraestructura"),
        ("Skills, MCP, conectores y agentes externos", "Skills / MCP / Conectores"),
        ("Seguridad de instrucciones y prompt injection", "Prompt Injection / Contenido Externo"),
    ]
    parts = ["#### Checklist de Seguridad Obligatorio (extraído en vivo de `SECURITY.md`):"]
    for heading, label in sections:
        block = extract_section(security_content, heading)
        parts.append(f"\n**{label}:**\n{block if block else '_(sección no encontrada en SECURITY.md)_'}")
    return "\n".join(parts)


def build_visibility_block(seo_content: str) -> str:
    sections = [
        ("Checklist técnico transversal", "Transversal"),
        ("Checklist específico SEO", "SEO"),
        ("Checklist específico AEO", "AEO"),
        ("Checklist específico GEO", "GEO"),
    ]
    parts = ["#### Checklist de Visibilidad Activo (extraído en vivo de `AEO_GEO_SEO.md`):"]
    for heading, label in sections:
        block = extract_section(seo_content, heading)
        parts.append(f"\n**{label}:**\n{block if block else '_(sección no encontrada en AEO_GEO_SEO.md)_'}")
    return "\n".join(parts)


def build_ui_ux_block(ui_content: str) -> str:
    sections = [
        ("Gate de entrada", "Gate de Entrada UX"),
        ("Reglas de exclusividad", "Reglas de Originalidad y Exclusividad (Anti-clon)"),
    ]
    parts = ["#### Requisitos de UI/UX Activos (extraídos en vivo de `UI_UX_EXCLUSIVA.md`):"]
    for heading, label in sections:
        block = extract_section(ui_content, heading)
        parts.append(f"\n**{label}:**\n{block if block else '_(sección no encontrada en UI_UX_EXCLUSIVA.md)_'}")
    return "\n".join(parts)


# ---------------------------------------------------------------------------
# Construcción del TASK-Fx.md final
# ---------------------------------------------------------------------------

def _fallback_title(row: dict) -> str:
    """Cuando la tabla de fases no tiene columna de título separada (p. ej. el
    esquema Fase|Objetivo|Entregable|Depende de|Estado de la Fase 3 de
    INICIO_PROYECTO.md), usa el objetivo como título en vez del código de fase
    desnudo ('TASK-F0 — F0' no dice nada; 'TASK-F0 — BOOTSTRAP DEL REPO...' sí)."""
    if row["title"]:
        return row["title"]
    if row["objective"]:
        obj = row["objective"].split(" / ")[0].strip()
        return (obj[:70] + "…") if len(obj) > 70 else obj
    return row["phase"]


def build_task_file(project_dir: Path, row: dict, reqs: dict, use_lite: bool) -> str:
    template_key = "template_lite" if use_lite else "template"
    template_path = project_dir / DEFAULT_FILES[template_key]
    output = strip_template_meta_header(load_file(template_path), DEFAULT_FILES[template_key])

    display_title = _fallback_title(row)

    # Reemplazos básicos de cabecera (mismos para ambas plantillas)
    output = output.replace("<N>", row["phase"])
    output = output.replace("<TÍTULO CORTO DE LA FASE O TAREA>", display_title.upper())
    output = output.replace("<TÍTULO>", display_title.upper())

    obj_text = (
        f"**Objetivo (desde PROGRESS.md):** {row['objective'] or '<pendiente de completar>'}\n"
        f"**Dependencias:** {row['dependencies']}"
    )
    output = output.replace(
        "Construir <funcionalidad> cumpliendo el criterio de aceptación definido en "
        "`SPEC.md`, sección <X>, sin romper lo ya construido en fases previas.",
        obj_text,
    )
    output = output.replace("<funcionalidad>", display_title)

    if template_key != "template":
        # La plantilla Lite no usa el sistema de marcadores <!-- INJECT --> del
        # TASK_TEMPLATE.md completo; el propio TASK_LITE_TEMPLATE.md ya remite a
        # SECURITY.md / UI_UX_EXCLUSIVA.md en su sección 5/6/8, así que aquí no
        # tocamos esas secciones. Ver aviso en el resumen final del script.
        return output

    for key in ("visibility", "security", "ui_ux"):
        applies = reqs[key]
        if applies:
            source_path = project_dir / DEFAULT_FILES[
                {"visibility": "aeo_geo_seo", "security": "security", "ui_ux": "ui_ux"}[key]
            ]
            if not source_path.exists():
                warn(f"{source_path.name} no existe: se marca '{key}' como no verificable.")
                replacement = f"No verificable: falta el archivo `{source_path.name}` en el proyecto."
            else:
                source_content = load_file(source_path)
                builder = {"visibility": build_visibility_block, "security": build_security_block,
                           "ui_ux": build_ui_ux_block}[key]
                replacement = builder(source_content)
        else:
            replacement = NOT_APPLICABLE_TEXT[key]

        output, found = inject(output, key, replacement)
        if not found:
            warn(f"No se encontró el marcador <!-- INJECT:{INJECT_MARKERS[key]} --> en "
                 f"{DEFAULT_FILES['template']}. Esa sección quedó SIN modificar — revísala a mano.")

    return output


def detect_lite_mode(context_content: str, project_dir: Path, forced: bool) -> bool:
    if forced:
        return True
    if (project_dir / "QUICK_CONTEXT.md").exists():
        return True
    # Exige que "Lite" sea el valor declarado justo tras "Modo de trabajo:" (permitiendo
    # negrita/código de Markdown entre medias) — NO basta con que "Lite" se mencione más
    # adelante en la misma línea como una de las opciones posibles (p. ej. "Completo / Lite").
    return bool(re.search(r"modo\s+de\s+trabajo\**\s*:\**\s*lite\b", context_content, re.IGNORECASE))


def main():
    parser = argparse.ArgumentParser(
        description="Generador de TASK-Fx.md y control de estado para el Harness de IA.")
    parser.add_argument("--phase", "-p", type=str, help="Código de fase (ej: F1). Si se omite, se toma la primera fase pendiente de PROGRESS.md.")
    parser.add_argument("--lite", "-l", action="store_true", help="Forzar la plantilla Modo Lite.")
    parser.add_argument("--dir", "-d", type=str, default=".", help="Directorio raíz del proyecto.")
    parser.add_argument("--sync", action="store_true", help="Compila y valida PROGRESS.md en progress.json (artefacto que verifica el CI).")
    parser.add_argument("--check", action="store_true", help="Valida el estado (progreso, TASKs, aprobaciones) sin modificar nada. Es lo que ejecuta el CI.")
    parser.add_argument("--approval", type=str, metavar="ACCION", help="Registra una aprobación humana con sello APPROVAL-NNN en DECISIONS.md.")
    parser.add_argument("--ref", type=str, default="", help="Referencia de la aprobación (chat, PR, reunión) para --approval.")
    parser.add_argument("--approved-by", type=str, default="Humano", help="Quién otorga la aprobación (para --approval).")
    args = parser.parse_args()

    project_dir = Path(args.dir)

    if args.approval:
        cmd_approval(project_dir, args.approval, args.phase, args.ref, args.approved_by)
        return
    if args.sync:
        cmd_sync(project_dir)
        return
    if args.check:
        cmd_check(project_dir)
        return

    progress_content = load_file(project_dir / DEFAULT_FILES["progress"])
    context_content = load_file(project_dir / DEFAULT_FILES["context"], required=False)

    rows = parse_progress_table(progress_content)
    if not rows:
        fail(
            f"No se pudo leer ninguna fase con formato 'F<N>'/'M<N>' en ninguna tabla de "
            f"{DEFAULT_FILES['progress']}. Revisa que exista una tabla Markdown con una "
            f"columna de cabecera que contenga 'Fase'."
        )

    # Auto-sincronización del artefacto de estado: PROGRESS.md es la superficie de
    # edición; si alguien lo editó a mano y diverge de progress.json, se recompila
    # y valida aquí (el CI lo verifica también con --check, sin auto-reparación).
    state_path = project_dir / STATE_FILE
    if state_path.exists():
        try:
            stored = json.loads(state_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            fail(f"{STATE_FILE} no es JSON válido ({exc}). Ejecuta: python task_generator.py --sync")
        compiled = compile_state_from_md(progress_content)
        if state_fingerprint(stored) != state_fingerprint(compiled):
            errors = validate_state(compiled, project_dir)
            if errors:
                _print_errors_and_fail(
                    errors,
                    "PROGRESS.md cambió respecto a progress.json y el nuevo estado es inválido. "
                    "Corrige PROGRESS.md y ejecuta --sync.")
            updated_state = {**compiled, "updated": datetime.date.today().isoformat()}
            state_path.write_text(json.dumps(updated_state, ensure_ascii=False, indent=2) + "\n",
                                  encoding="utf-8")
            warn("PROGRESS.md había cambiado respecto a progress.json: estado recompilado y validado.")

    phase = args.phase
    if phase:
        if re.fullmatch(r"M\d+", phase, re.IGNORECASE):
            fail(
                f"'{phase}' es una fase de PROCESO (lectura de PRD, entrevista, SPEC.md, plan "
                f"de fases), no una fase de ejecución de código. No se genera TASK_TEMPLATE para "
                f"fases M — sigue directamente los pasos de INICIO_PROYECTO.md para esa fase."
            )
        row = get_phase_row(rows, phase)
        if row is None:
            disponibles = ", ".join(r["phase"] for r in rows)
            fail(f"La fase '{phase}' no aparece en {DEFAULT_FILES['progress']}. Fases encontradas: {disponibles}.")
    else:
        phase = detect_next_phase(rows)
        if phase is None:
            f_rows = [r for r in rows if re.fullmatch(r"F\d+", r["phase"])]
            m_rows = [r for r in rows if re.fullmatch(r"M\d+", r["phase"])]
            if not f_rows:
                m_pending = [r["phase"] for r in m_rows if not is_row_done(r)]
                if m_pending:
                    print(f"ℹ️  Todavía no hay tabla de fases de ejecución (F#) en {DEFAULT_FILES['progress']}.")
                    print(f"   Quedan fases de proceso pendientes: {', '.join(m_pending)}.")
                    print("   Complétalas siguiendo INICIO_PROYECTO.md; la Fase M3 debe añadir la tabla F0-Fn.")
                else:
                    print(f"ℹ️  Las fases de proceso (M#) están cerradas pero {DEFAULT_FILES['progress']} "
                          f"todavía no tiene una tabla de fases de ejecución (F#). Añádela en la Fase M3 "
                          f"(ver INICIO_PROYECTO.md, sección 'FASE 3 — Plan de Fases de Ejecución').")
            else:
                print("✅ No queda ninguna fase de ejecución (F#) pendiente en PROGRESS.md. Nada que generar.")
            sys.exit(0)
        print(f"-> Detectada siguiente fase de ejecución pendiente en PROGRESS.md: {phase}")
        row = get_phase_row(rows, phase)

    if not row["objective"]:
        warn(f"No se encontró texto de objetivo/entregable para {phase} en la tabla de PROGRESS.md; "
             f"el TASK generado lo dejará marcado como '<pendiente de completar>'.")

    is_lite = detect_lite_mode(context_content, project_dir, args.lite)

    print(f"-> Analizando requisitos de la fase {phase} ('{_fallback_title(row)}')...")
    reqs = analyze_phase_requirements(row)
    print(f"   - Seguridad: {'SÍ' if reqs['security'] else 'NO'}")
    print(f"   - Visibilidad (SEO/AEO/GEO): {'SÍ' if reqs['visibility'] else 'NO'}")
    print(f"   - UI/UX: {'SÍ' if reqs['ui_ux'] else 'NO'}")
    print("   (heurística por palabras clave: revisa manualmente si el resultado no encaja con la fase real)")

    task_content = build_task_file(project_dir, row, reqs, is_lite)

    task_filename = "TASK-QUICK.md" if is_lite else f"TASK-{phase}.md"
    task_output_path = project_dir / task_filename
    task_output_path.write_text(task_content, encoding="utf-8")

    print(f"\n🎉 Archivo de tarea generado: {task_output_path}")
    print(f"   Modo: {'Lite (TASK-QUICK.md)' if is_lite else 'Completo (' + task_filename + ')'}")
    if is_lite:
        warn("Modo Lite: TASK_LITE_TEMPLATE.md no usa el sistema de marcadores de inyección; "
             "revisa a mano las secciones 5, 6 y 8 contra SKILLS_MCP.md / UI_UX_EXCLUSIVA.md / SECURITY.md.")


if __name__ == "__main__":
    main()
