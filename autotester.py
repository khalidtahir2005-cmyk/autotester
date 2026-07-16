import sys
import os
import subprocess
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QPushButton, QLabel, QFileDialog, 
                             QTextEdit, QFrame, QProgressBar)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QPropertyAnimation, QEasingCurve, QPoint
from PyQt6.QtGui import QFont, QPalette, QColor, QLinearGradient, QBrush, QPainter, QPen

# 1. Thread pour exécuter pytest en arrière-plan
class TestRunnerThread(QThread):
    finished_signal = pyqtSignal(str, bool)
    progress_signal = pyqtSignal(int)

    def __init__(self, target_path):
        super().__init__()
        self.target_path = target_path

    def run(self):
        try:
            # Simuler une progression pour l'animation
            for i in range(10):
                self.progress_signal.emit((i + 1) * 10)
                self.msleep(100)
            
            if os.path.isdir(self.target_path):
                cwd_dir = self.target_path
                cmd = ["py", "-m", "pytest", "-v"]
            else:
                cwd_dir = os.path.dirname(self.target_path)
                cmd = ["py", "-m", "pytest", "-v", os.path.basename(self.target_path)]

            result = subprocess.run(
                cmd, 
                cwd=cwd_dir, 
                stdout=subprocess.PIPE, 
                stderr=subprocess.PIPE, 
                text=True,
                shell=True
            )
            output = result.stdout if result.stdout else result.stderr
            success = (result.returncode == 0)
            
            self.progress_signal.emit(100)
            self.finished_signal.emit(output, success)
        except Exception as e:
            self.finished_signal.emit(f"Erreur lors de l'exécution du test : {str(e)}", False)


# 2. Classe principale de l'interface graphique (GUI)
class AutoTesterApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("AutoTester Pro v3.0")
        self.setMinimumSize(800, 600)
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint)
        self.target_path = ""
        self.is_dragging = False
        self.drag_position = None
        
        # Appliquer le thème sombre ultra moderne
        self.setup_modern_theme()
        self.setAcceptDrops(True)
        self.init_ui()
        self.setup_animations()

    def setup_modern_theme(self):
        """Configure le thème sombre premium avec dégradés"""
        palette = QPalette()
        palette.setColor(QPalette.ColorRole.Window, QColor("#0a0a0f"))
        palette.setColor(QPalette.ColorRole.WindowText, QColor("#e0e0e0"))
        palette.setColor(QPalette.ColorRole.Base, QColor("#1a1812"))
        palette.setColor(QPalette.ColorRole.AlternateBase, QColor("#1a1a2e"))
        palette.setColor(QPalette.ColorRole.Text, QColor("#e0e0e0"))
        palette.setColor(QPalette.ColorRole.Button, QColor("#1e1e32"))
        palette.setColor(QPalette.ColorRole.ButtonText, QColor("#e0e0e0"))
        palette.setColor(QPalette.ColorRole.Highlight, QColor("#6c5ce7"))
        palette.setColor(QPalette.ColorRole.HighlightedText, QColor("#ffffff"))
        self.setPalette(palette)

        self.setStyleSheet("""
            QMainWindow {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                                          stop:0 #0a0a0f, stop:1 #1a1a2e);
                border: 1px solid #2a2a3e;
                border-radius: 12px;
            }
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                                          stop:0 #2d2d4a, stop:1 #1a1a32);
                color: #e0e0e0;
                border: 1px solid #3a3a5a;
                border-radius: 10px;
                padding: 12px 24px;
                font-size: 13px;
                font-weight: 600;
                letter-spacing: 0.5px;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                                          stop:0 #3d3d6a, stop:1 #2a2a4a);
                border-color: #6c5ce7;
            }
            QPushButton:pressed {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                                          stop:0 #1a1a32, stop:1 #0d0d1a);
            }
            QPushButton:disabled {
                background: #1a1a2e;
                color: #4a4a6a;
                border-color: #2a2a3e;
            }
            QTextEdit {
                background-color: #0d0d14;
                color: #e0e0e0;
                border: 1px solid #2a2a3e;
                border-radius: 10px;
                padding: 12px;
                font-family: 'Consolas', 'Fira Code', 'JetBrains Mono', monospace;
                font-size: 12px;
                line-height: 1.8;
            }
            QLabel {
                color: #c0c0d0;
            }
            QProgressBar {
                background-color: #1a1a2e;
                border: none;
                border-radius: 6px;
                height: 6px;
                text-align: center;
            }
            QProgressBar::chunk {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                                          stop:0 #6c5ce7, stop:1 #00b894);
                border-radius: 6px;
            }
        """)

    def init_ui(self):
        # Widget principal avec marges
        central_widget = QWidget()
        central_widget.setStyleSheet("background: transparent;")
        main_layout = QVBoxLayout()
        main_layout.setSpacing(20)
        main_layout.setContentsMargins(30, 30, 30, 30)

        # Barre de titre personnalisée
        title_bar = QFrame()
        title_bar.setStyleSheet("""
            QFrame {
                background: transparent;
                border: none;
                padding: 5px;
            }
        """)
        title_layout = QHBoxLayout()
        title_layout.setContentsMargins(0, 0, 0, 0)
        
        # Titre avec icône
        title_label = QLabel("⚡ AutoTester Pro")
        title_label.setStyleSheet("""
            color: #ffffff;
            font-size: 18px;
            font-weight: 700;
            letter-spacing: 1px;
            background: transparent;
        """)
        title_layout.addWidget(title_label)
        
        # Boutons de contrôle de la fenêtre
        title_layout.addStretch()
        
        btn_minimize = QPushButton("─")
        btn_minimize.setFixedSize(30, 30)
        btn_minimize.setStyleSheet("""
            QPushButton {
                background: transparent;
                border: none;
                color: #c0c0d0;
                font-size: 16px;
                padding: 0px;
            }
            QPushButton:hover {
                background: #2a2a3e;
                border-radius: 6px;
            }
        """)
        btn_minimize.clicked.connect(self.showMinimized)
        
        btn_close = QPushButton("✕")
        btn_close.setFixedSize(30, 30)
        btn_close.setStyleSheet("""
            QPushButton {
                background: transparent;
                border: none;
                color: #c0c0d0;
                font-size: 16px;
                padding: 0px;
            }
            QPushButton:hover {
                background: #e74c3c;
                color: white;
                border-radius: 6px;
            }
        """)
        btn_close.clicked.connect(self.close)
        
        title_layout.addWidget(btn_minimize)
        title_layout.addWidget(btn_close)
        title_bar.setLayout(title_layout)
        main_layout.addWidget(title_bar)

        # Zone de Drag & Drop ultra stylisée
        self.drop_area = QFrame()
        self.drop_area.setStyleSheet("""
            QFrame {
                border: 2px dashed #3a3a5a;
                border-radius: 16px;
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                                          stop:0 rgba(26,26,46,0.8),
                                          stop:1 rgba(13,13,20,0.8));
                padding: 50px;
            }
        """)
        
        drop_layout = QVBoxLayout()
        drop_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        drop_layout.setSpacing(15)
        
        # Icône avec animation
        self.icon_label = QLabel("📂")
        self.icon_label.setStyleSheet("""
            font-size: 64px;
            background: transparent;
        """)
        self.icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        drop_layout.addWidget(self.icon_label)
        
        self.drop_text = QLabel("Drop your project or test file here")
        self.drop_text.setStyleSheet("""
            color: #e0e0e0;
            font-size: 18px;
            font-weight: 600;
            background: transparent;
            letter-spacing: 0.5px;
        """)
        self.drop_text.setAlignment(Qt.AlignmentFlag.AlignCenter)
        drop_layout.addWidget(self.drop_text)
        
        sub_text = QLabel("Supports Python files and project directories")
        sub_text.setStyleSheet("""
            color: #6a6a8a;
            font-size: 13px;
            background: transparent;
        """)
        sub_text.setAlignment(Qt.AlignmentFlag.AlignCenter)
        drop_layout.addWidget(sub_text)
        
        self.drop_area.setLayout(drop_layout)
        main_layout.addWidget(self.drop_area)

        # Boutons de sélection
        buttons_layout = QHBoxLayout()
        buttons_layout.setSpacing(12)
        
        btn_browse_folder = QPushButton("📁 Browse Folder")
        btn_browse_folder.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                                          stop:0 rgba(45,45,74,0.6),
                                          stop:1 rgba(26,26,50,0.6));
                border: 1px solid rgba(58,58,90,0.4);
                padding: 12px 20px;
            }
        """)
        btn_browse_folder.clicked.connect(self.browse_folder)
        
        btn_browse_file = QPushButton("📄 Browse File")
        btn_browse_file.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                                          stop:0 rgba(45,45,74,0.6),
                                          stop:1 rgba(26,26,50,0.6));
                border: 1px solid rgba(58,58,90,0.4);
                padding: 12px 20px;
            }
        """)
        btn_browse_file.clicked.connect(self.browse_file)
        
        buttons_layout.addWidget(btn_browse_folder)
        buttons_layout.addWidget(btn_browse_file)
        main_layout.addLayout(buttons_layout)

        # Bouton principal d'exécution
        self.btn_run = QPushButton("🚀 Run Tests")
        self.btn_run.setEnabled(False)
        self.btn_run.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                                          stop:0 #6c5ce7, stop:1 #00b894);
                color: white;
                font-size: 16px;
                font-weight: 700;
                padding: 16px;
                border: none;
                border-radius: 12px;
                letter-spacing: 1px;
            }
            QPushButton:hover:enabled {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                                          stop:0 #7c6ce7, stop:1 #10c894);
                transform: scale(1.02);
            }
            QPushButton:pressed:enabled {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                                          stop:0 #5c4cd7, stop:1 #00a884);
            }
            QPushButton:disabled {
                background: #2a2a3e;
                color: #5a5a7a;
            }
        """)
        self.btn_run.clicked.connect(self.run_tests)
        main_layout.addWidget(self.btn_run)

        # Barre de progression
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                background-color: #1a1a2e;
                border: none;
                border-radius: 6px;
                height: 6px;
                text-align: center;
            }
            QProgressBar::chunk {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                                          stop:0 #6c5ce7, stop:1 #00b894);
                border-radius: 6px;
            }
        """)
        main_layout.addWidget(self.progress_bar)

        # Label de statut
        self.status_label = QLabel("● Ready")
        self.status_label.setStyleSheet("""
            color: #6a6a8a;
            font-weight: 500;
            font-size: 13px;
            padding: 10px;
            background: rgba(26,26,46,0.4);
            border-radius: 8px;
            border: 1px solid rgba(42,42,62,0.3);
        """)
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_layout.addWidget(self.status_label)

        # Console de sortie
        console_header = QLabel("📋 Output Console")
        console_header.setStyleSheet("""
            color: #8a8aaa;
            font-weight: 600;
            font-size: 13px;
            letter-spacing: 0.5px;
            margin-top: 5px;
        """)
        main_layout.addWidget(console_header)
        
        self.console_output = QTextEdit()
        self.console_output.setReadOnly(True)
        self.console_output.setStyleSheet("""
            QTextEdit {
                background-color: #0a0a12;
                color: #c0c0d0;
                border: 1px solid #1a1a2e;
                border-radius: 10px;
                padding: 15px;
                font-family: 'Consolas', 'Fira Code', 'JetBrains Mono', monospace;
                font-size: 12px;
                line-height: 1.8;
            }
        """)
        main_layout.addWidget(self.console_output)

        central_widget.setLayout(main_layout)
        self.setCentralWidget(central_widget)

    def setup_animations(self):
        """Configure les animations pour l'interface"""
        # Animation pour l'icône de drop
        self.icon_animation = QPropertyAnimation(self.icon_label, b"geometry")
        self.icon_animation.setDuration(1000)
        self.icon_animation.setLoopCount(-1)
        self.icon_animation.setEasingCurve(QEasingCurve.Type.InOutQuad)
        
        # Animation de rebond pour le bouton principal
        self.btn_animation = QPropertyAnimation(self.btn_run, b"geometry")
        self.btn_animation.setDuration(300)
        self.btn_animation.setEasingCurve(QEasingCurve.Type.OutBack)

    def mousePressEvent(self, event):
        """Permet de déplacer la fenêtre sans bordure"""
        if event.button() == Qt.MouseButton.LeftButton:
            self.is_dragging = True
            self.drag_position = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            event.accept()

    def mouseMoveEvent(self, event):
        if self.is_dragging:
            self.move(event.globalPosition().toPoint() - self.drag_position)
            event.accept()

    def mouseReleaseEvent(self, event):
        self.is_dragging = False

    # Événements Drag & Drop avec animations
    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
            # Animation de l'icône
            self.icon_animation.setStartValue(self.icon_label.geometry())
            self.icon_animation.setEndValue(self.icon_label.geometry().adjusted(0, -10, 0, 10))
            self.icon_animation.start()
            
            self.drop_area.setStyleSheet("""
                QFrame {
                    border: 2px solid #6c5ce7;
                    border-radius: 16px;
                    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                                              stop:0 rgba(108,92,231,0.15),
                                              stop:1 rgba(13,13,20,0.8));
                    padding: 50px;
                }
            """)
            self.drop_text.setStyleSheet("""
                color: #a09bfe;
                font-size: 18px;
                font-weight: 600;
                background: transparent;
                letter-spacing: 0.5px;
            """)
            self.icon_label.setText("📥")

    def dragLeaveEvent(self, event):
        self.icon_animation.stop()
        self.icon_label.setText("📂")
        self.drop_area.setStyleSheet("""
            QFrame {
                border: 2px dashed #3a3a5a;
                border-radius: 16px;
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                                          stop:0 rgba(26,26,46,0.8),
                                          stop:1 rgba(13,13,20,0.8));
                padding: 50px;
            }
        """)
        self.drop_text.setStyleSheet("""
            color: #e0e0e0;
            font-size: 18px;
            font-weight: 600;
            background: transparent;
            letter-spacing: 0.5px;
        """)

    def dropEvent(self, event):
        for url in event.mimeData().urls():
            file_path = url.toLocalFile()
            if os.path.exists(file_path):
                self.target_path = file_path
                self.update_target_display()
                break
        self.dragLeaveEvent(None)

    def browse_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "Select Project Directory")
        if folder:
            self.target_path = folder
            self.update_target_display()

    def browse_file(self):
        file, _ = QFileDialog.getOpenFileName(self, "Select Python Test File", "", "Python Files (*.py)")
        if file:
            self.target_path = file
            self.update_target_display()

    def update_target_display(self):
        name = os.path.basename(self.target_path)
        type_str = "📁 Directory" if os.path.isdir(self.target_path) else "📄 File"
        
        self.drop_text.setText(f"✅ {type_str} : {name}")
        self.drop_area.setStyleSheet("""
            QFrame {
                border: 2px solid #00b894;
                border-radius: 16px;
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                                          stop:0 rgba(0,184,148,0.12),
                                          stop:1 rgba(13,13,20,0.8));
                padding: 50px;
            }
        """)
        self.icon_label.setText("✅")
        self.btn_run.setEnabled(True)
        self.status_label.setText("● Ready to run tests")
        self.status_label.setStyleSheet("""
            color: #00b894;
            font-weight: 500;
            font-size: 13px;
            padding: 10px;
            background: rgba(0,184,148,0.08);
            border-radius: 8px;
            border: 1px solid rgba(0,184,148,0.2);
        """)

    def run_tests(self):
        if not self.target_path:
            return
            
        self.status_label.setText("● Running tests...")
        self.status_label.setStyleSheet("""
            color: #fdcb6e;
            font-weight: 500;
            font-size: 13px;
            padding: 10px;
            background: rgba(253,203,110,0.08);
            border-radius: 8px;
            border: 1px solid rgba(253,203,110,0.2);
        """)
        self.console_output.clear()
        self.btn_run.setEnabled(False)
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)

        self.thread = TestRunnerThread(self.target_path)
        self.thread.finished_signal.connect(self.on_testing_finished)
        self.thread.progress_signal.connect(self.progress_bar.setValue)
        self.thread.start()

    def on_testing_finished(self, output, success):
        self.console_output.setText(output)
        self.btn_run.setEnabled(True)
        self.progress_bar.setVisible(False)
        
        if success:
            self.status_label.setText("✅ All tests passed!")
            self.status_label.setStyleSheet("""
                color: #00b894;
                font-weight: 600;
                font-size: 14px;
                padding: 10px;
                background: rgba(0,184,148,0.12);
                border-radius: 8px;
                border: 1px solid rgba(0,184,148,0.3);
            """)
            self.icon_label.setText("🎉")
        else:
            self.status_label.setText("❌ Some tests failed")
            self.status_label.setStyleSheet("""
                color: #ff7675;
                font-weight: 600;
                font-size: 14px;
                padding: 10px;
                background: rgba(255,118,117,0.12);
                border-radius: 8px;
                border: 1px solid rgba(255,118,117,0.3);
            """)
            self.icon_label.setText("⚠️")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    
    # Définir la police par défaut
    font = QFont("Segoe UI", 9)
    app.setFont(font)
    
    window = AutoTesterApp()
    window.show()
    sys.exit(app.exec())
