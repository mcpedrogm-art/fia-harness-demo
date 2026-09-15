#!/usr/bin/env python3
"""Fachada de compatibilidad de FIA Harness (v3). La implementación vive en el paquete.

Requiere el paquete instalado:   pip install fia-harness
"""
import sys

try:
    from fia_harness.generators.bootstrap import (
        REQUIRED_TEMPLATES, DEFAULT_FOLDERS, RAG_MODULE_NAME, main)
    from fia_harness.parser.prd import extract_prd_metadata, find_prd_file, NON_PRD_FILES
except ImportError:
    sys.exit("Falta el paquete fia-harness. Instálalo con: pip install fia-harness")

if __name__ == "__main__":
    raise SystemExit(main())
