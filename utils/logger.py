"""
Module de logging pour docx2LaTeX

Fournit un système de logging centralisé pour tracer
toutes les actions de l'utilisateur et les états de l'application.
"""

import logging
import sys
from typing import Optional
from pathlib import Path
from datetime import datetime


class DocxLatexLogger:
    """
    Logger personnalisé pour docx2LaTeX avec sortie console et fichier
    """
    
    def __init__(self, name: str = "docx2latex"):
        """
        Initialise le logger
        
        Args:
            name (str): Nom du logger
        """
        self.logger = logging.getLogger(name)
        self.logger.setLevel(logging.DEBUG)
        
        # Éviter les doublons de handlers
        if not self.logger.handlers:
            self.setup_handlers()
    
    def setup_handlers(self) -> None:
        """Configure les handlers pour console et fichier"""
        
        # Formatter
        formatter = logging.Formatter(
            '%(asctime)s | %(levelname)-8s | %(name)s | %(message)s',
            datefmt='%H:%M:%S'
        )
        
        # Handler console
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.INFO)
        console_handler.setFormatter(formatter)
        self.logger.addHandler(console_handler)
        
        # Handler fichier (optionnel)
        try:
            log_file = Path("logs") / f"docx2latex_{datetime.now().strftime('%Y%m%d')}.log"
            log_file.parent.mkdir(exist_ok=True)
            
            file_handler = logging.FileHandler(log_file, encoding='utf-8')
            file_handler.setLevel(logging.DEBUG)
            file_handler.setFormatter(formatter)
            self.logger.addHandler(file_handler)
        except Exception:
            # Si on ne peut pas créer le fichier de log, on continue sans
            pass
    
    def info(self, message: str) -> None:
        """Log un message d'information"""
        self.logger.info(message)
    
    def debug(self, message: str) -> None:
        """Log un message de debug"""
        self.logger.debug(message)
    
    def warning(self, message: str) -> None:
        """Log un avertissement"""
        self.logger.warning(message)
    
    def error(self, message: str) -> None:
        """Log une erreur"""
        self.logger.error(message)
    
    def ui_action(self, action: str, details: str = "") -> None:
        """
        Log une action utilisateur dans l'interface
        
        Args:
            action (str): Type d'action
            details (str): Détails de l'action
        """
        message = f"UI_ACTION: {action}"
        if details:
            message += f" - {details}"
        self.info(message)
    
    def file_operation(self, operation: str, file_path: str, success: bool = True) -> None:
        """
        Log une opération sur fichier
        
        Args:
            operation (str): Type d'opération
            file_path (str): Chemin du fichier
            success (bool): Succès de l'opération
        """
        status = "SUCCESS" if success else "FAILED"
        file_name = Path(file_path).name if file_path else "None"
        self.info(f"FILE_OP: {operation} | {file_name} | {status}")
    
    def validation(self, item: str, valid: bool, reason: str = "") -> None:
        """
        Log une validation
        
        Args:
            item (str): Élément validé
            valid (bool): Résultat de la validation
            reason (str): Raison si invalide
        """
        status = "VALID" if valid else "INVALID"
        message = f"VALIDATION: {item} | {status}"
        if not valid and reason:
            message += f" | {reason}"
        self.info(message)
    
    def state_change(self, component: str, old_state: str, new_state: str) -> None:
        """
        Log un changement d'état
        
        Args:
            component (str): Composant concerné
            old_state (str): Ancien état
            new_state (str): Nouvel état
        """
        self.info(f"STATE_CHANGE: {component} | {old_state} → {new_state}")


# Instance globale du logger
logger = DocxLatexLogger()
