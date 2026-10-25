"""Compila los .typ de documentacion/ a PDF.
Uso (desde documentacion/):  uv run --python 3.12 --with typst python build.py [nombre ...]
"""
import shutil, sys
from pathlib import Path
import typst

AQUI = Path(__file__).resolve().parent
RAIZ = AQUI.parent
PDF = AQUI / "pdf"
DATOS = AQUI / "datos"
WEB_PDF = RAIZ / "docs" / "pdf"


def preparar_datos():
    DATOS.mkdir(exist_ok=True)
    for origen, destino in [
        (RAIZ / "tiempos" / "cronometro.log", DATOS / "cronometro.log"),
        (RAIZ / "docs" / "data" / "manifest.json", DATOS / "manifest.json"),
    ]:
        if origen.exists():
            shutil.copyfile(origen, destino)
        elif destino.exists():
            destino.unlink()  # evita datos obsoletos
    # el documento 04 lee manifest.json solo si existe; deja marca de presencia
    (DATOS / "manifest.presente").write_text("1" if (DATOS / "manifest.json").exists() else "0")


def main():
    PDF.mkdir(exist_ok=True)
    WEB_PDF.mkdir(parents=True, exist_ok=True)
    preparar_datos()
    filtro = sys.argv[1:]
    for typ in sorted(AQUI.glob("[0-9][0-9]_*.typ")):
        if filtro and not any(f in typ.name for f in filtro):
            continue
        salida = PDF / (typ.stem + ".pdf")
        typst.compile(str(typ), output=str(salida), root=str(AQUI), font_paths=[str(AQUI / "fuentes")])
        shutil.copyfile(salida, WEB_PDF / salida.name)
        print("OK", salida.name)


if __name__ == "__main__":
    main()
