from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, 
                           QPushButton, QLabel, QTextEdit, QGroupBox)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont, QFontDatabase
import os
from custom_text_edit import CustomTextEdit

class SummaryTab(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent
        self.initUI()
        
    def initUI(self):
        layout = QVBoxLayout()
        
        # 개요 입력 그룹
        input_group = QGroupBox("개요 입력")
        input_layout = QVBoxLayout()
        
        # OCR 결과를 표시할 CustomTextEdit 추가
        self.summary_text = CustomTextEdit()
        self.summary_text.setPlaceholderText("여기에 개요를 입력하세요...")
        
        # D2Coding 폰트 로드 및 설정
        font_path = os.path.join(os.path.dirname(__file__), 'fonts', 'D2Coding.ttf')
        font_id = QFontDatabase.addApplicationFont(font_path)
        font_family = QFontDatabase.applicationFontFamilies(font_id)[0]
        font = QFont(font_family, 12)
        self.summary_text.setFont(font)
        
        input_layout.addWidget(self.summary_text)
        input_group.setLayout(input_layout)
        layout.addWidget(input_group)
        
        # 버튼 그룹
        button_layout = QHBoxLayout()
        
        self.apply_btn = QPushButton("개요 적용")
        self.apply_btn.clicked.connect(self.apply_summary)
        
        self.clear_btn = QPushButton("초기화")
        self.clear_btn.clicked.connect(self.clear_summary)
        
        button_layout.addWidget(self.apply_btn)
        button_layout.addWidget(self.clear_btn)
        
        layout.addLayout(button_layout)
        
        # 상태 표시 레이블
        self.status_label = QLabel("")
        layout.addWidget(self.status_label)
        
        layout.addStretch()
        self.setLayout(layout)
        
    def apply_summary(self):
        summary_text = self.summary_text.toPlainText()
        if summary_text:
            # TODO: 개요 적용 로직 구현
            self.status_label.setText("개요가 적용되었습니다.")
        else:
            self.status_label.setText("개요를 입력해주세요.")
            
    def clear_summary(self):
        self.summary_text.clear()
        self.status_label.setText("")
