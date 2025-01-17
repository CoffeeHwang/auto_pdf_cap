from PyQt5.QtWidgets import (QMainWindow, QPushButton, QWidget, 
                           QVBoxLayout, QSlider, QLabel, QHBoxLayout, QLineEdit, QSpinBox, QGroupBox, QTextEdit, QTabWidget,
                           QMenuBar, QMenu, QAction, QShortcut)
from PyQt5.QtCore import Qt, QRect, QPoint, QThread
from PyQt5.QtGui import QKeySequence
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
        self.initUI()
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
            
        # BasicTab 설정 불러오기
        self.basic_tab.loadSettings()

    def saveSettings(self):
        """현재 설정 저장"""
        # 창 위치/크기 저장
        self.settings.setValue('MainWindow/geometry', self.saveGeometry())
        
        # BasicTab 설정 저장
        self.basic_tab.saveSettings()

    def closeEvent(self, event):
        """프로그램 종료 시 설정 저장"""
        self.saveSettings()
        event.accept()

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
        
        # 보기 메뉴
        view_menu = menubar.addMenu('보기')
        
        # 항상위 토글 액션
        self.always_on_top_action = QAction('항상위', self, checkable=True)
        self.always_on_top_action.setStatusTip('창을 항상 위에 표시')
        self.always_on_top_action.triggered.connect(self.toggle_always_on_top)
        view_menu.addAction(self.always_on_top_action)
        
        # 저장된 항상위 설정 불러오기
        is_always_on_top = self.settings.value('MainWindow/always_on_top', 'false').lower() == 'true'
        self.always_on_top_action.setChecked(is_always_on_top)
        self.toggle_always_on_top(is_always_on_top)

    def toggle_always_on_top(self, checked: bool):
        """항상위 설정을 토글"""
        flags = self.windowFlags()
        if checked:
            self.setWindowFlags(flags | Qt.WindowType.WindowStaysOnTopHint)
        else:
            self.setWindowFlags(flags & ~Qt.WindowType.WindowStaysOnTopHint)
            
        # 창 숨김/표시로 설정 적용
        self.show()
        
        # 설정 저장
        self.settings.setValue('MainWindow/always_on_top', str(checked).lower())

    def show_settings(self):
        """환경설정 창을 표시"""
        dialog = SettingsDialog(self)
        dialog.exec_()

    def setup_shortcuts(self):
        """단축키 설정"""
        # 윈도우 닫기 단축키
        close_shortcut = QShortcut(QKeySequence.StandardKey.Close, self)  # macOS에서는 CMD+W로 동작
        close_shortcut.activated.connect(self.close)

# end of file