#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Olho de Deus V2 — Sistema de Busca em Base de Dados
Criado por Martins Store
Discord: https://discord.com/invite/ksRpjyrKU6
"""

import os
import sys
import subprocess
import time
import hashlib
import uuid
import json
import re
import urllib.request
import urllib.error
from pathlib import Path
from datetime import datetime

# ──────────────────────────────────────────────
#  URLs DO BOT
# ──────────────────────────────────────────────
BOT_VERIFY_URL = "https://msbot.squareweb.app/api/olhodeus/verify"
BOT_DB_URL     = "https://msbot.squareweb.app/api/olhodeus/db"

# ──────────────────────────────────────────────
#  ATIVAR ANSI NO WINDOWS SEM os.system("color")
#  FIX: os.system() abre janela cmd oculta e causa piscar no .exe
# ──────────────────────────────────────────────
def _ativar_ansi_windows():
    """Ativa suporte a cores ANSI no terminal Windows sem abrir subprocesso."""
    if sys.platform == "win32":
        try:
            import ctypes
            kernel32 = ctypes.windll.kernel32
            # Habilita ENABLE_VIRTUAL_TERMINAL_PROCESSING (0x0004)
            handle = kernel32.GetStdHandle(-11)  # STD_OUTPUT_HANDLE
            mode = ctypes.c_ulong(0)
            kernel32.GetConsoleMode(handle, ctypes.byref(mode))
            kernel32.SetConsoleMode(handle, mode.value | 0x0004)
        except Exception:
            pass

_ativar_ansi_windows()

# ──────────────────────────────────────────────
#  CORES ANSI (Windows 10+ / Win11)
# ──────────────────────────────────────────────
RESET   = "\033[0m"
BOLD    = "\033[1m"
PURPLE  = "\033[38;5;129m"
VIOLET  = "\033[38;5;135m"
LPURP   = "\033[38;5;141m"
WHITE   = "\033[97m"
CYAN    = "\033[96m"
GREEN   = "\033[92m"
YELLOW  = "\033[93m"
RED     = "\033[91m"
GRAY    = "\033[90m"
DIM     = "\033[2m"

# ──────────────────────────────────────────────
#  ASCII ART — OLHO (piscante na abertura)
# ──────────────────────────────────────────────

EYE_OPEN = (
"⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀\n"
"⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀\n"
"⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀\n"
"⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀\n"
"⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀\n"
"⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀\n"
"⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀\n"
"⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⡄⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀\n"
"⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⡇⠀⠀⠀⠈⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀\n"
"⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⡇⡀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀\n"
"⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠄⢰⠇⠀⠀⠠⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠠⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀\n"
"⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢸⢸⠀⠀⠂⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠄⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀\n"
"⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠠⠀⠀⠀⠁⠀⠀⠀⠀⡇⢸⢸⡇⠇⢀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀\n"
"⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢀⠀⠀⠇⢀⡇⢸⣸⠀⠀⠀⠀⠀⠀⠀⠁⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀\n"
"⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠈⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠂⠀⠀⠀⠀⠀⠀⠀⠀⠀⢸⢀⠀⠃⢸⢠⢸⣿⢸⠀⠀⠀⠠⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠁⠀⠀⠐⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀\n"
"⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⡀⠰⠀⠀⠀⠀⠀⠀⠀⠀⠄⠀⠀⠀⠀⢸⢸⢠⠀⣾⢸⢸⣿⢸⢀⢠⠀⡆⡇⠀⠀⠐⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀\n"
"⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠁⠀⠀⠀⠀⢃⠀⢀⠀⠀⠀⢀⠀⠀⠀⠀⠀⠁⠘⢸⢸⠀⡏⣿⢸⣿⢸⡘⢸⡀⡇⡇⡀⠀⠀⠀⠄⠀⠀⠀⠃⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀\n"
"⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⣀⠀⢄⠀⠀⢀⠀⠀⢢⡀⠀⠀⠀⢰⠀⣸⢸⢴⣇⡟⣾⣿⢸⣿⢸⡇⡇⡇⡇⠰⠀⠀⠀⠈⠀⠀⠀⠀⠀⠀⠁⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀\n"
"⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢀⠀⠐⢄⠘⢄⠀⠣⡀⠀⠑⢄⠀⠱⣄⠁⡄⠆⣇⢿⢸⣾⣿⣇⣿⣿⣼⣿⣸⢷⡇⣼⢀⠀⠀⣠⠊⠀⣠⠆⠀⠀⠀⠁⠡⠎⠀⠈⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀\n"
"⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠈⠢⠀⠀⠀⡑⢄⠀⠁⠀⠑⢄⠙⢦⡀⠢⠙⡦⣈⢧⡻⣜⠼⣜⢯⣿⣿⣿⣿⣿⣿⣿⣿⣼⣹⢣⢣⢡⠞⣁⣴⠞⡁⠀⠀⠀⡠⠀⠀⠤⠀⠀⠀⠀⠀⡠⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀\n"
"⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢀⠀⠀⠀⠀⠀⠒⠤⣀⠑⠢⠬⣽⣒⠤⠈⠒⡦⢭⣟⠚⣩⠰⠊⠁⠀⠀⠀⢀⡀⡀⠀⠀⠀⠀⠀⠀⢀⠀⠉⠓⢮⣝⡳⢻⣭⠖⣋⠠⣀⡴⠞⡩⠄⠚⠁⠀⠀⠄⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀\n"
"⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠈⠀⠀⢀⡀⠈⠀⠀⠀⠈⠁⠒⠀⠬⠍⠛⠛⣚⣩⡆⠋⠁⣀⣴⣶⠏⣠⡞⣡⣶⣶⣶⡄⠀⠀⠀⠀⠀⠻⣷⣦⣀⠈⠛⢶⣬⣓⣒⢛⣃⣉⠠⠔⠀⠠⠂⠁⠀⠀⠀⠠⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀\n"
"⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠂⠠⠀⠀⠀⠈⠁⠐⠢⠤⣁⣒⣒⣛⣂⣶⡟⠟⠉⢀⣤⣾⣿⣿⡏⢠⢶⡃⢿⣿⣿⠿⠁⠀⠀⠀⠀⠀⠀⢹⣿⣿⣷⣤⠀⠈⠻⢯⣟⣂⣂⣒⣒⣒⣈⡩⠥⠐⠈⠁⠀⠀⠠⠀⠈⠉⠁⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀\n"
"⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢀⠀⠀⠀⠀⠈⠉⠉⠉⠀⠐⠒⣒⣛⣿⣿⣛⠉⠀⠀⠠⣾⣿⣿⣿⣿⡅⢊⠎⣹⠀⠉⠁⠀⠀⠀⠀⠀⠀⠀⠀⢸⣿⣿⣿⣿⣷⠀⠀⠀⠉⣛⠒⢲⠆⠡⠤⠤⠤⠒⠒⠀⠈⠀⠀⠀⠀⠀⢀⡀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀\n"
"⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢀⡀⠀⠀⠈⠀⡀⠠⠤⠐⠒⠒⣒⠒⠚⠳⠼⠛⠿⣶⣥⡠⡀⠙⢿⣿⣿⣿⣇⠀⠘⠄⠃⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⣮⣿⣿⣿⠟⠃⠀⢀⣴⣶⠿⠛⢿⣽⣛⠋⣉⣉⠉⠒⠒⠒⠂⠐⠀⠉⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀\n"
"⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠠⠀⠀⠒⠀⠩⠉⠀⠉⠉⢑⡚⢛⢋⠸⠝⠿⣮⣔⠄⡈⠛⠿⣿⣄⠈⠀⠁⠂⠄⠀⠀⠀⠀⠀⠀⢀⣼⣿⠿⠛⢁⢀⣠⣾⡻⠯⠭⣉⡙⠓⠚⠥⢄⡀⠀⠀⠈⠉⠐⠒⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀\n"
"⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢀⠀⠀⠤⠄⠀⠤⠐⠀⠈⢉⡠⠄⣀⠤⠒⣈⡭⠾⢙⡿⣾⣤⣂⠀⣉⠑⠀⠀⠀⠀⠀⠀⠀⠀⠀⠐⠊⣉⠠⣀⣬⡶⢿⣟⠯⢍⡛⠶⡤⠉⠑⠢⢄⠀⠀⠉⠀⠂⠠⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀\n"
"⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢀⠀⠒⡡⠔⠈⠀⠢⠋⠁⠂⠀⣡⠴⢃⣵⢟⡟⣷⣾⣿⣶⣶⣤⣤⣤⣴⣶⣦⣬⡷⣶⢿⢯⡳⣌⠢⢍⠛⠦⠌⠑⠠⠀⠀⠲⠤⡉⠢⠀⠈⠀⡀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀\n"
"⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠠⠀⠀⠀⠀⠀⠀⠊⠀⠀⠀⠀⠄⠀⠀⠁⠘⢁⢀⠔⠁⠁⣽⢣⣇⡏⡏⣿⡟⣿⣿⢿⣿⣿⢸⡵⢹⣯⠆⠑⢜⢣⡀⠉⠢⣈⠂⠀⠀⠀⠀⠀⠀⠂⡀⠀⠀⠀⠑⢄⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀\n"
"⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠂⠀⠀⠀⠀⠀⠀⠀⠔⠀⠀⡠⠈⠀⠀⠀⣰⠑⢸⣹⢹⢿⣿⡇⣿⣿⢸⡟⢸⠈⣷⠁⠙⢇⠀⠀⠀⠙⢦⡀⠈⠃⢄⠀⠀⠀⠐⠀⠀⠀⠀⠀⠄⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀\n"
"⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠐⠀⡀⠁⠀⠀⠀⠀⠀⠀⠀⠁⠃⠇⢸⢸⢸⠸⡏⡇⢸⣿⢸⣧⢨⠀⡝⡏⠀⠈⠂⠀⠀⠀⢀⠀⠀⠀⡀⠑⡀⠀⠀⠀⠈⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀\n"
"⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠒⠀⠀⠀⠀⠀⠀⡸⢸⢸⠀⣧⢿⢸⣿⠀⣿⠈⠀⠇⡇⠀⠀⠀⠐⠀⠀⠀⠀⠀⠀⠀⠀⠈⠄⠀⠀⠀⠄⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀\n"
"⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠈⠀⢀⠀⢁⠘⠀⡀⠸⡌⢸⣿⠀⡏⠀⢀⠀⡄⠀⣤⠀⠀⠀⠐⠀⠀⠀⠀⠀⢠⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀\n"
"⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠐⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢸⠀⡀⠇⠸⠃⢸⣿⠀⠇⠀⠀⢰⠀⠀⠀⠀⠀⠀⠀⠈⠀⠂⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀\n"
"⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⡀⠀⢀⠀⠀⠀⠁⠀⠂⠸⡟⠀⠀⠀⠀⠂⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠠⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀\n"
"⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠁⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠁⠀⠀⠀⠀⠀⠂⠀⠀⠀⡇⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⡀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀\n"
)

EYE_CLOSED = "\n".join(["⠀" * 99] * 50)

# ──────────────────────────────────────────────
#  TÍTULO FIXO DO MENU
# ──────────────────────────────────────────────

OLHO_TITLE = f"""{PURPLE}
  ___  _    _  _  ___     ___  ___     ___  ___ _   _ ___ 
 / _ \| |  | || ||   \   |   \|   |   |   \| __| | | / __|
| (_) | |__| || || () |  | |) | |_|   | |) | _|| |_| \__ \\
 \___/ \____/|___||___/   |___/|___|   |___/|___|\___/|___/
{VIOLET}
 __   ___  _   ___ 
 \ \ / / || | |_  )
  \ V /\_  _|  / / 
   \_/   |_|  /___|
{RESET}"""

TITLE_BOX = f"""
{PURPLE}  ╔══════════════════════════════════════════════════════╗
{PURPLE}  ║   {WHITE}{BOLD}          ◉  OLHO DE DEUS V2  ◉             {RESET}{PURPLE}   ║
{PURPLE}  ║   {VIOLET}     SISTEMA DE BUSCA EM BASE DE DADOS           {PURPLE}  ║
{PURPLE}  ╚══════════════════════════════════════════════════════╝{RESET}"""

DISCORD_LINE = f"""
{PURPLE}  ╔══════════════════════════════════════════════════════╗
{PURPLE}  ║  {WHITE}Discord: {CYAN}https://discord.com/invite/ksRpjyrKU6{PURPLE}  ║
{PURPLE}  ╚══════════════════════════════════════════════════════╝{RESET}
"""

SEPARATOR = f"{PURPLE}  {'═'*54}{RESET}"

# ──────────────────────────────────────────────
#  SISTEMA DE LICENÇA
# ──────────────────────────────────────────────

LICENSE_FILE = Path(os.environ.get("APPDATA", "")) / "OlhoDeus" / "license.dat"

# Flag para suprimir janelas no Windows (evita piscar ao compilar .exe)
_NO_WINDOW = subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0


def _hardware_id() -> str:
    """Gera ID único do hardware (MAC + volume serial)."""
    mac = hex(uuid.getnode()).replace("0x", "").upper()
    try:
        # FIX: CREATE_NO_WINDOW evita janela cmd piscando no .exe compilado
        vol = subprocess.run(
            "vol C:", shell=True, capture_output=True, text=True,
            creationflags=_NO_WINDOW
        ).stdout
        serial = "".join(filter(str.isalnum, vol))[-8:]
    except Exception:
        serial = "00000000"
    raw = f"{mac}-{serial}"
    return hashlib.sha256(raw.encode()).hexdigest()[:16].upper()


def _formatar_hwid(raw: str) -> str:
    raw = raw.upper().replace("-", "").replace(" ", "")
    return "-".join(raw[i:i+4] for i in range(0, min(len(raw), 16), 4))


def _verificar_servidor(hwid: str) -> dict:
    try:
        payload = json.dumps({"hwid": hwid}).encode("utf-8")
        req = urllib.request.Request(
            BOT_VERIFY_URL,
            data=payload,
            headers={"Content-Type": "application/json"},
            method="POST"
        )
        with urllib.request.urlopen(req, timeout=10) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        try:
            return json.loads(e.read().decode("utf-8"))
        except Exception:
            return {"authorized": False, "reason": f"Erro HTTP {e.code}"}
    except Exception as ex:
        return {"authorized": False, "reason": f"Sem conexão com servidor: {ex}"}


def _salvar_cache(hwid: str):
    LICENSE_FILE.parent.mkdir(parents=True, exist_ok=True)
    dados = {"hwid": hwid, "verified_at": time.time()}
    LICENSE_FILE.write_text(json.dumps(dados))


def _cache_valido() -> bool:
    try:
        if not LICENSE_FILE.exists():
            return False
        dados = json.loads(LICENSE_FILE.read_text())
        hwid_cache = dados.get("hwid", "")
        verified_at = dados.get("verified_at", 0)
        if hwid_cache != _hardware_id():
            return False
        return (time.time() - verified_at) < 86400
    except Exception:
        return False


def tela_ativacao():
    """Mostra tela de ativação — usuário deve ativar pelo Discord."""
    clear()
    print(TITLE_BOX)
    hwid     = _hardware_id()
    hwid_fmt = _formatar_hwid(hwid)
    print(f"""
{PURPLE}  ╔══════════════════════════════════════════════════════╗
{PURPLE}  ║          {WHITE}ATIVAÇÃO DE LICENÇA — OLHO DE DEUS V2{PURPLE}    ║
{PURPLE}  ╠══════════════════════════════════════════════════════╣
{PURPLE}  ║                                                      ║
{PURPLE}  ║  {YELLOW}Este PC ainda não está ativado.{PURPLE}                   ║
{PURPLE}  ║  {WHITE}Adquira sua licença:{CYAN} discord.com/invite/ksRpjyrKU6{PURPLE}║
{PURPLE}  ║                                                      ║
{PURPLE}  ╠══════════════════════════════════════════════════════╣
{PURPLE}  ║                                                      ║
{PURPLE}  ║  {WHITE}COMO ATIVAR:{PURPLE}                                      ║
{PURPLE}  ║  {CYAN}1.{WHITE} Compre o Olho de Deus V2 na nossa loja.        {PURPLE}║
{PURPLE}  ║  {CYAN}2.{WHITE} Acesse o canal de ativação no Discord.         {PURPLE}║
{PURPLE}  ║  {CYAN}3.{WHITE} Clique em "Ativar Licença".                    {PURPLE}║
{PURPLE}  ║  {CYAN}4.{WHITE} Digite o ID do seu PC abaixo.                  {PURPLE}║
{PURPLE}  ║  {CYAN}5.{WHITE} Abra o Olho de Deus V2 novamente.              {PURPLE}║
{PURPLE}  ║                                                      ║
{PURPLE}  ╚══════════════════════════════════════════════════════╝{RESET}
""")
    print(f"  {GRAY}ID do seu PC:{RESET}")
    print(f"  {WHITE}{BOLD}  {hwid_fmt}{RESET}")
    print(f"  {GRAY}(Copie este ID e informe no canal de ativação do Discord){RESET}\n")
    print(f"{PURPLE}  Suporte: discord.com/invite/ksRpjyrKU6{RESET}\n")
    input(f"  {GRAY}Pressione ENTER para sair...{RESET}")
    sys.exit(1)


def verificar_licenca() -> str:
    """Verifica licença e retorna o HWID para uso nas chamadas da API."""
    hwid = _hardware_id()

    if _cache_valido():
        return hwid

    clear()
    print(TITLE_BOX)
    print(f"\n  {CYAN}Verificando licença...{RESET}\n")
    resultado = _verificar_servidor(hwid)

    if resultado.get("authorized"):
        _salvar_cache(hwid)
        username = resultado.get("username", "")
        print(f"  {GREEN}✔ Licença válida!{WHITE} Bem-vindo, {username or 'usuário'}!{RESET}")
        time.sleep(1.5)
        return hwid
    else:
        motivo = resultado.get("reason", "Não autorizado.")
        if "Sem conexão" in motivo and LICENSE_FILE.exists():
            try:
                dados = json.loads(LICENSE_FILE.read_text())
                if dados.get("hwid") == hwid:
                    print(f"  {YELLOW}⚠ Sem conexão com servidor. Usando cache offline.{RESET}")
                    time.sleep(2)
                    return hwid
            except Exception:
                pass
        clear()
        print(TITLE_BOX)
        print(f"\n  {RED}✘ {motivo}{RESET}\n")
        time.sleep(1)
        tela_ativacao()


# ──────────────────────────────────────────────
#  ANIMAÇÃO DO OLHO (abertura)
# ──────────────────────────────────────────────

def animar_olho():
    """Pisca o olho em verde por 5 segundos antes de abrir o menu."""
    start = time.time()
    while time.time() - start < 5:
        # Olho aberto — FIX: usa escape ANSI em vez de os.system("cls")
        print("\033[2J\033[H", end="", flush=True)
        linhas = EYE_OPEN.split("\n")
        for linha in linhas:
            print(f"{GREEN}{linha}{RESET}")
        restante = max(0, 5 - int(time.time() - start))
        print(f"\n  {VIOLET}Carregando Olho de Deus V2... {WHITE}({restante}s){RESET}")
        time.sleep(0.45)

        # Olho fechado (piscada) — FIX: usa escape ANSI em vez de os.system("cls")
        print("\033[2J\033[H", end="", flush=True)
        linhas = EYE_CLOSED.split("\n")
        for linha in linhas:
            print(f"{GREEN}{linha}{RESET}")
        print(f"\n  {VIOLET}Carregando Olho de Deus V2...{RESET}")
        time.sleep(0.18)


# ──────────────────────────────────────────────
#  HELPERS
# ──────────────────────────────────────────────

def clear():
    # FIX: escape ANSI direto — sem abrir subprocesso, sem piscar no .exe
    print("\033[2J\033[H", end="", flush=True)


def print_banner():
    clear()
    print(TITLE_BOX)
    print(DISCORD_LINE)
    print(SEPARATOR)
    print()


def status(msg, color=CYAN):
    print(f"{color}  ► {WHITE}{msg}{RESET}")


def ok(msg):
    print(f"{GREEN}  ✔ {WHITE}{msg}{RESET}")


def warn(msg):
    print(f"{YELLOW}  ⚠ {msg}{RESET}")


def err(msg):
    print(f"{RED}  ✘ {msg}{RESET}")


# ──────────────────────────────────────────────
#  BUSCA INTELIGENTE NA DB
# ──────────────────────────────────────────────

def baixar_db(num: int, hwid: str) -> list[str] | None:
    """Baixa o conteúdo da DB do servidor autenticado por HWID."""
    try:
        url = f"{BOT_DB_URL}/{num}"
        req = urllib.request.Request(
            url,
            headers={
                "X-HWID": hwid,
                "User-Agent": "OlhoDeus/2.0"
            },
            method="GET"
        )
        with urllib.request.urlopen(req, timeout=30) as resp:
            content = resp.read().decode("utf-8", errors="ignore")
            linhas = [l.strip() for l in content.split("\n") if l.strip()]
            return linhas
    except urllib.error.HTTPError as e:
        if e.code == 403:
            err("Acesso negado. Verifique sua licença.")
        elif e.code == 404:
            err("DB não carregada no servidor. Contate o administrador.")
        else:
            err(f"Erro HTTP {e.code} ao baixar DB.")
        return None
    except Exception as ex:
        err(f"Erro ao conectar ao servidor: {ex}")
        return None


def _extrair_campos(linha: str) -> tuple[str, str, str] | None:
    """
    Extrai (url, login, senha) de uma linha da DB.
    Suporta formatos: url:login:senha  url|login|senha  url;login;senha
    Também suporta login:senha:url e variantes.
    """
    linha = linha.strip()
    if not linha:
        return None

    for sep in [":", "|", ";"]:
        partes = linha.split(sep)
        if len(partes) >= 3:
            for i, p in enumerate(partes):
                p_low = p.lower()
                if (p_low.startswith("http://") or p_low.startswith("https://")
                        or ("." in p and "/" in p and len(p) > 6)):
                    restantes = partes[:i] + partes[i+1:]
                    login = restantes[0] if len(restantes) > 0 else ""
                    senha = sep.join(restantes[1:]) if len(restantes) > 1 else ""
                    return (p.strip(), login.strip(), senha.strip())

            url   = sep.join(partes[:-2]).strip() if len(partes) > 3 else partes[0].strip()
            login = partes[-2].strip()
            senha = partes[-1].strip()
            return (url, login, senha)

        elif len(partes) == 2:
            return (linha, partes[0].strip(), partes[1].strip())

    return (linha, "", "")


def _url_match(url_linha: str, url_busca: str) -> bool:
    """Verifica se a URL da linha corresponde à URL de busca."""
    url_linha_l = url_linha.lower().strip().rstrip("/")
    url_busca_l = url_busca.lower().strip().rstrip("/")

    def sem_proto(u):
        return re.sub(r"^https?://", "", u)

    base_linha  = sem_proto(url_linha_l)
    base_busca  = sem_proto(url_busca_l)

    return (
        base_busca in base_linha
        or base_linha in base_busca
        or base_linha.startswith(base_busca)
        or base_busca.startswith(base_linha)
    )


def buscar_na_db(linhas: list[str], url_busca: str) -> list[dict]:
    """Busca inteligente: encontra todas as entradas que correspondem à URL."""
    resultados = []
    for linha in linhas:
        campos = _extrair_campos(linha)
        if campos is None:
            continue
        url_linha, login, senha = campos
        if _url_match(url_linha, url_busca):
            resultados.append({
                "url":   url_linha,
                "login": login,
                "senha": senha,
                "raw":   linha
            })
    return resultados


def salvar_resultados(resultados: list[dict], url_busca: str, nome_db: str) -> str:
    """Salva os resultados em um arquivo TXT na mesma pasta do programa."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    url_safe  = re.sub(r"[^\w\-_]", "_", url_busca)[:40]
    nome_arq  = f"resultados_{url_safe}_{timestamp}.txt"

    if getattr(sys, "frozen", False):
        pasta = Path(sys.executable).parent
    else:
        pasta = Path(__file__).parent

    caminho = pasta / nome_arq

    with open(caminho, "w", encoding="utf-8") as f:
        f.write("=" * 60 + "\n")
        f.write(f"  OLHO DE DEUS V2 — Resultados da Busca\n")
        f.write("=" * 60 + "\n")
        f.write(f"  DB:          {nome_db}\n")
        f.write(f"  URL Buscada: {url_busca}\n")
        f.write(f"  Total:       {len(resultados)} resultado(s)\n")
        f.write(f"  Data:        {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}\n")
        f.write("=" * 60 + "\n\n")
        for i, r in enumerate(resultados, 1):
            f.write(f"[{i}]\n")
            f.write(f"  URL:   {r['url']}\n")
            f.write(f"  Login: {r['login']}\n")
            f.write(f"  Senha: {r['senha']}\n")
            f.write("-" * 40 + "\n")

    return str(caminho)


# ──────────────────────────────────────────────
#  FLUXO DE BUSCA
# ──────────────────────────────────────────────

DB_NOMES = {
    1: "DB Gov",
    2: "DB Gov / Sites em Geral",
    3: "DB Gov V2",
}


def fluxo_busca(num_db: int, hwid: str):
    """Fluxo completo de busca em uma DB."""
    nome_db = DB_NOMES[num_db]

    print_banner()
    print(f"  {PURPLE}► {WHITE}DB selecionada: {VIOLET}{nome_db}{RESET}")
    print(f"  {GRAY}Baixando base de dados do servidor...{RESET}")

    linhas = baixar_db(num_db, hwid)
    if linhas is None:
        input(f"\n  {GRAY}Pressione ENTER para voltar ao menu...{RESET}")
        return

    ok(f"DB carregada — {len(linhas):,} registros")
    print()

    url_busca = input(f"  {PURPLE}►{WHITE} URL para buscar {GRAY}(ex: site.com.br){RESET}: ").strip()
    if not url_busca:
        warn("URL não informada.")
        input(f"\n  {GRAY}Pressione ENTER para voltar...{RESET}")
        return

    print(f"\n  {CYAN}Buscando '{url_busca}' na {nome_db}...{RESET}")
    todos = buscar_na_db(linhas, url_busca)

    if not todos:
        print()
        err(f"URL '{url_busca}' não encontrada na {nome_db}.")
        print(f"  {GRAY}Tente um domínio mais genérico (ex: site.com em vez de https://sub.site.com/path){RESET}")
        input(f"\n  {GRAY}Pressione ENTER para voltar ao menu...{RESET}")
        return

    print()
    ok(f"Encontrados {WHITE}{BOLD}{len(todos):,}{RESET}{GREEN} resultado(s) para '{url_busca}'")
    print()

    print(f"  {PURPLE}╔══════════════════════════════════════╗")
    print(f"  {PURPLE}║  {WHITE}Quantos resultados deseja salvar?    {PURPLE}║")
    print(f"  {PURPLE}║  {CYAN}[1]{WHITE} Todos ({len(todos):,})                     {PURPLE}║")
    print(f"  {PURPLE}║  {CYAN}[2]{WHITE} Quantidade específica               {PURPLE}║")
    print(f"  {PURPLE}╚══════════════════════════════════════╝{RESET}")
    print()

    escolha_q = input(f"  {PURPLE}►{WHITE} Escolha {GRAY}[1/2]{RESET}: ").strip()

    if escolha_q == "2":
        try:
            qtd_str = input(f"  {PURPLE}►{WHITE} Quantos resultados? {GRAY}(máx {len(todos)}){RESET}: ").strip()
            qtd = int(qtd_str)
            if qtd <= 0:
                err("Quantidade inválida.")
                input(f"\n  {GRAY}Pressione ENTER para voltar...{RESET}")
                return
            qtd = min(qtd, len(todos))
            resultados = todos[:qtd]
        except ValueError:
            err("Valor inválido.")
            input(f"\n  {GRAY}Pressione ENTER para voltar...{RESET}")
            return
    else:
        resultados = todos

    print(f"\n  {CYAN}Gerando arquivo com {len(resultados):,} resultado(s)...{RESET}")

    caminho = salvar_resultados(resultados, url_busca, nome_db)

    print()
    ok(f"Arquivo salvo com sucesso!")
    print(f"  {GRAY}Localização:{RESET}")
    print(f"  {WHITE}{BOLD}  {caminho}{RESET}")
    print()
    input(f"  {GRAY}Pressione ENTER para voltar ao menu principal...{RESET}")


# ──────────────────────────────────────────────
#  MENU PRINCIPAL
# ──────────────────────────────────────────────

def menu_principal(hwid: str):
    while True:
        print_banner()

        print(f"  {PURPLE}╔══════════════════════════════════════════════════════╗")
        print(f"  {PURPLE}║              {WHITE}{BOLD}SELECIONE A BASE DE DADOS{RESET}{PURPLE}             ║")
        print(f"  {PURPLE}╠══════════════════════════════════════════════════════╣")
        print(f"  {PURPLE}║                                                      ║")
        print(f"  {PURPLE}║  {CYAN}[1]{WHITE} DB Gov                                         {PURPLE}║")
        print(f"  {PURPLE}║  {CYAN}[2]{WHITE} DB Gov / Sites em Geral                        {PURPLE}║")
        print(f"  {PURPLE}║  {CYAN}[3]{WHITE} DB Gov V2                                       {PURPLE}║")
        print(f"  {PURPLE}║                                                      ║")
        print(f"  {PURPLE}║  {CYAN}[0]{WHITE} Sair                                           {PURPLE}║")
        print(f"  {PURPLE}║                                                      ║")
        print(f"  {PURPLE}╚══════════════════════════════════════════════════════╝{RESET}")
        print()

        escolha = input(f"  {PURPLE}►{WHITE} Escolha uma opção {GRAY}[0-3]{RESET}: ").strip()

        if escolha == "0":
            clear()
            print(f"\n  {PURPLE}Encerrando Olho de Deus V2...{RESET}\n")
            sys.exit(0)
        elif escolha in ("1", "2", "3"):
            fluxo_busca(int(escolha), hwid)
        else:
            warn("Opção inválida. Tente novamente.")
            time.sleep(1)


# ──────────────────────────────────────────────
#  MAIN
# ──────────────────────────────────────────────

def main():
    # 1. Animação do olho piscando (5 segundos)
    animar_olho()

    # 2. Verificar licença
    hwid = verificar_licenca()

    # 3. Entrar no menu principal
    menu_principal(hwid)


if __name__ == "__main__":
    main()
