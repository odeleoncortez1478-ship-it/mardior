#!/usr/bin/env python3
"""
MARDIOR — Automatización Gmail + ReadyCloud
============================================

Usage:
    mardior                         # Arranca worker + dashboard
    mardior --worker-only           # Solo worker (sin web)
    mardior --web-only              # Solo dashboard web
    mardior --seed                  # Insertar datos de demo
    mardior --setup-gmail           # Autenticar Gmail OAuth
    mardior --hash-password <pw>    # Generar hash bcrypt para dashboard

También:
    python -m mardior               # Equivalente a mardior
    python main.py                  # Legacy
"""

from mardior.__main__ import run

if __name__ == "__main__":
    run()
