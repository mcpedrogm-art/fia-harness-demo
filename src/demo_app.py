"""fia-demo-app — mini-app de ejemplo que gobierna el kit FIA Harness.

Python 3.8+ estándar, cero dependencias. Su propósito es servir de cobaya
para mostrar el enclavamiento del harness, no ser un producto.
"""

import datetime
import sys


def greet(name: str = "mundo") -> str:
    name = name.strip()
    if not name:
        raise ValueError("el nombre no puede estar vacío")
    now = datetime.datetime.now().strftime("%H:%M:%S")
    return f"Hola, {name}. Son las {now}."


def main(argv=None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    if not argv or argv[0] in ("-h", "--help"):
        print("Uso: python -m demo_app greet [--name NOMBRE]")
        return 0
    if argv[0] != "greet":
        print(f"Comando desconocido: {argv[0]}", file=sys.stderr)
        return 2
    name = "mundo"
    if "--name" in argv:
        idx = argv.index("--name")
        if idx + 1 >= len(argv):
            print("Falta el valor de --name", file=sys.stderr)
            return 2
        name = argv[idx + 1]
    try:
        print(greet(name))
    except ValueError as exc:
        print(str(exc), file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
