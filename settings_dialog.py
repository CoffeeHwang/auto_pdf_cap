from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, 
                           QLabel, QLineEdit, QGroupBox, QPushButton)
from PyQt5.QtCore import QSettings

class SettingsDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.settings = QSettings('Coffee.Hwang', 'AutoPdfCap')
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
        
        # 버튼
        button_layout = QHBoxLayout()
        save_button = QPushButton("저장")
        cancel_button = QPushButton("취소")
        button_layout.addStretch()
        button_layout.addWidget(save_button)
        button_layout.addWidget(cancel_button)
        
        # 시그널 연결
        save_button.clicked.connect(self.save_and_close)
        cancel_button.clicked.connect(self.reject)
        
        # 레이아웃 구성
        layout.addWidget(ocr_group)
        layout.addStretch()
        layout.addLayout(button_layout)
        
    def load_settings(self):
        """저장된 설정 불러오기"""
        self.key_edit.setText(self.settings.value('ocr/secret_key', ''))
        self.url_edit.setText(self.settings.value('ocr/api_url', ''))
        
    def save_and_close(self):
        """설정 저장 및 창 닫기"""
        # 설정 저장
        self.settings.setValue('ocr/secret_key', self.key_edit.text())
        self.settings.setValue('ocr/api_url', self.url_edit.text())
        self.settings.sync()  # 설정을 디스크에 즉시 저장
        
        self.accept()  # 다이얼로그 닫기
