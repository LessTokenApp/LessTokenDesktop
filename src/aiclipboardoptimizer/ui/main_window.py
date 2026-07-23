"""Main application window."""
from pathlib import Path
from typing import Optional
import sys

from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QTabWidget, QLabel, QLineEdit, QPushButton, QTextEdit,
    QComboBox, QSpinBox, QCheckBox, QStatusBar, QSystemTrayIcon,
    QMenu, QApplication, QMessageBox, QFileDialog
)
from PySide6.QtCore import Qt, QTimer, Signal, Slot
from PySide6.QtGui import QIcon, QClipboard

from ..application import Application
from ..config import AppConfig
from ..services import ContentType
from ..core.logger import Logger

logger = Logger.get(__name__)


class MainWindow(QMainWindow):
    """Main application window with tabbed interface."""

    # Signals
    clipboard_changed = Signal(str)
    processing_started = Signal()
    processing_completed = Signal(str)

    def __init__(self, app: Application):
        super().__init__()
        self.app = app
        self.setWindowTitle("AI Clipboard Optimizer")
        self.setGeometry(100, 100, 1000, 600)

        # Initialize UI
        self._setup_ui()
        self._setup_hotkeys()
        self._setup_clipboard_monitor()
        self._setup_tray()

        logger.info("Main window initialized")

    def _setup_ui(self) -> None:
        """Setup main UI components."""
        # Central widget
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QVBoxLayout(central)

        # Toolbar
        toolbar = self._create_toolbar()
        main_layout.addLayout(toolbar)

        # Tab widget
        tabs = QTabWidget()
        tabs.addTab(self._create_processor_tab(), "Processor")
        tabs.addTab(self._create_image_tab(), "Images")
        tabs.addTab(self._create_file_tab(), "Files")
        tabs.addTab(self._create_history_tab(), "History")
        tabs.addTab(self._create_settings_tab(), "Settings")

        main_layout.addWidget(tabs)

        # Status bar
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("Ready")

    def _create_toolbar(self) -> QHBoxLayout:
        """Create top toolbar with quick actions."""
        layout = QHBoxLayout()

        # Clipboard preview
        layout.addWidget(QLabel("Clipboard:"))
        self.clipboard_preview = QLineEdit()
        self.clipboard_preview.setReadOnly(True)
        self.clipboard_preview.setMaximumHeight(30)
        self.clipboard_preview.setPlaceholderText("Copy text here...")
        layout.addWidget(self.clipboard_preview)

        # Content type indicator
        self.content_type_label = QLabel("Type: -")
        layout.addWidget(self.content_type_label)

        # Provider selector
        layout.addWidget(QLabel("Provider:"))
        self.provider_combo = QComboBox()
        self._update_provider_list()
        layout.addWidget(self.provider_combo)

        # Process button
        self.process_btn = QPushButton("Process (Ctrl+Shift+P)")
        self.process_btn.clicked.connect(self._on_process_clicked)
        layout.addWidget(self.process_btn)

        # Token counter
        self.token_label = QLabel("Tokens: 0 | Cost: $0.00")
        layout.addWidget(self.token_label)

        return layout

    def _create_processor_tab(self) -> QWidget:
        """Create text processor tab."""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        # Prompt selection
        prompt_layout = QHBoxLayout()
        prompt_layout.addWidget(QLabel("Prompt:"))
        self.prompt_combo = QComboBox()
        self._update_prompt_list()
        prompt_layout.addWidget(self.prompt_combo)
        layout.addLayout(prompt_layout)

        # Input text
        layout.addWidget(QLabel("Input:"))
        self.input_text = QTextEdit()
        self.input_text.setPlaceholderText("Paste text here or click 'From Clipboard'")
        layout.addWidget(self.input_text)

        # Buttons
        btn_layout = QHBoxLayout()
        from_clipboard_btn = QPushButton("From Clipboard")
        from_clipboard_btn.clicked.connect(self._from_clipboard)
        btn_layout.addWidget(from_clipboard_btn)

        process_btn = QPushButton("Process")
        process_btn.clicked.connect(self._on_process_clicked)
        btn_layout.addWidget(process_btn)

        layout.addLayout(btn_layout)

        # Output text
        layout.addWidget(QLabel("Output:"))
        self.output_text = QTextEdit()
        self.output_text.setReadOnly(True)
        layout.addWidget(self.output_text)

        # Copy buttons
        copy_layout = QHBoxLayout()
        copy_btn = QPushButton("Copy to Clipboard")
        copy_btn.clicked.connect(self._copy_to_clipboard)
        copy_layout.addWidget(copy_btn)

        save_btn = QPushButton("Save to File")
        save_btn.clicked.connect(self._save_to_file)
        copy_layout.addWidget(save_btn)

        layout.addLayout(copy_layout)

        return widget

    def _create_image_tab(self) -> QWidget:
        """Create image processing tab."""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        layout.addWidget(QLabel("Image Optimization"))

        # Settings
        settings_layout = QHBoxLayout()

        settings_layout.addWidget(QLabel("Max Width:"))
        self.img_width = QSpinBox()
        self.img_width.setValue(1024)
        self.img_width.setMaximum(4000)
        settings_layout.addWidget(self.img_width)

        settings_layout.addWidget(QLabel("Max Height:"))
        self.img_height = QSpinBox()
        self.img_height.setValue(768)
        self.img_height.setMaximum(4000)
        settings_layout.addWidget(self.img_height)

        settings_layout.addWidget(QLabel("Quality:"))
        self.img_quality = QSpinBox()
        self.img_quality.setValue(60)
        self.img_quality.setMaximum(95)
        settings_layout.addWidget(self.img_quality)

        settings_layout.addStretch()
        layout.addLayout(settings_layout)

        # OCR checkbox
        self.ocr_checkbox = QCheckBox("Extract Text (OCR)")
        self.ocr_checkbox.setChecked(False)
        layout.addWidget(self.ocr_checkbox)

        # File selection
        file_layout = QHBoxLayout()
        self.img_path_label = QLineEdit()
        self.img_path_label.setReadOnly(True)
        self.img_path_label.setPlaceholderText("No image selected")
        file_layout.addWidget(self.img_path_label)

        select_btn = QPushButton("Select Image")
        select_btn.clicked.connect(self._select_image)
        file_layout.addWidget(select_btn)
        layout.addLayout(file_layout)

        # Results
        layout.addWidget(QLabel("Results:"))
        self.img_results = QTextEdit()
        self.img_results.setReadOnly(True)
        layout.addWidget(self.img_results)

        # Process button
        process_btn = QPushButton("Optimize")
        process_btn.clicked.connect(self._optimize_image)
        layout.addWidget(process_btn)

        layout.addStretch()
        return widget

    def _create_file_tab(self) -> QWidget:
        """Create file processing tab."""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        layout.addWidget(QLabel("File Extraction"))

        # File selection
        file_layout = QHBoxLayout()
        self.file_path_label = QLineEdit()
        self.file_path_label.setReadOnly(True)
        self.file_path_label.setPlaceholderText("No file selected")
        file_layout.addWidget(self.file_path_label)

        select_btn = QPushButton("Select File")
        select_btn.clicked.connect(self._select_file)
        file_layout.addWidget(select_btn)
        layout.addLayout(file_layout)

        # Page range for PDF
        pdf_layout = QHBoxLayout()
        pdf_layout.addWidget(QLabel("PDF Pages (e.g., 1-5):"))
        self.pdf_pages = QLineEdit()
        self.pdf_pages.setPlaceholderText("Leave empty for all pages")
        pdf_layout.addWidget(self.pdf_pages)
        layout.addLayout(pdf_layout)

        # Extract button
        extract_btn = QPushButton("Extract")
        extract_btn.clicked.connect(self._extract_file)
        layout.addWidget(extract_btn)

        # Results
        layout.addWidget(QLabel("Extracted Content:"))
        self.file_results = QTextEdit()
        self.file_results.setReadOnly(True)
        layout.addWidget(self.file_results)

        layout.addStretch()
        return widget

    def _create_history_tab(self) -> QWidget:
        """Create history viewer tab."""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        layout.addWidget(QLabel("Processing History"))

        # Search
        search_layout = QHBoxLayout()
        search_layout.addWidget(QLabel("Search:"))
        self.history_search = QLineEdit()
        self.history_search.setPlaceholderText("Search history...")
        search_layout.addWidget(self.history_search)

        search_btn = QPushButton("Search")
        search_btn.clicked.connect(self._search_history)
        search_layout.addWidget(search_btn)

        layout.addLayout(search_layout)

        # History display
        self.history_text = QTextEdit()
        self.history_text.setReadOnly(True)
        layout.addWidget(self.history_text)

        # Stats
        self.stats_label = QLabel()
        layout.addWidget(self.stats_label)

        # Load history
        self._load_history()

        return widget

    def _create_settings_tab(self) -> QWidget:
        """Create settings tab."""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        layout.addWidget(QLabel("Application Settings"))

        # Provider settings
        layout.addWidget(QLabel("Providers:"))
        provider_layout = QVBoxLayout()

        self.provider_settings = {}
        for provider in ["openai", "claude", "gemini", "ollama"]:
            p_layout = QHBoxLayout()
            p_layout.addWidget(QLabel(f"{provider.capitalize()}:"))

            api_key = QLineEdit()
            api_key.setEchoMode(QLineEdit.Password)
            api_key.setPlaceholderText("API Key (leave empty if not available)")
            p_layout.addWidget(api_key)

            self.provider_settings[provider] = api_key
            provider_layout.addLayout(p_layout)

        layout.addLayout(provider_layout)

        # Selection criterion
        layout.addWidget(QLabel("Provider Selection:"))
        self.selection_combo = QComboBox()
        self.selection_combo.addItems(["Auto (Balanced)", "Cheapest", "Fastest", "Quality"])
        layout.addWidget(self.selection_combo)

        # Log level
        layout.addWidget(QLabel("Log Level:"))
        self.log_level_combo = QComboBox()
        self.log_level_combo.addItems(["DEBUG", "INFO", "WARNING", "ERROR"])
        self.log_level_combo.setCurrentText("INFO")
        layout.addWidget(self.log_level_combo)

        # Save button
        save_btn = QPushButton("Save Settings")
        save_btn.clicked.connect(self._save_settings)
        layout.addWidget(save_btn)

        layout.addStretch()
        return widget

    def _setup_hotkeys(self) -> None:
        """Setup global hotkeys."""
        # Ctrl+Shift+P for quick processing
        from pynput import keyboard

        def on_press(key):
            try:
                if hasattr(key, 'vk') and key.vk == 0xAE:  # Windows VK for P
                    # Check if Ctrl+Shift pressed
                    pass
            except:
                pass

        # For now, use timer-based approach
        logger.info("Hotkey support requires additional setup")

    def _setup_clipboard_monitor(self) -> None:
        """Setup clipboard monitoring."""
        self.clipboard_timer = QTimer()
        self.clipboard_timer.timeout.connect(self._check_clipboard)
        self.clipboard_timer.start(1000)  # Check every second

    def _setup_tray(self) -> None:
        """Setup system tray icon."""
        self.tray_icon = QSystemTrayIcon(self)
        self.tray_menu = QMenu()

        show_action = self.tray_menu.addAction("Show")
        show_action.triggered.connect(self.showNormal)

        hide_action = self.tray_menu.addAction("Hide")
        hide_action.triggered.connect(self.hide)

        self.tray_menu.addSeparator()

        exit_action = self.tray_menu.addAction("Exit")
        exit_action.triggered.connect(self._exit_app)

        self.tray_icon.setContextMenu(self.tray_menu)
        self.tray_icon.show()

    # Slots
    @Slot()
    def _check_clipboard(self) -> None:
        """Check clipboard for changes."""
        clipboard = QApplication.clipboard()
        text = clipboard.text()

        if text and len(text) < 200:
            self.clipboard_preview.setText(text[:100])

            # Detect content type
            if self.app:
                detector = self.app.get_content_detector()
                info = detector.detect(text)
                self.content_type_label.setText(f"Type: {info.content_type.value}")

    @Slot()
    def _on_process_clicked(self) -> None:
        """Process text."""
        text = self.input_text.toPlainText()
        if not text.strip():
            QMessageBox.warning(self, "Error", "Please enter text to process")
            return

        prompt_id = self.prompt_combo.currentData()
        if not prompt_id:
            QMessageBox.warning(self, "Error", "Please select a prompt")
            return

        try:
            self.processing_started.emit()
            self.status_bar.showMessage("Processing...")

            result = self.app.process_text(text, prompt_id=prompt_id, auto_copy=False)

            if result:
                self.output_text.setText(result)
                self.status_bar.showMessage("Processing complete")
            else:
                QMessageBox.warning(self, "Error", "Processing failed")

        except Exception as e:
            logger.error(f"Processing error: {e}")
            QMessageBox.critical(self, "Error", str(e))

    @Slot()
    def _from_clipboard(self) -> None:
        """Load from clipboard."""
        clipboard = QApplication.clipboard()
        text = clipboard.text()
        self.input_text.setText(text)

    @Slot()
    def _copy_to_clipboard(self) -> None:
        """Copy output to clipboard."""
        text = self.output_text.toPlainText()
        if text:
            clipboard = QApplication.clipboard()
            clipboard.setText(text)
            self.status_bar.showMessage("Copied to clipboard")

    @Slot()
    def _save_to_file(self) -> None:
        """Save output to file."""
        text = self.output_text.toPlainText()
        if not text:
            QMessageBox.warning(self, "Error", "Nothing to save")
            return

        path, _ = QFileDialog.getSaveFileName(self, "Save Output", "", "Text Files (*.txt)")
        if path:
            try:
                with open(path, 'w', encoding='utf-8') as f:
                    f.write(text)
                self.status_bar.showMessage(f"Saved to {path}")
            except Exception as e:
                QMessageBox.critical(self, "Error", str(e))

    @Slot()
    def _select_image(self) -> None:
        """Select image file."""
        path, _ = QFileDialog.getOpenFileName(self, "Select Image", "", "Images (*.png *.jpg *.jpeg *.webp)")
        if path:
            self.img_path_label.setText(path)

    @Slot()
    def _optimize_image(self) -> None:
        """Optimize selected image."""
        img_path = self.img_path_label.text()
        if not img_path:
            QMessageBox.warning(self, "Error", "Please select an image")
            return

        try:
            result = self.app.optimize_image(
                image_path=Path(img_path),
                max_width=self.img_width.value(),
                max_height=self.img_height.value(),
                quality=self.img_quality.value(),
                extract_text=self.ocr_checkbox.isChecked(),
            )

            output = f"""
Original: {result.original_size_bytes:,} bytes ({result.original_dimensions[0]}x{result.original_dimensions[1]})
Optimized: {result.optimized_size_bytes:,} bytes ({result.optimized_dimensions[0]}x{result.optimized_dimensions[1]})

Size Savings: {result.size_savings:.1f}%
Token Savings: {result.token_savings:.1f}%

Original Tokens: {result.token_estimate_original:,}
Optimized Tokens: {result.token_estimate_optimized:,}
"""

            if result.extracted_text:
                output += f"\nExtracted Text:\n{result.extracted_text[:200]}..."

            self.img_results.setText(output)
            self.status_bar.showMessage("Image optimized successfully")

        except Exception as e:
            logger.error(f"Image optimization error: {e}")
            QMessageBox.critical(self, "Error", str(e))

    @Slot()
    def _select_file(self) -> None:
        """Select file."""
        path, _ = QFileDialog.getOpenFileName(
            self, "Select File", "",
            "All Files (*);;PDF (*.pdf);;Word (*.docx);;CSV (*.csv);;JSON (*.json)"
        )
        if path:
            self.file_path_label.setText(path)

    @Slot()
    def _extract_file(self) -> None:
        """Extract from file."""
        file_path = self.file_path_label.text()
        if not file_path:
            QMessageBox.warning(self, "Error", "Please select a file")
            return

        try:
            pages = None
            if self.pdf_pages.text():
                # Parse page range
                page_str = self.pdf_pages.text()
                if '-' in page_str:
                    start, end = map(int, page_str.split('-'))
                    pages = list(range(start, end + 1))
                else:
                    pages = [int(page_str)]

            result = self.app.extract_file(Path(file_path), pages)

            output = f"""
File: {result.file_path.name}
Type: {result.file_type}
Total Chars: {result.total_chars:,}
Total Words: {result.total_words:,}
Estimated Tokens: {result.token_estimate:,}

Content Preview:
{result.text_summary}
"""

            self.file_results.setText(output)
            self.status_bar.showMessage("File extracted successfully")

        except Exception as e:
            logger.error(f"File extraction error: {e}")
            QMessageBox.critical(self, "Error", str(e))

    @Slot()
    def _search_history(self) -> None:
        """Search history."""
        query = self.history_search.text()
        if not query:
            self._load_history()
            return

        try:
            history_service = self.app.get_history_service()
            results = history_service.search(query, limit=20)

            output = f"Found {len(results)} results:\n\n"
            for entry in results:
                output += f"[{entry.timestamp.strftime('%Y-%m-%d %H:%M')}] {entry.prompt_name}\n"
                output += f"Input: {entry.original_content[:50]}...\n"
                output += f"Output: {entry.processed_content[:50]}...\n"
                output += f"Cost: ${entry.cost_usd:.6f}\n\n"

            self.history_text.setText(output)

        except Exception as e:
            logger.error(f"Search error: {e}")
            QMessageBox.critical(self, "Error", str(e))

    @Slot()
    def _load_history(self) -> None:
        """Load history."""
        try:
            history_service = self.app.get_history_service()
            stats = history_service.get_statistics()

            entries = history_service.get_recent(limit=20)

            output = f"""
History Statistics:
- Total Entries: {stats['total_entries']}
- Total Cost: ${stats['total_cost_usd']:.2f}
- Total Tokens: {stats['total_tokens']:,}

Recent Entries:
"""

            for entry in entries:
                output += f"\n[{entry.timestamp.strftime('%Y-%m-%d %H:%M')}] {entry.prompt_name}\n"
                output += f"Input: {entry.original_content[:50]}...\n"
                output += f"Provider: {entry.provider}/{entry.model}\n"
                output += f"Cost: ${entry.cost_usd:.6f}\n"

            self.history_text.setText(output)
            self.stats_label.setText(
                f"Total: {stats['total_entries']} entries | "
                f"Cost: ${stats['total_cost_usd']:.2f} | "
                f"Tokens: {stats['total_tokens']:,}"
            )

        except Exception as e:
            logger.error(f"History load error: {e}")

    @Slot()
    def _save_settings(self) -> None:
        """Save settings."""
        try:
            # Save provider API keys
            for provider, widget in self.provider_settings.items():
                api_key = widget.text()
                if api_key:
                    self.app.register_provider(provider, api_key)

            QMessageBox.information(self, "Success", "Settings saved")
            self.status_bar.showMessage("Settings saved")

        except Exception as e:
            logger.error(f"Settings save error: {e}")
            QMessageBox.critical(self, "Error", str(e))

    @Slot()
    def _exit_app(self) -> None:
        """Exit application."""
        self.app.shutdown()
        QApplication.quit()

    def _update_provider_list(self) -> None:
        """Update provider combo box."""
        manager = self.app.get_provider_manager()
        providers = manager.get_available_providers()
        self.provider_combo.clear()
        for provider in providers:
            self.provider_combo.addItem(provider, provider)

    def _update_prompt_list(self) -> None:
        """Update prompt combo box."""
        prompt_service = self.app.get_prompt_service()
        prompts = prompt_service.get_all_prompts()
        self.prompt_combo.clear()
        for prompt in prompts:
            self.prompt_combo.addItem(prompt.name, prompt.id)

    def closeEvent(self, event) -> None:
        """Handle close event."""
        # Hide to tray instead of close
        self.hide()
        event.ignore()
