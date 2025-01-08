from PyQt5.QtWidgets import (QMainWindow, QPushButton, QWidget, 
                           QVBoxLayout, QSlider, QLabel, QHBoxLayout, QLineEdit, QSpinBox, QGroupBox, QTextEdit, QTabWidget,
                           QMenuBar, QMenu, QAction, QShortcut)
from PyQt5.QtCore import Qt, QRect, QPoint, QThread
from PyQt5.QtGui import QKeySequence
from modaless_window import ModalessWindow
from worker_cap import WorkerCapture
from tab_basic import BasicTab
from tab_ocr import OcrTab
from tab_gen_outline import GenOutlineTab
from settings_dialog import SettingsDialog
from supa_settings import SupaSettings
import sys

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.settings = SupaSettings()  
        self.modaless_window = None
        self.initUI()
        self.create_modaless()  # 시작 시 모달리스 창 생성만 하고 보이지 않게 함
        self.loadSettings()   # 설정 불러오기
        self.setup_shortcuts()

    def initUI(self):
        # 메뉴바 생성
        self.create_menu_bar()
        
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)

        # QTabWidget 추가
        self.tab_widget = QTabWidget(self)
        layout.addWidget(self.tab_widget)  # 기존 레이아웃에 탭 위젯 추가
    
        # 첫 번째 탭
        self.basic_tab = BasicTab(self)
        self.tab_widget.addTab(self.basic_tab, "캡쳐자동화")

        # 두 번째 탭
        self.ocr_tab = OcrTab(self)
        self.tab_widget.addTab(self.ocr_tab, "개요OCR추출")

        # 세 번째 탭
        self.gen_outline_tab = GenOutlineTab(self)
        self.tab_widget.addTab(self.gen_outline_tab, "개요적용")

        self.setWindowTitle('메인 창')
        self.setGeometry(100, 100, 500, 400)

    def loadSettings(self):
        """저장된 설정 불러오기"""
        # 창 위치/크기 설정 불러오기
        geometry = self.settings.value('MainWindow/geometry')
        if geometry:
            self.restoreGeometry(geometry)
            
        # SpinBox 값들 불러오기
        x1 = int(self.settings.value('MainWindow/x1', 0))
        y1 = int(self.settings.value('MainWindow/y1', 0))
        x2 = int(self.settings.value('MainWindow/x2', 0))
        y2 = int(self.settings.value('MainWindow/y2', 0))
        
        self.basic_tab.x1_spin.setValue(x1)
        self.basic_tab.y1_spin.setValue(y1)
        self.basic_tab.x2_spin.setValue(x2)
        self.basic_tab.y2_spin.setValue(y2)
        
        # LineEdit 값들 불러오기
        self.basic_tab.margin_edit.setText(self.settings.value('MainWindow/margin', '0'))
        self.basic_tab.diff_width_edit.setText(self.settings.value('MainWindow/diff_width', '0'))
        
        # 투명도 슬라이더 값 불러오기
        opacity = int(self.settings.value('MainWindow/opacity', 50))
        self.basic_tab.opacity_slider.setValue(opacity)
        self.basic_tab.opacity_label.setText(f'투명도: {opacity}%')
        
        # 모달리스 창 설정 불러오기
        if self.modaless_window:
            # 창 위치/크기 복원
            modaless_geometry = self.settings.value('ModalessWindow/geometry')
            if modaless_geometry:
                self.modaless_window.restoreGeometry(modaless_geometry)
            
            # 투명도 적용
            self.modaless_window.setWindowOpacity(opacity / 100.0)
            
            # 저장된 사각형이 있다면 복원
            if x1 or y1 or x2 or y2:  # 하나라도 0이 아닌 값이 있다면
                window_pos = self.modaless_window.mapToGlobal(QPoint(0, 0))
                rect = QRect(
                    x1 - window_pos.x(),
                    y1 - window_pos.y(),
                    x2 - x1,
                    y2 - y1
                )
                self.modaless_window.rectangle = rect
                self.modaless_window.can_draw = False  # 새로 그리기 방지
                self.modaless_window.update()
        
        # 기타설정값 불러오기
        self.basic_tab.file_name_edit.setText(self.settings.value('MainWindow/file_name', ''))
        self.basic_tab.page_loop_edit.setText(self.settings.value('MainWindow/page_loop', ''))
        self.basic_tab.delay_edit.setText(self.settings.value('MainWindow/capture_delay', '0'))

    def saveSettings(self):
        """현재 설정 저장"""
        # 창 위치/크기 저장
        self.settings.setValue('MainWindow/geometry', self.saveGeometry())
        
        # SpinBox 값들 저장
        self.settings.setValue('MainWindow/x1', self.basic_tab.x1_spin.value())
        self.settings.setValue('MainWindow/y1', self.basic_tab.y1_spin.value())
        self.settings.setValue('MainWindow/x2', self.basic_tab.x2_spin.value())
        self.settings.setValue('MainWindow/y2', self.basic_tab.y2_spin.value())
        
        # LineEdit 값들 저장
        self.settings.setValue('MainWindow/margin', self.basic_tab.margin_edit.text())
        self.settings.setValue('MainWindow/diff_width', self.basic_tab.diff_width_edit.text())
        
        # 투명도 슬라이더 값 저장
        self.settings.setValue('MainWindow/opacity', self.basic_tab.opacity_slider.value())
        
        # 모달리스 창 설정 저장
        if self.modaless_window:
            self.settings.setValue('ModalessWindow/geometry', 
                                 self.modaless_window.saveGeometry())
        
        # 기타설정값 저장
        self.settings.setValue('MainWindow/file_name', self.basic_tab.file_name_edit.text())
        self.settings.setValue('MainWindow/page_loop', self.basic_tab.page_loop_edit.text())
        self.settings.setValue('MainWindow/capture_delay', self.basic_tab.delay_edit.text())

    def closeEvent(self, event):
        """프로그램 종료 시 설정 저장"""
        self.saveSettings()
        if self.modaless_window:
            self.modaless_window.close()
        event.accept()

    def create_modaless(self):
        """모달리스 창을 생성만 하고 보이지 않게 함"""
        if self.modaless_window is None:
            self.modaless_window = ModalessWindow(parent=self)
            
            # 저장된 투명도 적용
            opacity = self.basic_tab.opacity_slider.value() / 100.0
            self.modaless_window.setWindowOpacity(opacity)
            
            # 저장된 모달리스 창 설정 불러오기
            modaless_geometry = self.settings.value('ModalessWindow/geometry')
            if modaless_geometry:
                self.modaless_window.restoreGeometry(modaless_geometry)
            else:
                # 기본 위치와 크기 설정
                self.modaless_window.setGeometry(300, 300, 400, 300)

    def show_modaless(self):
        """모달리스 창을 생성하고 보이게 함"""
        if self.modaless_window is None:
            self.create_modaless()
        self.modaless_window.show()

    def change_opacity(self, value):
        if self.modaless_window is not None:
            opacity = value / 100.0
            self.modaless_window.setWindowOpacity(opacity)
            self.basic_tab.opacity_label.setText(f'투명도: {value}%')
            
    def clear_rectangles(self):
        if self.modaless_window is not None:
            self.modaless_window.rectangle = None
            self.modaless_window.can_draw = True  # 초기화 후 다시 그리기 가능 상태로 변경
            self.modaless_window.update()
            
    def on_coordinate_changed(self):
        if self.modaless_window and self.modaless_window.rectangle: # type: ignore
            # 시그널 블록
            self.basic_tab.x1_spin.blockSignals(True)
            self.basic_tab.y1_spin.blockSignals(True)
            self.basic_tab.x2_spin.blockSignals(True)
            self.basic_tab.y2_spin.blockSignals(True)

            try:
                # 절대 좌표에서 상대 좌표로 변환
                window_pos = self.modaless_window.mapToGlobal(QPoint(0, 0))
                
                # 새로운 상대 좌표 계산
                new_rect = QRect(
                    self.basic_tab.x1_spin.value() - window_pos.x(),
                    self.basic_tab.y1_spin.value() - window_pos.y(),
                    self.basic_tab.x2_spin.value() - self.basic_tab.x1_spin.value(),
                    self.basic_tab.y2_spin.value() - self.basic_tab.y1_spin.value()
                )
                
                # 사각형 업데이트
                self.modaless_window.rectangle = new_rect
                self.modaless_window.update()
            
            finally:
                # 시그널 언블록
                self.basic_tab.x1_spin.blockSignals(False)
                self.basic_tab.y1_spin.blockSignals(False)
                self.basic_tab.x2_spin.blockSignals(False)
                self.basic_tab.y2_spin.blockSignals(False)

    def on_margin_changed(self):
        """Margin 값이 변경될 때 모달리스 창 업데이트"""
        if self.modaless_window:
            self.modaless_window.update()

    def on_diff_width_changed(self):
        """Diff Width 값이 변경될 때 모달리스 창 업데이트"""
        if self.modaless_window:
            self.modaless_window.update()

    def toggle_modaless(self):
        """모달리스 창 보이기/숨기기 토글"""
        if self.modaless_window is None:
            self.show_modaless()
        else:
            if self.modaless_window.isVisible():
                self.modaless_window.hide()
            else:
                self.modaless_window.show()

    def log_message(self, message):
        """로그 메시지를 추가하는 메서드"""
        self.basic_tab.log_text_edit.append(message)  # 메시지를 추가
        self.basic_tab.log_text_edit.verticalScrollBar().setValue(self.basic_tab.log_text_edit.verticalScrollBar().maximum()) # type: ignore

    def start_process(self):
        self.modaless_window.hide() # type: ignore
        # QThread를 사용하여 auto_pdf_capture를 비동기로 실행
        self.thread = QThread() # type: ignore
        self.worker = WorkerCapture(self,
                             self.basic_tab.file_name_edit.text(), 
                             int(self.basic_tab.page_loop_edit.text()),
                             int(self.basic_tab.x1_spin.value()), 
                             int(self.basic_tab.y1_spin.value()),
                             int(self.basic_tab.x2_spin.value()), 
                             int(self.basic_tab.y2_spin.value()),
                             int(self.basic_tab.margin_edit.text()), 
                             int(self.basic_tab.diff_width_edit.text()),
                             float(self.basic_tab.delay_edit.text()),
                             self.basic_tab.left_first_check.isChecked())
        self.worker.moveToThread(self.thread) # type: ignore

        self.thread.started.connect(self.worker.run)
        self.worker.finished.connect(self.thread.quit)
        self.worker.finished.connect(self.worker.deleteLater)
        self.thread.finished.connect(self.thread.deleteLater)
        self.thread.finished.connect(lambda: self.basic_tab.btn_start.setText("시작"))

        self.thread.start()

    def stop_process(self):
        """캡쳐 프로세스를 중지합니다."""
        if hasattr(self, 'worker'):
            self.worker.stop()
            self.log_message("캡쳐를 중지했습니다.")

    def create_menu_bar(self):
        """메뉴바 생성 및 설정"""
        menubar = self.menuBar()
        
        # 파일 메뉴
        file_menu = menubar.addMenu('파일')
        
        # 환경설정 메뉴 항목
        settings_action = QAction('환경설정...', self)
        settings_action.setShortcut('Ctrl+,')  # macOS 스타일 단축키
        settings_action.triggered.connect(self.show_settings)
        file_menu.addAction(settings_action)
        
    def show_settings(self):
        """환경설정 창을 표시"""
        dialog = SettingsDialog(self)
        dialog.exec_()

    def setup_shortcuts(self):
        """단축키 설정"""
        # 윈도우 닫기 단축키
        close_shortcut = QShortcut(QKeySequence.StandardKey.Close, self)  # macOS에서는 CMD+W로 동작
        close_shortcut.activated.connect(self.close)