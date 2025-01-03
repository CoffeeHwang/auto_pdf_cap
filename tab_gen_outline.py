from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, 
                           QPushButton, QLabel, QGroupBox, QFileDialog,
                           QMessageBox, QDialog, QTextEdit, QStyle)
from PyQt5.QtCore import Qt, QFileSystemWatcher
from PyQt5.QtGui import QFont, QFontDatabase, QIcon
import os
import sys
import subprocess
from custom_text_edit import CustomTextEdit
from outline_ocr import apply_indentation, apply_page_offset, apply_none_page
from pypdf2_ol_gen import pdf_outline_gen
from settings_dialog import SettingsDialog
from supa_common import log
from drop_area_widget import DropAreaWidget
from supa_settings import SupaSettings

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from tab_basic import BasicTab

class GenOutlineTab(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent    
        self.temp_file = None  # 임시 파일 객체 저장
        
        # 기본 저장 디렉토리 설정
        if getattr(sys, 'frozen', False):
            # PyInstaller로 실행된 경우
            self.save_directory = os.path.dirname(sys.executable)
        else:
            # 일반 Python으로 실행된 경우
            self.save_directory = os.path.dirname(os.path.abspath(__file__))
            
        self.current_file_path = ""  # 현재 파일 경로
        self.file_watcher = QFileSystemWatcher()  # 파일 변경 감지
        self.file_watcher.fileChanged.connect(self.on_file_changed)  # 파일 변경 시그널 연결
        self.initUI()
        
        # BasicTab의 파일명 변경 시그널 연결
        try:
            basic_tab: BasicTab = self.parent.tab_widget.widget(0)  # 첫 번째 탭(BasicTab)
            basic_tab.filename_changed.connect(self._on_basic_tab_filename_changed)
            # 초기 파일명이 있다면 적용
            initial_filename = basic_tab.file_name_edit.text().strip()
            if initial_filename:
                self._on_basic_tab_filename_changed(initial_filename)
        except (AttributeError, TypeError) as e:
            print(f"BasicTab 초기화 중 오류 발생: {e}")  # 로깅으로 대체 가능
            
    def initUI(self):
        layout = QVBoxLayout()
        layout.setSpacing(10)  # 위젯 간 간격 설정
        
        # 현재 파일명 표시
        filename_layout = QHBoxLayout()
        filename_label = QLabel("현재 파일:")
        filename_label.setStyleSheet("font-weight: bold;")
        self.current_filename_label = QLabel("")
        self.current_filename_label.setStyleSheet("color: #0066cc;")
        
        # 파일 위치 열기 버튼
        self.btn_open_location = QPushButton()
        self.btn_open_location.setIcon(self.style().standardIcon(QStyle.SP_DialogOpenButton))  # 폴더 열기 아이콘
        self.btn_open_location.setToolTip("파일 위치 열기")
        self.btn_open_location.setFixedSize(24, 24)  # 버튼 크기 고정
        self.btn_open_location.setStyleSheet("""
            QPushButton {
                border: none;
                background-color: transparent;
            }
            QPushButton:hover {
                background-color: #e0e0e0;
                border-radius: 3px;
            }
        """)
        self.btn_open_location.clicked.connect(self._open_file_location)
        self.btn_open_location.setEnabled(False)  # 초기에는 비활성화
        
        filename_layout.addWidget(filename_label)
        filename_layout.addWidget(self.current_filename_label)
        filename_layout.addWidget(self.btn_open_location)
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
        self.open_editor_btn = QPushButton("편집기 열기")
        self.open_editor_btn.clicked.connect(self.open_in_editor)
        button_layout.addWidget(self.open_editor_btn)
        
        self.gen_outline_btn = QPushButton("개요포맷")
        self.gen_outline_btn.clicked.connect(self.gen_outline)
        
        self.clear_btn = QPushButton("누락페이지")
        self.clear_btn.clicked.connect(self.apply_none_page)
        
        # 페이지 번호 조절 버튼 추가
        self.increase_btn = QPushButton("페이지넘버 +1")
        self.increase_btn.clicked.connect(self.increase_pages)
        
        self.decrease_btn = QPushButton("페이지넘버 -1")
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
        settings = SupaSettings()
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
            filename = self.get_default_filename()
            if not filename:
                filename = "untitled_outlines.txt"
            self.current_filename_label.setText(filename)
            
            # 현재 디렉터리에 파일 생성
            self.current_file_path = os.path.join(self.save_directory, filename)
            with open(self.current_file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            # 파일 감시 시작
            if self.current_file_path in self.file_watcher.files():
                self.file_watcher.removePath(self.current_file_path)
            self.file_watcher.addPath(self.current_file_path)
            
            # 외부 편집기로 파일 열기
            subprocess.run([editor_path, self.current_file_path])
            
            self.status_label.setText(f"외부 편집기에서 파일이 열렸습니다: {filename}")
            
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
        self.current_filename_label.setText(filename)
        # 파일 경로 업데이트
        self.current_file_path = os.path.join(self.save_directory, filename)
        # 파일명이 있을 때만 위치 열기 버튼 활성화
        self.btn_open_location.setEnabled(bool(filename.strip()))
        
    def get_default_filename(self) -> str:
        """기본 탭의 파일 이름을 가져와서 .txt 확장자를 붙여 반환"""
        try:
            filename = self.current_filename_label.text()
            if not filename:  # 파일명이 없으면 빈 문자열 반환
                return ""
                
            # 확장자가 .txt가 아니면 .txt를 붙여서 반환
            if not filename.lower().endswith('.txt'):
                filename = filename.rsplit('.', 1)[0] + '.txt'
            return filename
        except Exception:
            return ""
                
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
        (success, result_msg) = pdf_outline_gen(
            pdf_file=self.pdf_drop_area.file_path,
            ol_file=self.current_file_path,
            depth_sep='    ',
            page_sep='\t'
        )
        self.status_label.setText(result_msg)
        if success :
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
        
    def _on_basic_tab_filename_changed(self, filename: str):
        """BasicTab의 파일명이 변경될 때 호출되는 메서드"""
        if filename.strip():
            # .txt 확장자 추가
            if not filename.lower().endswith('.txt'):
                filename = filename.rsplit('.', 1)[0] + '.txt'
            self.set_current_filename(filename)
            
    def _open_file_location(self):
        """현재 파일이 있는 위치를 파인더에서 열기"""
        if not self.current_file_path or not os.path.exists(self.current_file_path):
            QMessageBox.warning(self, "경고", "파일이 아직 저장되지 않았습니다.")
            return
            
        try:
            subprocess.run(["open", "-R", self.current_file_path])
        except Exception as e:
            QMessageBox.critical(self, "오류", f"파일 위치를 열 수 없습니다: {str(e)}")