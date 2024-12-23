from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, 
                           QPushButton, QLabel, QGroupBox, QFileDialog)
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
        input_group = QGroupBox("OCR 추출 결과")
        input_layout = QVBoxLayout()
        
        # OCR 결과를 표시할 CustomTextEdit 추가
        self.summary_text = CustomTextEdit()
        self.summary_text.setPlaceholderText("OCR 탭에서 추출된 텍스트가 여기에 표시됩니다...")
        
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
        
        # 파일 불러오기 버튼 추가
        self.load_btn = QPushButton("파일 불러오기")
        self.load_btn.clicked.connect(self.load_file)
        button_layout.addWidget(self.load_btn)
        
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
        
    def load_file(self):
        """파일 불러오기"""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "개요 파일 불러오기",
            "",
            "텍스트 파일 (*.txt);;모든 파일 (*.*)"
        )
        
        if file_path:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                self.summary_text.setPlainText(content)
                self.status_label.setText(f"파일을 불러왔습니다: {os.path.basename(file_path)}")
            except Exception as e:
                self.status_label.setText(f"파일 불러오기 실패: {str(e)}")
        
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
