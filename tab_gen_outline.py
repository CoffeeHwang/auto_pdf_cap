from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, 
                           QPushButton, QLabel, QGroupBox, QFileDialog,
                           QMessageBox, QDialog)
from PyQt5.QtCore import Qt, QProcess, QSettings, QFileSystemWatcher
from PyQt5.QtGui import QFont, QFontDatabase
import os
import sys
import subprocess
from custom_text_edit import CustomTextEdit
from outline_ocr import apply_indentation, apply_page_offset, apply_none_page
from pypdf2_ol_gen import pdf_outline_gen
from settings_dialog import SettingsDialog
from supa_common import log
from drop_area_widget import DropAreaWidget

class GenOutlineTab(QWidget):
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
        self.te_outlines = CustomTextEdit(self)  # parent 설정
        self.te_outlines.setPlaceholderText("OCR 탭에서 추출된 텍스트가 여기에 표시됩니다...")
        self.te_outlines.setFrameStyle(0)  # 프레임 제거
        
        # D2Coding 폰트 로드 및 설정
        font_path = os.path.join(os.path.dirname(__file__), 'fonts', 'D2Coding.ttf')
        font_id = QFontDatabase.addApplicationFont(font_path)
        font_family = QFontDatabase.applicationFontFamilies(font_id)[0]
        font = QFont(font_family, 12)
        self.te_outlines.setFont(font)
        
        input_layout.addWidget(self.te_outlines, stretch=1)
        input_group.setLayout(input_layout)
        layout.addWidget(input_group, stretch=1)
        
        # 버튼 그룹
        button_layout = QHBoxLayout()
        
        # 외부 편집기로 열기 버튼
        self.open_editor_btn = QPushButton("편집기로 열기")
        self.open_editor_btn.clicked.connect(self.open_in_editor)
        button_layout.addWidget(self.open_editor_btn)
        
        self.gen_outline_btn = QPushButton("개요생성")
        self.gen_outline_btn.clicked.connect(self.gen_outline)
        
        self.clear_btn = QPushButton("페이지채우기")
        self.clear_btn.clicked.connect(self.apply_none_page)
        
        # 페이지 번호 조절 버튼 추가
        self.increase_btn = QPushButton("페이지 +1")
        self.increase_btn.clicked.connect(self.increase_pages)
        
        self.decrease_btn = QPushButton("페이지 -1")
        self.decrease_btn.clicked.connect(self.decrease_pages)
        
        button_layout.addWidget(self.gen_outline_btn)
        button_layout.addWidget(self.clear_btn)
        button_layout.addWidget(self.increase_btn)
        button_layout.addWidget(self.decrease_btn)
        
        # 개요적용 버튼 추가
        self.apply_outline_btn = QPushButton("개요적용")
        self.apply_outline_btn.clicked.connect(self.apply_outline)
        button_layout.addWidget(self.apply_outline_btn)
        
        layout.addLayout(button_layout)
        
        # PDF 파일 드롭 영역 추가
        pdf_group = QGroupBox("PDF 파일")
        pdf_layout = QVBoxLayout()
        self.pdf_drop_area = DropAreaWidget(['pdf'], self)
        pdf_layout.addWidget(self.pdf_drop_area)
        pdf_group.setLayout(pdf_layout)
        layout.addWidget(pdf_group)
        
        # 상태 표시 레이블
        self.status_label = QLabel("")
        layout.addWidget(self.status_label)
        
        layout.addStretch()
        self.setLayout(layout)
            
    def open_in_editor(self):
        """현재 텍스트를 외부 편집기로 열기"""
        content = self.te_outlines.toPlainText()
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
                self.te_outlines.setPlainText(content)
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
        content = self.te_outlines.toPlainText()
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
                
    def gen_outline(self):
        """개요 적용"""
        te_outlines = self.te_outlines.toPlainText()
        if te_outlines:
            # 현재 스크롤바 위치 저장
            scrollbar = self.te_outlines.verticalScrollBar()
            current_scroll = scrollbar.value()
            
            # 텍스트 적용
            ocr_lines = apply_indentation(input_lines=te_outlines.split('\n'))
            self.te_outlines.setPlainText("\n".join(ocr_lines))
            
            # 스크롤바 위치 복원
            scrollbar.setValue(current_scroll)
            
            self.status_label.setText("개요가 적용되었습니다.")
        else:
            self.status_label.setText("개요를 입력해주세요.")
            
    def apply_none_page(self):
        te_outlines = self.te_outlines.toPlainText()
        if te_outlines:
            # 현재 스크롤바 위치 저장
            scrollbar = self.te_outlines.verticalScrollBar()
            current_scroll = scrollbar.value()
            
            # 텍스트 적용
            ocr_lines = apply_none_page(input_lines=te_outlines.split('\n'), page_offset=-1)
            self.te_outlines.setPlainText("\n".join(ocr_lines))
            
            # 스크롤바 위치 복원
            scrollbar.setValue(current_scroll)
            
            self.status_label.setText("빈 페이지를 채웠습니다.")
        else:
            self.status_label.setText("개요를 입력해주세요.")
        
    def apply_outline(self):
        """개요 적용"""
        log(self)
        # 안전 검사
        if not self.pdf_drop_area.file_path:
            self.status_label.setText("PDF 파일이 선택되지 않았습니다.")
            return
        if not self.current_file_path:
            self.status_label.setText("개요 파일이 생성되지 않았습니다.")
            return
        if not os.path.exists(self.current_file_path):
            self.status_label.setText("개요 파일이 존재하지 않습니다.")
            return
        
        # 개요 pdf 파일적용 로직
        pdf_outline_gen(
            pdf_file=self.pdf_drop_area.file_path,
            ol_file=self.current_file_path,
            depth_sep='    ',
            page_sep='\t'
        )
        self.status_label.setText("개요가 적용되었습니다.")
        self.open_pdf_location()

    def open_pdf_location(self):
        """생성된 PDF 파일 경로를 탐색기로 오픈"""
        if self.pdf_drop_area.file_path and os.path.exists(self.pdf_drop_area.file_path):
            pdf_dir = os.path.dirname(self.pdf_drop_area.file_path)
            if sys.platform == "win32":
                os.startfile(pdf_dir)
            elif sys.platform == "darwin":
                subprocess.Popen(["open", pdf_dir])
            else:  # linux variants
                subprocess.Popen(["xdg-open", pdf_dir])
            self.status_label.setText("PDF 파일 위치가 열렸습니다.")
        else:
            self.status_label.setText("PDF 파일이 존재하지 않습니다.")

        
    def increase_pages(self):
        """모든 페이지 번호를 1씩 증가"""
        te_outlines = self.te_outlines.toPlainText()
        if te_outlines:
            # 현재 스크롤바 위치 저장
            scrollbar = self.te_outlines.verticalScrollBar()
            current_scroll = scrollbar.value()
            
            # 텍스트 적용
            ocr_lines = apply_page_offset(input_lines=te_outlines.split('\n'), page_offset=1)
            self.te_outlines.setPlainText("\n".join(ocr_lines))
            
            # 스크롤바 위치 복원
            scrollbar.setValue(current_scroll)
            
            self.status_label.setText("페이지 번호가 1+ 오프셋 적용되었습니다.")
        
    def decrease_pages(self):
        """모든 페이지 번호를 1씩 감소"""
        te_outlines = self.te_outlines.toPlainText()
        if te_outlines:
            # 현재 스크롤바 위치 저장
            scrollbar = self.te_outlines.verticalScrollBar()
            current_scroll = scrollbar.value()
            
            # 텍스트 적용
            ocr_lines = apply_page_offset(input_lines=te_outlines.split('\n'), page_offset=-1)
            self.te_outlines.setPlainText("\n".join(ocr_lines))
            
            # 스크롤바 위치 복원
            scrollbar.setValue(current_scroll)
            
            self.status_label.setText("페이지 번호가 1- 오프셋 적용되었습니다.")
        
    def update_from_ocr_tab(self, text_content: str, current_file: str = None):
        """OCR 탭에서 텍스트 업데이트"""
        self.te_outlines.setPlainText(text_content)
        
        # 현재 파일 경로가 전달된 경우 해당 파일명을 사용
        if current_file:
            self.set_current_filename(current_file)
            # PDF 파일 경로도 업데이트
            if os.path.exists(current_file):
                self.pdf_drop_area.set_file_path(current_file)
        else:
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