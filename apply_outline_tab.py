from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, 
                           QPushButton, QLabel, QGroupBox)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont, QFontDatabase
import os
from custom_text_edit import CustomTextEdit
from drop_area_widget import DropAreaWidget

class ApplyOutlineTab(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent
        self.initUI()
        
    def initUI(self):
        layout = QVBoxLayout()
        layout.setSpacing(20)  # 위젯 간 간격 설정
        
        # 개요 파일 드롭 영역
        outline_group = QGroupBox("개요 파일")
        outline_layout = QVBoxLayout()
        self.outline_drop_area = DropAreaWidget(['txt'], self)
        outline_layout.addWidget(self.outline_drop_area)
        outline_group.setLayout(outline_layout)
        layout.addWidget(outline_group)
        
        # PDF 파일 드롭 영역
        pdf_group = QGroupBox("PDF 파일")
        pdf_layout = QVBoxLayout()
        self.pdf_drop_area = DropAreaWidget(['pdf'], self)
        pdf_layout.addWidget(self.pdf_drop_area)
        pdf_group.setLayout(pdf_layout)
        layout.addWidget(pdf_group)
        
        # 버튼 영역
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        layout.addLayout(button_layout)
        
        self.setLayout(layout)