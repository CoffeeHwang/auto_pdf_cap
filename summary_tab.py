from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, 
                           QPushButton, QLabel, QGroupBox, QFileDialog)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont, QFontDatabase
import os
from custom_text_edit import CustomTextEdit
from outline_ocr import apply_indentation, apply_page_offset

class SummaryTab(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent
        self.initUI()
        
    def initUI(self):
        layout = QVBoxLayout()
        layout.setSpacing(10)  # 위젯 간 간격 설정
        
        # 개요 입력 그룹
        input_group = QGroupBox("OCR 추출 결과")
        input_layout = QVBoxLayout()
        input_layout.setSpacing(5)  # 내부 위젯 간 간격 설정
        
        # 안내 레이블 추가
        label = QLabel("텍스트 파일을 드래그하여 추가할 수 있습니다")
        input_layout.addWidget(label)
        
        # OCR 결과를 표시할 CustomTextEdit 추가
        self.summary_text = CustomTextEdit(self)  # parent 설정
        self.summary_text.setPlaceholderText("OCR 탭에서 추출된 텍스트가 여기에 표시됩니다...")
        self.summary_text.setFrameStyle(0)  # 프레임 제거
        
        # D2Coding 폰트 로드 및 설정
        font_path = os.path.join(os.path.dirname(__file__), 'fonts', 'D2Coding.ttf')
        font_id = QFontDatabase.addApplicationFont(font_path)
        font_family = QFontDatabase.applicationFontFamilies(font_id)[0]
        font = QFont(font_family, 12)
        self.summary_text.setFont(font)
        
        # CustomTextEdit를 layout에 추가할 때 stretch factor를 1로 설정
        input_layout.addWidget(self.summary_text, stretch=1)
        input_group.setLayout(input_layout)
        layout.addWidget(input_group, stretch=1)
        
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
        
        # 페이지 번호 조절 버튼 추가
        self.increase_btn = QPushButton("페이지 +1")
        self.increase_btn.clicked.connect(self.increase_pages)
        
        self.decrease_btn = QPushButton("페이지 -1")
        self.decrease_btn.clicked.connect(self.decrease_pages)
        
        button_layout.addWidget(self.apply_btn)
        button_layout.addWidget(self.clear_btn)
        button_layout.addWidget(self.increase_btn)
        button_layout.addWidget(self.decrease_btn)
        
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
            self.load_text_from_file(file_path)
    
    def load_text_from_file(self, file_path):
        """파일에서 텍스트 불러오기"""
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
            # 현재 스크롤바 위치 저장
            scrollbar = self.summary_text.verticalScrollBar()
            current_scroll = scrollbar.value()
            
            # 텍스트 적용
            ocr_lines = apply_indentation(input_lines=summary_text.split('\n'))
            self.summary_text.setPlainText("\n".join(ocr_lines))
            
            # 스크롤바 위치 복원
            scrollbar.setValue(current_scroll)
            
            self.status_label.setText("개요가 적용되었습니다.")
        else:
            self.status_label.setText("개요를 입력해주세요.")
            
    def clear_summary(self):
        self.summary_text.clear()
        self.status_label.setText("")
        
    def increase_pages(self):
        """모든 페이지 번호를 1씩 증가"""
        summary_text = self.summary_text.toPlainText()
        if summary_text:
            # 현재 스크롤바 위치 저장
            scrollbar = self.summary_text.verticalScrollBar()
            current_scroll = scrollbar.value()
            
            # 텍스트 적용
            ocr_lines = apply_page_offset(input_lines=summary_text.split('\n'), page_offset=1)
            self.summary_text.setPlainText("\n".join(ocr_lines))
            
            # 스크롤바 위치 복원
            scrollbar.setValue(current_scroll)
            
            self.status_label.setText("페이지 번호가 1+ 오프셋 적용되었습니다.")
        
    def decrease_pages(self):
        """모든 페이지 번호를 1씩 감소"""
        summary_text = self.summary_text.toPlainText()
        if summary_text:
            # 현재 스크롤바 위치 저장
            scrollbar = self.summary_text.verticalScrollBar()
            current_scroll = scrollbar.value()
            
            # 텍스트 적용
            ocr_lines = apply_page_offset(input_lines=summary_text.split('\n'), page_offset=-1)
            self.summary_text.setPlainText("\n".join(ocr_lines))
            
            # 스크롤바 위치 복원
            scrollbar.setValue(current_scroll)
            
            self.status_label.setText("페이지 번호가 1- 오프셋 적용되었습니다.")

# end of file