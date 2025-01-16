from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, 
                           QLabel, QLineEdit, QGroupBox, QPushButton,
                           QFileDialog)
from PyQt5.QtCore import QSettings
import os
from supa_common import log
from supa_settings import SupaSettings

class SettingsDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.settings = SupaSettings()
        self.setup_ui()
        self.load_settings()
        
    def setup_ui(self):
        """UI 구성"""
        self.setWindowTitle("환경설정")
        self.setMinimumWidth(400)
        
        layout = QVBoxLayout(self)
        
        # OCR 그룹
        ocr_group = QGroupBox("OCR 설정")
        ocr_layout = QVBoxLayout()
        
        # Secret Key 입력
        key_layout = QHBoxLayout()
        key_label = QLabel("Secret Key:")
        self.key_edit = QLineEdit()
        key_layout.addWidget(key_label)
        key_layout.addWidget(self.key_edit)
        
        # API URL 입력
        url_layout = QHBoxLayout()
        url_label = QLabel("API URL:")
        self.url_edit = QLineEdit()
        url_layout.addWidget(url_label)
        url_layout.addWidget(self.url_edit)
        
        ocr_layout.addLayout(key_layout)
        ocr_layout.addLayout(url_layout)
        ocr_group.setLayout(ocr_layout)
        layout.addWidget(ocr_group)
        
        # 편집기 그룹
        editor_group = QGroupBox("외부 편집기 설정")
        editor_layout = QHBoxLayout()
        
        self.editor_path_edit = QLineEdit()
        self.editor_path_edit.setPlaceholderText("편집기 경로를 입력하거나 선택하세요...")
        self.editor_path_edit.setText(self.settings.value("editor_path", ""))  # 초기값 설정
        editor_layout.addWidget(self.editor_path_edit)
        
        select_editor_btn = QPushButton("편집기 선택")
        select_editor_btn.clicked.connect(self.select_editor)
        editor_layout.addWidget(select_editor_btn)
        
        editor_group.setLayout(editor_layout)
        layout.addWidget(editor_group)
        
        # 버튼
        button_layout = QHBoxLayout()
        save_button = QPushButton("저장")
        cancel_button = QPushButton("취소")
        button_layout.addStretch()
        button_layout.addWidget(save_button)
        button_layout.addWidget(cancel_button)
        
        layout.addStretch()
        layout.addLayout(button_layout)
        
        # 시그널 연결
        save_button.clicked.connect(self.save_and_close)
        cancel_button.clicked.connect(self.reject)
        
    def load_settings(self):
        """저장된 설정 불러오기"""
        self.key_edit.setText(self.settings.value("ocr/secret_key", ""))
        self.url_edit.setText(self.settings.value("ocr/api_url", ""))
        self.editor_path_edit.setText(self.settings.value("editor_path", ""))
        
    def save_and_close(self):
        """설정 저장 및 다이얼로그 닫기"""
        self.settings.setValue("ocr/secret_key", self.key_edit.text())
        self.settings.setValue("ocr/api_url", self.url_edit.text())
        self.settings.setValue("editor_path", self.editor_path_edit.text())
        self.accept()
        
    def select_editor(self):
        """외부 편집기 선택"""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "편집기 선택",
            "/Applications" if os.path.exists("/Applications") else "",  # macOS의 경우 Applications 폴더
            "실행 파일 (*);;모든 파일 (*.*)"
        )
        
        if file_path:
            self.editor_path_edit.setText(file_path)

# end of file