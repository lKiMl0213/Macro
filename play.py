import os
import subprocess
import sys
from pathlib import Path

VENV_DIR = "venv"
MAIN_FILE = "main.py"
REQ_FILE = "requirements.txt"


def run(cmd):
    subprocess.check_call(cmd)


def create_venv():
    if not Path(VENV_DIR).exists():
        print("Criando venv...")
        run([sys.executable, "-m", "venv", VENV_DIR])
    else:
        print("Venv já existe.")


def venv_python():
    if os.name == "nt":
        return os.path.join(VENV_DIR, "Scripts", "python.exe")
    else:
        return os.path.join(VENV_DIR, "bin", "python")


def upgrade_pip():
    py = venv_python()
    print("Atualizando pip...")
    run([py, "-m", "pip", "install", "--upgrade", "pip"])


def install_requirements():
    if Path(REQ_FILE).exists():
        py = venv_python()
        print("Instalando requirements...")
        run([py, "-m", "pip", "install", "-r", REQ_FILE])
    else:
        print("Nenhum requirements.txt encontrado.")


def run_main():
    if Path(MAIN_FILE).exists():
        py = venv_python()
        print(f"Executando {MAIN_FILE}...\n")
        run([py, MAIN_FILE])
    else:
        print("main.py não encontrado.")


def main():
    create_venv()
    upgrade_pip()
    install_requirements()
    run_main()


if __name__ == "__main__":
    main()