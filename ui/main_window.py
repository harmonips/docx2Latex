"""
Fenêtre principale de l'application docx2LaTeX

Interface utilisateur principale avec zones de drag & drop,
gestion des fichiers et navigation entre les étapes.
"""

from typing import Dict, Optional, Any
from pathlib import Path
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
    QLabel, QPushButton, QMessageBox, QProgressBar,
    QSplitter, QTabWidget, QTextEdit, QGroupBox,
    QApplication
)
from PyQt6.QtCore import Qt, pyqtSignal, QTimer
from PyQt6.QtGui import QFont, QIcon, QAction

from .widgets import FileDropZone, StatusBar

# Import du logger
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))
from utils.logger import logger


class MainWindow(QMainWindow):
    def export_all_references_to_bib(self, references_list: list, bibtex_path: str, output_dir: Path):
        """
        Pour chaque référence extraite, cherche l'entrée correspondante dans le .bib source (par DOI puis titre),
        et écrit toutes les entrées trouvées dans references.bib avec la clé = numéro d'apparition (1,2,3,...).
        Ne duplique pas les entrées déjà ajoutées.
        """
        import re
        bib_content = ""
        log_lines = []
        try:
            with open(bibtex_path, "r", encoding="utf-8") as f:
                bib_content = f.read()
            log_lines.append(f"[INFO] BibTeX file loaded: {bibtex_path}")
        except Exception as e:
            self.status_bar.update_status(f"❌ Could not read BibTeX file: {e}")
            log_lines.append(f"[ERROR] Could not read BibTeX file: {e}")
            self._write_export_log(output_dir, log_lines)
            return

        entries = []
        seen_dois = set()
        seen_titles = set()
        # DEBUG: dump all extracted references and BibTeX file size
        debug_lines = [
            f"[DEBUG] BibTeX file: {bibtex_path}",
            f"[DEBUG] BibTeX file size: {len(bib_content)} chars",
            f"[DEBUG] Number of extracted references: {len(references_list)}",
            f"[DEBUG] Extracted references list:",
        ]
        for i, ref in enumerate(references_list, 1):
            debug_lines.append(f"  {i}: {ref}")
        debug_lines.append("[DEBUG] --- Begin export loop ---")
        for idx, ref_text in enumerate(references_list, 1):
            bib_entry = None
            log_lines.append(f"[INFO] Processing reference {idx}: {ref_text}")
            # Match by DOI
            doi_match = re.search(r"doi:([\w./-]+)", ref_text, re.IGNORECASE)
            if doi_match:
                doi = doi_match.group(1)
                log_lines.append(f"[DEBUG] Found DOI in reference {idx}: {doi}")
                if doi in seen_dois:
                    log_lines.append(f"[SKIP] Reference {idx}: DOI {doi} already exported.")
                    continue
                bib_entry_re = re.compile(r'@\w+\{[^@]*doi\s*=\s*[{\"]?%s[}\"]?[^@]*\}' % re.escape(doi), re.IGNORECASE|re.DOTALL)
                bib_entry_match = bib_entry_re.search(bib_content)
                if bib_entry_match:
                    bib_entry = bib_entry_match.group(0)
                    seen_dois.add(doi)
                    log_lines.append(f"[OK] Reference {idx}: Matched by DOI {doi}.")
                else:
                    log_lines.append(f"[FAIL] Reference {idx}: DOI {doi} not found in BibTeX.")
            # Else, match by title
            if not bib_entry:
                title_match = re.search(r"\. ([*\"]?)([A-Za-z0-9 ,:;\-\(\)\&\'\*]+)[*\"]?\. \d{4}", ref_text)
                if title_match:
                    title = title_match.group(2).strip()
                    log_lines.append(f"[DEBUG] Found title in reference {idx}: '{title}'")
                    if title.lower() in seen_titles:
                        log_lines.append(f"[SKIP] Reference {idx}: Title '{title}' already exported.")
                        continue
                    bib_entry_re = re.compile(r'@\w+\{[^@]*title\s*=\s*[{\"]?[^@{\n]*%s[^@{\n]*[}\"]?[^@]*\}' % re.escape(title), re.IGNORECASE|re.DOTALL)
                    bib_entry_match = bib_entry_re.search(bib_content)
                    if bib_entry_match:
                        bib_entry = bib_entry_match.group(0)
                        seen_titles.add(title.lower())
                        log_lines.append(f"[OK] Reference {idx}: Matched by title '{title}'.")
                    else:
                        log_lines.append(f"[FAIL] Reference {idx}: Title '{title}' not found in BibTeX.")
                else:
                    log_lines.append(f"[DEBUG] No title found in reference {idx}.")
            if bib_entry:
                # Replace key with refXXX (e.g. ref001, ref002, ...)
                ref_key = f"ref{idx:03d}"
                log_lines.append(f"[DEBUG] Replacing BibTeX key with {ref_key} for reference {idx}.")
                def repl_key(m):
                    return f"{m.group(1)}{ref_key},"
                bib_entry = re.sub(r"(@\w+\{)[^,]+,", repl_key, bib_entry, count=1)
                entries.append(bib_entry)
                log_lines.append(f"[EXPORT] Reference {idx}: Exported as {ref_key} to references.bib.")
            else:
                self.status_bar.update_status(f"❌ Reference {idx} not found in BibTeX file.")
                log_lines.append(f"[ERROR] Reference {idx}: No match found in BibTeX for:\n{ref_text}\n---")
            debug_lines.append(f"[DEBUG] After ref {idx}: entries={len(entries)}, seen_dois={list(seen_dois)}, seen_titles={list(seen_titles)}")

        debug_lines.append(f"[DEBUG] --- End export loop ---")
        debug_lines.append(f"[DEBUG] Total entries exported: {len(entries)}")
        if not entries:
            self.status_bar.update_status("❌ No references exported to references.bib")
            log_lines.append("[ERROR] No references exported to references.bib")
            self._write_export_log(output_dir, log_lines)
            # Write debug log
            try:
                debug_path = output_dir / "references_debug.log"
                with open(debug_path, "w", encoding="utf-8") as f:
                    f.write("\n".join(debug_lines) + "\n")
                    f.flush()
            except Exception:
                pass
            return
        bib_out = output_dir / "references.bib"
        try:
            with open(bib_out, "w", encoding="utf-8") as f:
                f.write("% LOG: BibTeX export at end of script\n")
                f.write("\n\n".join(entries) + "\n")
                f.flush()
            self.status_bar.update_status(f"✅ {len(entries)} references exported to {bib_out}")
            log_lines.append(f"[SUCCESS] {len(entries)} references exported to {bib_out}")
        except Exception as e:
            self.status_bar.update_status(f"❌ Could not write references.bib: {e}")
            log_lines.append(f"[ERROR] Could not write references.bib: {e}")
        self._write_export_log(output_dir, log_lines)
        # Write debug log
        try:
            debug_path = output_dir / "references_debug.log"
            with open(debug_path, "w", encoding="utf-8") as f:
                f.write("\n".join(debug_lines) + "\n")
                f.flush()
        except Exception:
            pass

    def _write_export_log(self, output_dir: Path, log_lines: list):
        """Écrit un fichier log détaillé de l'export des références."""
        try:
            log_path = output_dir / "references_export.log"
            with open(log_path, "w", encoding="utf-8") as f:
                f.write("\n".join(log_lines) + "\n")
                f.flush()
        except Exception as e:
            # Logging failure is not critical for the main workflow
            pass
    def export_single_reference_to_bib(self, ref_number: int, ref_text: str, bibtex_path: str, output_dir: Path):
        """
        Extrait la référence correspondante du gros .bib et la copie dans references.bib avec la clé = numéro.
        - ref_number: numéro de la référence (ex: 8)
        - ref_text: texte de la référence extraite du markdown
        - bibtex_path: chemin du gros fichier .bib
        - output_dir: dossier où écrire references.bib
        """
        import re
        bib_content = ""
        try:
            with open(bibtex_path, "r", encoding="utf-8") as f:
                bib_content = f.read()
        except Exception as e:
            self.status_bar.update_status(f"❌ Could not read BibTeX file: {e}")
            return

        # Essayer de matcher par DOI
        doi_match = re.search(r"doi:([\w./-]+)", ref_text, re.IGNORECASE)
        bib_entry = None
        if doi_match:
            doi = doi_match.group(1)
            bib_entry_re = re.compile(r"@\w+\{[^@]*doi\s*=\s*[{\"]?%s[}\"]?[^@]*\}" % re.escape(doi), re.IGNORECASE|re.DOTALL)
            bib_entry = bib_entry_re.search(bib_content)

        # Sinon, essayer de matcher par titre (plus risqué)
        if not bib_entry:
            # Extraire le titre entre guillemets ou italique
            title_match = re.search(r"\. ([*\"]?)([A-Za-z0-9 ,:;\-\(\)\&\'\*]+)[*\"]?\. \d{4}", ref_text)
            if title_match:
                title = title_match.group(2).strip()
                # Chercher le titre dans le .bib (simplifié)
                bib_entry_re = re.compile(r"@\w+\{[^@]*title\s*=\s*[{\"]?[^@{\n]*%s[^@{\n]*[}\"]?[^@]*\}" % re.escape(title), re.IGNORECASE|re.DOTALL)
                bib_entry = bib_entry_re.search(bib_content)

        if not bib_entry:
            self.status_bar.update_status(f"❌ Reference {ref_number} not found in BibTeX file.")
            return

        entry = bib_entry.group(0)
        # Remplacer la clé par le numéro
        entry = re.sub(r"(@\w+\{)[^,]+,", r"\1%d," % ref_number, entry, count=1)

        # Écrire dans references.bib
        bib_out = output_dir / "references.bib"
        try:
            with open(bib_out, "w", encoding="utf-8") as f:
                f.write(entry + "\n")
            self.status_bar.update_status(f"✅ Reference {ref_number} exported to {bib_out}")
        except Exception as e:
            self.status_bar.update_status(f"❌ Could not write references.bib: {e}")
    """
    Fenêtre principale de l'application docx2LaTeX
    
    Gère l'interface utilisateur principale et coordonne
    les différentes étapes de conversion.
    """
    
    def __init__(self, config: Dict[str, Any], parent: Optional[QWidget] = None):
        """
        Initialise la fenêtre principale
        
        Args:
            config (Dict[str, Any]): Configuration de l'application
            parent (QWidget, optional): Widget parent
        """
        super().__init__(parent)
        self.config = config
        self.project_data = {
            "docx_file": "",
            "template_folder": "",
            "bibtex_file": "",
            "is_ready": False
        }
        
        # Log de l'initialisation
        logger.info("=== DOCX2LATEX APPLICATION STARTING ===")
        logger.info(f"Version: {config['app']['version']}")
        logger.info(f"Author: {config['app']['author']}")
        
        self.setup_ui()
        self.setup_connections()
        self.apply_config()
        
        logger.info("Main window initialized successfully")
        
    def setup_ui(self) -> None:
        """Configure l'interface utilisateur"""
        # Configuration de la fenêtre
        self.setWindowTitle(f"{self.config['app']['name']} v{self.config['app']['version']}")
        self.setMinimumSize(800, 600)
        
        # Widget central
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Layout principal
        main_layout = QVBoxLayout(central_widget)
        main_layout.setSpacing(20)
        main_layout.setContentsMargins(20, 20, 20, 10)
        
        # En-tête
        self.create_header(main_layout)
        
        # Zone de sélection des fichiers
        self.create_file_selection_area(main_layout)
        
        # Barre de progression
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        main_layout.addWidget(self.progress_bar)
        
        # Zone des onglets (masquée initialement)
        self.create_tabs_area(main_layout)
        self.tabs_widget.setVisible(False)
        
        # Boutons d'action
        self.create_action_buttons(main_layout)
        
        # Barre de statut
        self.status_bar = StatusBar()
        main_layout.addWidget(self.status_bar)
        
        # Menu bar
        self.create_menu_bar()
        
    def create_header(self, layout: QVBoxLayout) -> None:
        """
        Crée la zone d'en-tête
        
        Args:
            layout (QVBoxLayout): Layout parent
        """
        header_group = QGroupBox()
        header_layout = QVBoxLayout(header_group)
        
        # Titre principal
        title_label = QLabel("📄 docx2LaTeX")
        title_font = QFont()
        title_font.setPointSize(18)
        title_font.setBold(True)
        title_label.setFont(title_font)
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_label.setStyleSheet("color: #2E7D32; padding: 10px;")
        header_layout.addWidget(title_label)
        
        # Sous-titre
        subtitle_label = QLabel("DOCX to LaTeX Converter for Medical Publications")
        subtitle_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        subtitle_label.setStyleSheet("color: #666; font-style: italic;")
        header_layout.addWidget(subtitle_label)
        
        layout.addWidget(header_group)
        
    def create_file_selection_area(self, layout: QVBoxLayout) -> None:
        """
        Crée la zone de sélection des fichiers
        
        Args:
            layout (QVBoxLayout): Layout parent
        """
        files_group = QGroupBox("📁 File Selection")
        files_layout = QVBoxLayout(files_group)
        files_layout.setSpacing(15)
        
        # Instructions
        instructions = QLabel(
            "1️⃣ Drop your files in the zones below or use the Browse buttons\n"
            "2️⃣ Once all files are selected, click 'Analyze Files'"
        )
        instructions.setStyleSheet("padding: 10px; background-color: #E3F2FD; border-radius: 5px;")
        files_layout.addWidget(instructions)
        
        # Zones de drop
        drop_zones_layout = QHBoxLayout()
        drop_zones_layout.setSpacing(15)
        
        # Zone DOCX
        self.docx_zone = FileDropZone(
            "📄 Word File",
            "Word Files (*.docx *.doc)",
            [".docx", ".doc"]
        )
        drop_zones_layout.addWidget(self.docx_zone)
        
        # Zone Template
        self.template_zone = FileDropZone(
            "📁 Template Folder",
            "Folders"
        )
        drop_zones_layout.addWidget(self.template_zone)
        
        # Zone BibTeX
        self.bibtex_zone = FileDropZone(
            "📚 BibTeX References",
            "BibTeX Files (*.bib)",
            [".bib"]
        )
        drop_zones_layout.addWidget(self.bibtex_zone)
        
        files_layout.addLayout(drop_zones_layout)
        layout.addWidget(files_group)
        
    def create_tabs_area(self, layout: QVBoxLayout) -> None:
        """
        Crée la zone des onglets pour l'édition
        
        Args:
            layout (QVBoxLayout): Layout parent
        """
        self.tabs_widget = QTabWidget()

        # Onglet Métadonnées (masqué)
        metadata_widget = QWidget()
        metadata_layout = QVBoxLayout(metadata_widget)
        metadata_layout.addWidget(QLabel("Document title, authors, and metadata"))
        self.metadata_editor = QTextEdit()
        self.metadata_editor.setPlaceholderText("Extracted metadata will appear here...")
        metadata_layout.addWidget(self.metadata_editor)
        metadata_index = self.tabs_widget.addTab(metadata_widget, "📝 Metadata")
        self.tabs_widget.setTabVisible(metadata_index, False)

        # Onglet Contenu
        content_widget = QWidget()
        content_layout = QVBoxLayout(content_widget)
        content_layout.addWidget(QLabel("Document content in markdown format"))
        self.content_editor = QTextEdit()
        self.content_editor.setPlaceholderText("Converted content will appear here...")
        content_layout.addWidget(self.content_editor)
        self.tabs_widget.addTab(content_widget, "📖 Content")
        
        # Onglet Références
        references_widget = QWidget()
        references_layout = QVBoxLayout(references_widget)
        references_layout.addWidget(QLabel("References and citations"))
        self.references_editor = QTextEdit()
        self.references_editor.setPlaceholderText("Mapped references will appear here...")
        references_layout.addWidget(self.references_editor)
        self.tabs_widget.addTab(references_widget, "📚 References")
        
        layout.addWidget(self.tabs_widget)
        
    def create_action_buttons(self, layout: QVBoxLayout) -> None:
        """
        Crée les boutons d'action
        
        Args:
            layout (QVBoxLayout): Layout parent
        """
        buttons_layout = QHBoxLayout()
        buttons_layout.addStretch()
        
        # Bouton Analyser
        self.analyze_button = QPushButton("🔍 Analyze Files")
        self.analyze_button.setMinimumHeight(40)
        self.analyze_button.setStyleSheet("""
            QPushButton {
                background-color: #2196F3;
                color: white;
                font-weight: bold;
                border: none;
                border-radius: 5px;
                padding: 10px 20px;
            }
            QPushButton:hover {
                background-color: #1976D2;
            }
            QPushButton:disabled {
                background-color: #ccc;
            }
        """)
        self.analyze_button.setEnabled(False)
        buttons_layout.addWidget(self.analyze_button)
        
        # Bouton Générer LaTeX
        self.generate_button = QPushButton("📄 Generate LaTeX")
        self.generate_button.setMinimumHeight(40)
        self.generate_button.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                font-weight: bold;
                border: none;
                border-radius: 5px;
                padding: 10px 20px;
            }
            QPushButton:hover {
                background-color: #388E3C;
            }
            QPushButton:disabled {
                background-color: #ccc;
            }
        """)
        self.generate_button.setEnabled(False)
        buttons_layout.addWidget(self.generate_button)
        
        # Bouton Compiler PDF
        self.compile_button = QPushButton("🔧 Compile PDF")
        self.compile_button.setMinimumHeight(40)
        self.compile_button.setStyleSheet("""
            QPushButton {
                background-color: #FF9800;
                color: white;
                font-weight: bold;
                border: none;
                border-radius: 5px;
                padding: 10px 20px;
            }
            QPushButton:hover {
                background-color: #F57C00;
            }
            QPushButton:disabled {
                background-color: #ccc;
            }
        """)
        self.compile_button.setEnabled(False)
        buttons_layout.addWidget(self.compile_button)
        
        buttons_layout.addStretch()
        layout.addLayout(buttons_layout)
        
    def create_menu_bar(self) -> None:
        """Crée la barre de menu"""
        menubar = self.menuBar()
        
        # Menu Fichier
        file_menu = menubar.addMenu("&File")
        
        new_action = QAction("&New Project", self)
        new_action.setShortcut("Ctrl+N")
        new_action.triggered.connect(self.new_project)
        file_menu.addAction(new_action)
        
        open_action = QAction("&Open Project...", self)
        open_action.setShortcut("Ctrl+O")
        open_action.triggered.connect(self.open_project)
        file_menu.addAction(open_action)
        
        save_action = QAction("&Save Project", self)
        save_action.setShortcut("Ctrl+S")
        save_action.triggered.connect(self.save_project)
        file_menu.addAction(save_action)
        
        file_menu.addSeparator()
        
        exit_action = QAction("&Exit", self)
        exit_action.setShortcut("Ctrl+Q")
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # Menu Aide
        help_menu = menubar.addMenu("&Help")
        
        about_action = QAction("&About", self)
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)
        
    def setup_connections(self) -> None:
        """Configure les connexions de signaux"""
        # Zones de fichiers
        self.docx_zone.file_selected.connect(self.on_docx_selected)
        self.template_zone.file_selected.connect(self.on_template_selected)
        self.bibtex_zone.file_selected.connect(self.on_bibtex_selected)
        
        # Boutons
        self.analyze_button.clicked.connect(self.analyze_files)
        self.generate_button.clicked.connect(self.generate_latex)
        self.compile_button.clicked.connect(self.compile_pdf)
        
    def apply_config(self) -> None:
        """Applique la configuration à l'interface"""
        ui_config = self.config.get("ui", {})
        
        # Taille de la fenêtre
        if "window_width" in ui_config and "window_height" in ui_config:
            self.resize(ui_config["window_width"], ui_config["window_height"])
            
        # Police
        if "font_family" in ui_config and "font_size" in ui_config:
            font = QFont(ui_config["font_family"], ui_config["font_size"])
            self.setFont(font)
            
    def on_docx_selected(self, file_path: str) -> None:
        """
        Callback pour sélection fichier DOCX
        
        Args:
            file_path (str): Chemin du fichier DOCX
        """
        old_file = self.project_data["docx_file"]
        self.project_data["docx_file"] = file_path
        logger.state_change("DOCX_FILE", 
                          Path(old_file).name if old_file else "None",
                          Path(file_path).name if file_path else "None")
        
        self.update_ui_state()
        if file_path:
            self.status_bar.update_status(f"DOCX file selected: {Path(file_path).name}")
        else:
            self.status_bar.update_status("DOCX file removed")
            
    def on_template_selected(self, file_path: str) -> None:
        """
        Callback pour sélection dossier template
        
        Args:
            file_path (str): Chemin du dossier template
        """
        old_folder = self.project_data["template_folder"]
        self.project_data["template_folder"] = file_path
        logger.state_change("TEMPLATE_FOLDER", 
                          Path(old_folder).name if old_folder else "None",
                          Path(file_path).name if file_path else "None")
        
        self.update_ui_state()
        if file_path:
            self.status_bar.update_status(f"Template selected: {Path(file_path).name}")
        else:
            self.status_bar.update_status("Template removed")
            
    def on_bibtex_selected(self, file_path: str) -> None:
        """
        Callback pour sélection fichier BibTeX
        
        Args:
            file_path (str): Chemin du fichier BibTeX
        """
        old_file = self.project_data["bibtex_file"]
        self.project_data["bibtex_file"] = file_path
        logger.state_change("BIBTEX_FILE", 
                          Path(old_file).name if old_file else "None",
                          Path(file_path).name if file_path else "None")
        
        self.update_ui_state()
        if file_path:
            self.status_bar.update_status(f"BibTeX selected: {Path(file_path).name}")
        else:
            self.status_bar.update_status("BibTeX removed")
            
    def update_ui_state(self) -> None:
        """Met à jour l'état de l'interface selon les fichiers sélectionnés"""
        docx_ok = bool(self.project_data["docx_file"])
        template_ok = bool(self.project_data["template_folder"])
        bibtex_ok = bool(self.project_data["bibtex_file"])
        
        logger.state_change("UI_STATE", 
                          f"Files: {sum([docx_ok, template_ok, bibtex_ok])}/3",
                          f"DOCX:{docx_ok}, Template:{template_ok}, BibTeX:{bibtex_ok}")
        
        # Mettre à jour les indicateurs
        self.status_bar.update_indicators(docx_ok, template_ok, bibtex_ok)
        
        # Activer le bouton d'analyse si tous les fichiers sont présents
        all_files_ready = docx_ok and template_ok and bibtex_ok
        old_ready_state = self.project_data["is_ready"]
        self.project_data["is_ready"] = all_files_ready
        self.analyze_button.setEnabled(all_files_ready)
        
        if old_ready_state != all_files_ready:
            logger.state_change("ANALYZE_BUTTON", 
                              "disabled" if not old_ready_state else "enabled",
                              "enabled" if all_files_ready else "disabled")
        
        if all_files_ready:
            self.status_bar.update_status("✅ All files ready - Click 'Analyze'")
            logger.info(">>> ALL FILES READY - USER CAN CLICK ANALYZE <<<")
        elif not any([docx_ok, template_ok, bibtex_ok]):
            self.status_bar.update_status("Select your files to get started")
            
    def analyze_files(self) -> None:
        """Lance l'analyse des fichiers sélectionnés"""
        logger.ui_action("ANALYZE_BUTTON_CLICKED", "Starting file analysis")
        logger.info("=== ANALYSIS PHASE STARTING ===")
        logger.info(f"DOCX: {self.project_data['docx_file']}")
        logger.info(f"Template: {self.project_data['template_folder']}")
        logger.info(f"BibTeX: {self.project_data['bibtex_file']}")

        # Vérifier que tous les fichiers nécessaires sont sélectionnés
        docx = self.project_data["docx_file"]
        template = self.project_data["template_folder"]
        bibtex = self.project_data["bibtex_file"]
        if not (docx and template and bibtex):
            self.status_bar.update_status("❌ Please select all required files (DOCX, template, BibTeX)")
            QMessageBox.warning(self, "Missing files", "Please select a DOCX file, a template folder, and a BibTeX file.")
            return

        # Créer le dossier de sortie sous la forme output/nomdufichierdocx
        docx_name = Path(docx).stem
        output_dir = Path.cwd() / "output" / docx_name
        output_dir.mkdir(parents=True, exist_ok=True)
        self.status_bar.update_status(f"📁 Output directory created: {output_dir}")

        # Étape Pandoc : conversion DOCX → Markdown
        import subprocess
        md_path = output_dir / "content.md"
        try:
            result = subprocess.run([
                "pandoc", str(docx), "-o", str(md_path), "--wrap=none"
            ], capture_output=True, text=True, check=True)
        except Exception as e:
            self.status_bar.update_status("❌ Pandoc conversion failed")
            QMessageBox.critical(self, "Pandoc Error", f"Pandoc failed to convert DOCX to Markdown.\n{e}")
            return

        # Charger le Markdown et extraire les références
        if md_path.exists():
            self.status_bar.update_status(f"✅ DOCX converted to Markdown: {md_path}")
            try:
                with open(md_path, "r", encoding="utf-8") as f:
                    md_content = f.read()
                self.content_editor.setPlainText(md_content)

                # Extraction des références individuelles
                references_block = self.extract_references_from_markdown(md_content)
                references_list = self.split_references(references_block)
                if references_list:
                    self.references_editor.setPlainText("\n".join(ref.strip() for ref in references_list))
                    # Générer references.bib automatiquement
                    self.export_all_references_to_bib(
                        references_list,
                        self.project_data["bibtex_file"],
                        output_dir
                    )
                else:
                    self.references_editor.setPlainText("No references section found.")
            except Exception as e:
                self.status_bar.update_status("❌ Failed to load Markdown content")
                # Log détaillé dans le dossier de sortie
                try:
                    log_path = output_dir / "markdown_read_error.log"
                    with open(log_path, "w", encoding="utf-8") as logf:
                        logf.write(f"[ERROR] Could not read Markdown file: {md_path}\nException: {e}\n")
                except Exception:
                    pass
                QMessageBox.critical(self, "Read Error", f"Could not read the generated Markdown file.\n{e}")
                return
        else:
            self.status_bar.update_status("❌ Pandoc did not produce Markdown output")
            QMessageBox.critical(self, "Pandoc Error", "Pandoc did not produce the expected Markdown file.")
            return

        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        logger.info("Starting analysis simulation...")

        # Simuler l'analyse (à remplacer par la vraie logique)
        QTimer.singleShot(1000, self.on_analysis_complete)

    def extract_references_from_markdown(self, md_content: str) -> str:
        """
        Extrait la section Références/Bibliographie du Markdown.
        Cherche un titre de section (## References ou ## Bibliography) et extrait jusqu'à la fin ou la prochaine section.
        """
        import re
        pattern = re.compile(r"^## +(?:References|Bibliography)\s*$", re.MULTILINE | re.IGNORECASE)
        match = pattern.search(md_content)
        if not match:
            return ""
        start = match.end()
        next_section = re.search(r"^## +.+$", md_content[start:], re.MULTILINE)
        if next_section:
            end = start + next_section.start()
        else:
            end = len(md_content)
        references_block = md_content[start:end].strip()
        return references_block

    def split_references(self, references_block: str) -> list:
        """
        Découpe le bloc de références en une liste de références individuelles, dans l'ordre d'apparition.
        Gère les formats courants :
        - Numérotation 1. 2. 3.
        - Numérotation [1] [2] [3]
        - Numérotation 1) 2) 3)
        Fonctionne même si toutes les références sont sur une seule ligne ou séparées par des retours à la ligne.
        """
        import re
        if not references_block.strip():
            return []
        # On découpe sur chaque numéro suivi d'un séparateur, y compris '1\.' (chiffre + backslash + point)
        # On capture le séparateur pour le remettre devant chaque référence
        pattern = r'(?:^|\n)\s*(\d+\\\.|\d+\.|\[\d+\]|\d+\))\s+'
        block = references_block
        if not re.match(pattern, block):
            block = '\n' + block
        parts = re.split(pattern, block)
        refs = []
        i = 1
        while i < len(parts):
            sep = parts[i]
            ref = parts[i+1] if (i+1) < len(parts) else ''
            refs.append(f'{sep} {ref}'.strip())
            i += 2
        refs = [r for r in refs if r.strip()]
        return refs
        
    def on_analysis_complete(self) -> None:
        """Callback appelé quand l'analyse est terminée"""
        logger.info("=== ANALYSIS PHASE COMPLETED ===")
        self.progress_bar.setValue(100)
        self.progress_bar.setVisible(False)
        
        # Afficher les onglets d'édition
        self.tabs_widget.setVisible(True)
        logger.state_change("TABS_WIDGET", "hidden", "visible")
        
        # Activer les boutons suivants
        self.generate_button.setEnabled(True)
        logger.state_change("GENERATE_BUTTON", "disabled", "enabled")
        
        self.status_bar.update_status("✅ Analysis complete - You can edit the content")
        logger.info(">>> ANALYSIS COMPLETE - USER CAN EDIT CONTENT <<<")
        
        # TODO: Remplir les éditeurs avec le contenu analysé
        
    def generate_latex(self) -> None:
        """Génère le fichier LaTeX"""
        logger.ui_action("GENERATE_BUTTON_CLICKED", "Starting LaTeX generation")
        self.status_bar.update_status("📄 Generating LaTeX...")
        # TODO: Implémenter la génération LaTeX
        
    def compile_pdf(self) -> None:
        """Compile le PDF"""
        logger.ui_action("COMPILE_BUTTON_CLICKED", "Starting PDF compilation")
        self.status_bar.update_status("🔧 Compiling PDF...")
        # TODO: Implémenter la compilation PDF
        
    def new_project(self) -> None:
        """Crée un nouveau projet"""
        # TODO: Implémenter la création de nouveau projet
        pass
        
    def open_project(self) -> None:
        """Ouvre un projet existant"""
        # TODO: Implémenter l'ouverture de projet
        pass
        
    def save_project(self) -> None:
        """Sauvegarde le projet actuel"""
        # TODO: Implémenter la sauvegarde de projet
        pass
        
    def show_about(self) -> None:
        """Affiche la boîte de dialogue À propos"""
        QMessageBox.about(
            self,
            "About docx2LaTeX",
            f"""
            <h3>{self.config['app']['name']} v{self.config['app']['version']}</h3>
            <p>DOCX to LaTeX Converter for Medical Publications</p>
            <p>Developed by {self.config['app']['author']}</p>
            <p>© 2025 - All rights reserved</p>
            """
        )
