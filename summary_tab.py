from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, 
                           QPushButton, QLabel, QGroupBox, QFileDialog,
                           QMessageBox, QDialog)
from PyQt5.QtCore import Qt, QProcess, QSettings, QFileSystemWatcher
from PyQt5.QtGui import QFont, QFontDatabase
import os
import tempfile
from custom_text_edit import CustomTextEdit
from outline_ocr import apply_indentation, apply_page_offset
from settings_dialog import SettingsDialog

class SummaryTab(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent
        self.temp_file = None  # 임시 파일 객체 저장
        self.process = None  # QProcess 객체 저장
        self.current_filename = ""  # 현재 파일명 저장
        self.current_file_path = ""  # 현재 파일 경로 저장
        self.file_watcher = QFileSystemWatcher()  # 파일 변경 감지
        self.file_watcher.fileChanged.connect(self.on_file_changed)  # 파일 변경 시그널 연결
        self.initUI()
        
    def initUI(self):
        layout = QVBoxLayout()
        layout.setSpacing(10)  # 위젯 간 간격 설정
        
        # 현재 파일명 표시
        filename_layout = QHBoxLayout()
        filename_label = QLabel("현재 파일:")
        filename_label.setStyleSheet("font-weight: bold;")
        self.current_filename_label = QLabel("")
        self.current_filename_label.setStyleSheet("color: #0066cc;")
        filename_layout.addWidget(filename_label)
        filename_layout.addWidget(self.current_filename_label)
        filename_layout.addStretch()
        layout.addLayout(filename_layout)
        
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
        
        input_layout.addWidget(self.summary_text, stretch=1)
        input_group.setLayout(input_layout)
        layout.addWidget(input_group, stretch=1)
        
        # 버튼 그룹
        button_layout = QHBoxLayout()
        
        # 외부 편집기로 열기 버튼
        self.open_editor_btn = QPushButton("편집기로 열기")
        self.open_editor_btn.clicked.connect(self.open_in_editor)
        button_layout.addWidget(self.open_editor_btn)
        
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
            
    def open_in_editor(self):
        """현재 텍스트를 외부 편집기로 열기"""
        content = self.summary_text.toPlainText()
        if not content.strip():
            self.status_label.setText("편집할 내용이 없습니다.")
            return
            
        # 설정에서 편집기 경로 가져오기
        settings = QSettings("AutoPdfCap", "Settings")
        editor_path = settings.value("editor_path", "")
        
        if not editor_path:
            reply = QMessageBox.question(
                self, 
                "편집기 설정 필요", 
                "외부 편집기가 설정되지 않았습니다. 지금 설정하시겠습니까?",
                QMessageBox.Yes | QMessageBox.No
            )
            
            if reply == QMessageBox.Yes:
                dialog = SettingsDialog(self)
                if dialog.exec_() == QDialog.Accepted:
                    editor_path = settings.value("editor_path", "")
                else:
                    return
            else:
                return
                
        if not editor_path:  # 여전히 편집기가 설정되지 않은 경우
            return
            
        try:
            # 현재 파일명이 없으면 기본 파일명 사용
            if not self.current_filename:
                self.current_filename = self.get_default_filename()
                if not self.current_filename:
                    self.current_filename = "untitled_outlines.txt"
                self.current_filename_label.setText(self.current_filename)
            
            # 현재 디렉터리에 파일 생성
            self.current_file_path = os.path.join(os.getcwd(), self.current_filename)
            with open(self.current_file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            # 파일 감시 시작
            if self.current_file_path in self.file_watcher.files():
                self.file_watcher.removePath(self.current_file_path)
            self.file_watcher.addPath(self.current_file_path)
            
            # 이전 프로세스가 있다면 정리
            if self.process is not None:
                self.process.close()
            
            # 외부 편집기로 파일 열기
            self.process = QProcess()
            self.process.start(editor_path, [self.current_file_path])
            
            self.status_label.setText(f"외부 편집기에서 파일이 열렸습니다: {self.current_filename}")
            
        except Exception as e:
            QMessageBox.critical(self, "오류", f"편집기로 열기 실패: {str(e)}")
            self.status_label.setText("편집기로 열기 실패")
            
    def on_file_changed(self, path):
        """파일이 변경되면 호출되는 함수"""
        try:
            # 파일이 존재하는지 확인 (삭제되지 않았는지)
            if os.path.exists(path):
                with open(path, 'r', encoding='utf-8') as f:
                    content = f.read()
                self.summary_text.setPlainText(content)
                self.status_label.setText("파일이 업데이트되었습니다.")
                
                # 일부 에디터는 파일을 저장할 때 새로운 파일을 만들고 이름을 바꾸는 방식을 사용
                # 이 경우 파일 감시를 다시 설정해야 함
                if path not in self.file_watcher.files():
                    self.file_watcher.addPath(path)
                    
        except Exception as e:
            self.status_label.setText(f"파일 업데이트 실패: {str(e)}")
            
    def set_current_filename(self, filename: str):
        """현재 파일명 설정 및 표시"""
        self.current_filename = filename
        self.current_filename_label.setText(filename)
        
    def get_default_filename(self):
        """기본 탭의 파일 이름을 가져와서 .txt 확장자를 붙여 반환"""
        try:
            basic_tab = self.parent.tab_widget.widget(0)  # 첫 번째 탭(BasicTab)
            filename = basic_tab.file_name_edit.text().strip()
            if filename and not filename.lower().endswith('.txt'):
                filename += '.txt'
            return filename
        except Exception:
            return ""
        
    def save_file(self):
        """현재 텍스트를 파일로 저장"""
        content = self.summary_text.toPlainText()
        if not content.strip():
            self.status_label.setText("저장할 내용이 없습니다.")
            return
            
        default_name = self.get_default_filename()
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "파일 저장하기",
            default_name,  # 기본 파일 이름 설정
            "텍스트 파일 (*.txt);;모든 파일 (*.*)"
        )
        
        if file_path:
            try:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                self.status_label.setText(f"파일이 저장되었습니다: {os.path.basename(file_path)}")
            except Exception as e:
                self.status_label.setText(f"파일 저장 실패: {str(e)}")
                
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

    def update_from_ocr_tab(self, text_content):
        """OCR 탭에서 텍스트 업데이트"""
        self.summary_text.setPlainText(text_content)
        
        # 기본 탭의 파일명 가져오기
        try:
            basic_tab = self.parent.tab_widget.widget(0)  # 첫 번째 탭(BasicTab)
            filename = basic_tab.file_name_edit.text().strip()
            if filename:
                self.set_current_filename(filename + ".txt")
        except Exception:
            pass

    def closeEvent(self, event):
        """위젯이 닫힐 때 파일 감시 중지"""
        if hasattr(self, 'current_file_path') and self.current_file_path:
            if self.current_file_path in self.file_watcher.files():
                self.file_watcher.removePath(self.current_file_path)
        event.accept()