"""
Widgets personnalisés pour l'interface docx2LaTeX

Ce module contient les composants d'interface réutilisables,
notamment les zones de drag & drop pour les fichiers.
"""

from typing import Optional, List, Callable
from pathlib import Path
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
    QLineEdit, QFileDialog, QFrame, QMessageBox
)
from PyQt6.QtCore import Qt, pyqtSignal, QMimeData
from PyQt6.QtGui import QDragEnterEvent, QDropEvent, QPalette, QFont

# Import du logger
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))
from utils.logger import logger


class FileDropZone(QFrame):
    """
    Zone de drag & drop pour fichiers avec bouton de navigation
    
    Signaux:
        file_selected(str): Émis quand un fichier valide est sélectionné
    """
    
    file_selected = pyqtSignal(str)
    
    def __init__(self, 
                 title: str, 
                 file_filter: str = "Tous les fichiers (*.*)",
                 extensions: Optional[List[str]] = None,
                 parent: Optional[QWidget] = None):
        """
        Initialise la zone de drop
        
        Args:
            title (str): Titre affiché dans la zone
            file_filter (str): Filtre pour le dialog de fichier
            extensions (List[str], optional): Extensions acceptées
            parent (QWidget, optional): Widget parent
        """
        super().__init__(parent)
        self.title = title
        self.file_filter = file_filter
        self.extensions = extensions or []
        self.current_file = ""
        
        # Log de l'initialisation
        logger.info(f"Creating FileDropZone: {title}")
        logger.debug(f"Extensions allowed: {self.extensions}")
        
        self.setup_ui()
        self.setup_drag_drop()
        
    def setup_ui(self) -> None:
        """Configure l'interface de la zone de drop"""
        self.setFrameStyle(QFrame.Shape.Box)
        self.setLineWidth(2)
        self.setMinimumHeight(100)
        self.setMaximumHeight(120)
        
        # Layout principal
        layout = QVBoxLayout(self)
        layout.setSpacing(10)
        
        # Titre
        title_label = QLabel(self.title)
        title_font = QFont()
        title_font.setBold(True)
        title_font.setPointSize(10)
        title_label.setFont(title_font)
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title_label)
        
        # Zone d'affichage du fichier
        self.file_display = QLabel("Drop a file here or click Browse")
        self.file_display.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.file_display.setWordWrap(True)
        self.file_display.setStyleSheet("""
            QLabel {
                color: #666;
                font-style: italic;
                padding: 10px;
                border: 1px dashed #ccc;
                border-radius: 5px;
                background-color: #f9f9f9;
            }
        """)
        layout.addWidget(self.file_display)
        
        # Bouton parcourir
        browse_layout = QHBoxLayout()
        browse_layout.addStretch()
        
        self.browse_button = QPushButton("📁 Browse...")
        self.browse_button.clicked.connect(self.browse_file)
        browse_layout.addWidget(self.browse_button)
        
        self.clear_button = QPushButton("❌ Clear")
        self.clear_button.clicked.connect(self.clear_file)
        self.clear_button.setVisible(False)
        browse_layout.addWidget(self.clear_button)
        
        browse_layout.addStretch()
        layout.addLayout(browse_layout)
        
    def setup_drag_drop(self) -> None:
        """Configure le drag & drop"""
        self.setAcceptDrops(True)
        
    def dragEnterEvent(self, event: QDragEnterEvent) -> None:
        """Gère l'entrée du drag"""
        logger.ui_action("DRAG_ENTER", f"Zone: {self.title}")
        
        if event.mimeData().hasUrls():
            # Vérifier si c'est un fichier valide
            urls = event.mimeData().urls()
            if len(urls) == 1 and urls[0].isLocalFile():
                file_path = urls[0].toLocalFile()
                logger.debug(f"Dragged file: {file_path}")
                
                if self.is_valid_file(file_path):
                    event.acceptProposedAction()
                    self.setStyleSheet("QFrame { border: 2px solid #4CAF50; background-color: #E8F5E8; }")
                    logger.ui_action("DRAG_ACCEPTED", f"File: {Path(file_path).name}")
                    return
                else:
                    logger.ui_action("DRAG_REJECTED", f"Invalid file: {Path(file_path).name}")
        
        event.ignore()
        
    def dragLeaveEvent(self, event) -> None:
        """Gère la sortie du drag"""
        logger.ui_action("DRAG_LEAVE", f"Zone: {self.title}")
        self.setStyleSheet("")
        
    def dropEvent(self, event: QDropEvent) -> None:
        """Gère le drop du fichier"""
        logger.ui_action("DROP_EVENT", f"Zone: {self.title}")
        self.setStyleSheet("")
        
        urls = event.mimeData().urls()
        if urls and urls[0].isLocalFile():
            file_path = urls[0].toLocalFile()
            logger.file_operation("DROP", file_path)
            
            if self.is_valid_file(file_path):
                self.set_file(file_path)
                event.acceptProposedAction()
                logger.ui_action("DROP_SUCCESS", f"File accepted: {Path(file_path).name}")
            else:
                logger.ui_action("DROP_FAILED", f"Invalid file: {Path(file_path).name}")
                self.show_invalid_file_message(file_path)
                
    def is_valid_file(self, file_path: str) -> bool:
        """
        Vérifie si le fichier/dossier est valide
        
        Args:
            file_path (str): Chemin du fichier ou dossier
            
        Returns:
            bool: True si le fichier/dossier est valide
        """
        path = Path(file_path)
        logger.debug(f"Validating: {file_path}")
        
        # Pour les dossiers (templates)
        if "Folder" in self.title or "Template" in self.title:
            if not path.is_dir():
                logger.validation(f"Template folder", False, "Not a directory")
                return False
            # Vérifier la présence d'un fichier template.tex
            template_file = path / "template.tex"
            is_valid = template_file.is_file()
            logger.validation(f"Template folder ({path.name})", is_valid, 
                            "template.tex not found" if not is_valid else "")
            return is_valid
        
        # Pour les fichiers normaux
        if not path.is_file():
            logger.validation(f"File ({path.name})", False, "Not a file")
            return False
            
        if not self.extensions:
            logger.validation(f"File ({path.name})", True, "No extension filter")
            return True
            
        file_ext = path.suffix.lower()
        is_valid = file_ext in [ext.lower() for ext in self.extensions]
        logger.validation(f"File ({path.name})", is_valid, 
                        f"Extension {file_ext} not in {self.extensions}" if not is_valid else "")
        return is_valid
        
    def browse_file(self) -> None:
        """Ouvre le dialog de sélection de fichier ou dossier"""
        logger.ui_action("BROWSE_CLICKED", f"Zone: {self.title}")
        
        if "Folder" in self.title or "Template" in self.title:
            # Sélection de dossier pour les templates
            logger.debug("Opening folder dialog")
            folder_path = QFileDialog.getExistingDirectory(
                self,
                f"Select {self.title.lower()}",
                ""
            )
            if folder_path:
                logger.file_operation("BROWSE_FOLDER_SELECTED", folder_path)
                self.set_file(folder_path)
            else:
                logger.ui_action("BROWSE_CANCELLED", "Folder selection")
        else:
            # Sélection de fichier normal
            logger.debug(f"Opening file dialog with filter: {self.file_filter}")
            file_path, _ = QFileDialog.getOpenFileName(
                self,
                f"Select {self.title.lower()}",
                "",
                self.file_filter
            )
            if file_path:
                logger.file_operation("BROWSE_FILE_SELECTED", file_path)
                self.set_file(file_path)
            else:
                logger.ui_action("BROWSE_CANCELLED", "File selection")
            
    def set_file(self, file_path: str) -> None:
        """
        Définit le fichier sélectionné
        
        Args:
            file_path (str): Chemin du fichier
        """
        logger.file_operation("SET_FILE", file_path)
        self.current_file = file_path
        file_name = Path(file_path).name
        
        # Mettre à jour l'affichage
        self.file_display.setText(f"✅ {file_name}")
        self.file_display.setStyleSheet("""
            QLabel {
                color: #2E7D32;
                font-weight: bold;
                padding: 10px;
                border: 1px solid #4CAF50;
                border-radius: 5px;
                background-color: #E8F5E8;
            }
        """)
        
        # Afficher le bouton effacer
        self.clear_button.setVisible(True)
        
        # Émettre le signal
        logger.ui_action("FILE_SELECTED_SIGNAL", f"Zone: {self.title}, File: {file_name}")
        self.file_selected.emit(file_path)
        
    def clear_file(self) -> None:
        """Efface le fichier sélectionné"""
        logger.ui_action("CLEAR_CLICKED", f"Zone: {self.title}")
        old_file = self.current_file
        
        self.current_file = ""
        self.file_display.setText("Drop a file here or click Browse")
        self.file_display.setStyleSheet("""
            QLabel {
                color: #666;
                font-style: italic;
                padding: 10px;
                border: 1px dashed #ccc;
                border-radius: 5px;
                background-color: #f9f9f9;
            }
        """)
        self.clear_button.setVisible(False)
        
        logger.file_operation("CLEAR_FILE", old_file if old_file else "None")
        self.file_selected.emit("")
        
    def get_file_path(self) -> str:
        """
        Retourne le chemin du fichier sélectionné
        
        Returns:
            str: Chemin du fichier ou chaîne vide
        """
        return self.current_file
        
    def show_invalid_file_message(self, file_path: str) -> None:
        """
        Affiche un message d'erreur pour fichier/dossier invalide
        
        Args:
            file_path (str): Chemin du fichier/dossier invalide
        """
        logger.ui_action("SHOW_ERROR_MESSAGE", f"Invalid file: {Path(file_path).name}")
        
        if "Folder" in self.title or "Template" in self.title:
            QMessageBox.warning(
                self,
                "Invalid Folder",
                f"The selected folder does not contain a 'template.tex' file:\n{Path(file_path).name}\n\n"
                f"Please ensure the folder contains a valid template.tex file."
            )
        else:
            ext_msg = ""
            if self.extensions:
                ext_msg = f"\n\nAccepted extensions: {', '.join(self.extensions)}"
                
            QMessageBox.warning(
                self,
                "Invalid File",
                f"The selected file is not valid:\n{Path(file_path).name}{ext_msg}"
            )


class StatusBar(QWidget):
    """
    Barre de statut personnalisée pour afficher l'état du projet
    """
    
    def __init__(self, parent: Optional[QWidget] = None):
        """
        Initialise la barre de statut
        
        Args:
            parent (QWidget, optional): Widget parent
        """
        super().__init__(parent)
        self.setup_ui()
        
    def setup_ui(self) -> None:
        """Configure l'interface de la barre de statut"""
        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 5, 10, 5)
        
        # Statut principal
        self.status_label = QLabel("Ready - Select your files")
        layout.addWidget(self.status_label)
        
        layout.addStretch()
        
        # Indicateurs de fichiers
        self.docx_indicator = QLabel("📄")
        self.docx_indicator.setToolTip("DOCX File")
        layout.addWidget(self.docx_indicator)
        
        self.template_indicator = QLabel("📁")
        self.template_indicator.setToolTip("LaTeX Template")
        layout.addWidget(self.template_indicator)
        
        self.bibtex_indicator = QLabel("📚")
        self.bibtex_indicator.setToolTip("BibTeX File")
        layout.addWidget(self.bibtex_indicator)
        
        self.update_indicators(False, False, False)
        
    def update_status(self, message: str) -> None:
        """
        Met à jour le message de statut
        
        Args:
            message (str): Nouveau message de statut
        """
        self.status_label.setText(message)
        
    def update_indicators(self, docx: bool, template: bool, bibtex: bool) -> None:
        """
        Met à jour les indicateurs de fichiers
        
        Args:
            docx (bool): Fichier DOCX présent
            template (bool): Template présent
            bibtex (bool): Fichier BibTeX présent
        """
        # Styles pour les indicateurs
        style_active = "color: #4CAF50; font-size: 16px;"
        style_inactive = "color: #ccc; font-size: 16px;"
        
        self.docx_indicator.setStyleSheet(style_active if docx else style_inactive)
        self.template_indicator.setStyleSheet(style_active if template else style_inactive)
        self.bibtex_indicator.setStyleSheet(style_active if bibtex else style_inactive)
