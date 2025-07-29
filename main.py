#!/usr/bin/env python3
"""
docx2LaTeX - Point d'entrée principal de l'application

Convertisseur DOCX vers LaTeX pour publications médicales
Utilise PyQt6 pour l'interface graphique

Usage:
    python main.py

Author: harmonips
Version: 1.0.0
"""

import sys
import os
import json
from pathlib import Path
from PyQt6.QtWidgets import QApplication, QMessageBox
from PyQt6.QtCore import Qt

# Ajouter le répertoire racine au path pour les imports
sys.path.insert(0, str(Path(__file__).parent))

from ui.main_window import MainWindow
from utils.logger import logger


def load_config() -> dict:
    """
    Charge la configuration depuis config.json
    
    Returns:
        dict: Configuration de l'application
    """
    config_path = Path(__file__).parent / "config.json"
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        QMessageBox.critical(None, "Error", f"Configuration file not found: {config_path}")
        sys.exit(1)
    except json.JSONDecodeError as e:
        QMessageBox.critical(None, "Error", f"Error in configuration file: {e}")
        sys.exit(1)


def check_dependencies() -> bool:
    """
    Vérifie que Pandoc est installé et accessible
    
    Returns:
        bool: True si toutes les dépendances sont présentes
    """
    import subprocess
    try:
        # Vérifier Pandoc
        result = subprocess.run(['pandoc', '--version'], 
                              capture_output=True, text=True, timeout=5)
        if result.returncode != 0:
            raise subprocess.CalledProcessError(result.returncode, 'pandoc')
        return True
    except (subprocess.CalledProcessError, FileNotFoundError, subprocess.TimeoutExpired):
        QMessageBox.warning(
            None, 
            "Missing Dependency", 
            "Pandoc is not installed or accessible.\n\n"
            "Please install Pandoc from:\n"
            "https://pandoc.org/installing.html\n\n"
            "The application will continue but conversion will not work."
        )
        return False


def main():
    """
    Fonction principale de l'application
    """
    # Créer l'application Qt
    app = QApplication(sys.argv)
    app.setApplicationName("docx2LaTeX")
    app.setApplicationVersion("1.0.0")
    app.setOrganizationName("harmonips")
    
    logger.info("=== APPLICATION STARTUP ===")
    logger.info("Qt Application created")
    
    # Charger la configuration
    config = load_config()
    logger.info("Configuration loaded successfully")
    
    # Vérifier les dépendances
    deps_ok = check_dependencies()
    logger.info(f"Dependencies check: {'OK' if deps_ok else 'FAILED'}")
    
    # Créer et afficher la fenêtre principale
    logger.info("Creating main window...")
    main_window = MainWindow(config)
    main_window.show()
    logger.info("Main window displayed")
    logger.info("=== APPLICATION READY FOR USER INTERACTION ===")
    
    # Démarrer la boucle d'événements
    logger.info("Starting Qt event loop...")
    exit_code = app.exec()
    logger.info(f"Application exited with code: {exit_code}")
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
