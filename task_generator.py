#!/usr/bin/env python3
"""Fachada de compatibilidad de FIA Harness (v3). La implementación vive en el paquete.

Requiere el paquete instalado:   pip install fia-harness
"""
import sys

try:
    from fia_harness.core.state import (
        REQUIRED_SEALED, STATE_FILE, SCHEMA_NAME, STATUS_VALUES,
        compile_state_from_md, state_fingerprint, sha256_hex, validate_state,
        compute_doc_hashes, validate_sealed_docs, validate_spec_snapshot)
    from fia_harness.core.commands import (
        cmd_sync, cmd_check, cmd_seal, cmd_approval, cmd_reopen, cmd_stats)
    from fia_harness.parser.markdown import (
        parse_progress_table, detect_next_phase, get_phase_row, extract_section)
    from fia_harness.core.policy import analyze_phase_requirements
    from fia_harness.generators.task import (
        inject, detect_lite_mode, strip_template_meta_header)
    from fia_harness.legacy import main_task_generator as main
except ImportError:
    sys.exit("Falta el paquete fia-harness. Instálalo con: pip install fia-harness")

if __name__ == "__main__":
    raise SystemExit(main())
