# build.spec — PyInstaller spec for eve-gate-logger
# Edit TESSERACT_DIR if your Tesseract is installed elsewhere.
import os

TESSERACT_DIR = r"C:\Program Files\Tesseract-OCR"

a = Analysis(
    ["main.py"],
    pathex=["."],
    binaries=[
        (os.path.join(TESSERACT_DIR, "tesseract.exe"), "."),
    ],
    datas=[
        (os.path.join(TESSERACT_DIR, "tessdata", "eng.traineddata"), "tessdata"),
        ("esi_ship_types/ship_types.csv", "esi_ship_types"),
    ],
    hiddenimports=["win32gui", "win32con", "PIL._tkinter_finder"],
    hookspath=[],
    noarchive=False,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    name="eve-gate-logger",
    console=True,
    onefile=True,
)
