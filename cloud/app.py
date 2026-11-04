"""Entrada exclusiva da nuvem; o app.py raiz mantém a configuração local."""
import os
import sys
from pathlib import Path

os.environ['TCC_DEPLOYMENT']='cloud'
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from tcc_analyzer.ui.pages import main

main()
