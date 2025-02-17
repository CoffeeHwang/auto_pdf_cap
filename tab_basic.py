from PyQt6.QtWidgets import (QWidget, QPushButton, QVBoxLayout, QSlider, 
                           QLabel, QHBoxLayout, QLineEdit, QGroupBox, QTextEdit,
                           QCheckBox, QGridLayout, QSizePolicy)
from PyQt6.QtCore import Qt, pyqtSignal, QTimer, QThread
from supa_settings import SupaSettings
from cap_region_window import CapRegionWindow
from worker_cap import WorkerCapture

class BasicTab(QWidget):
    # 파일명이 변경될 때 발생하는 시그널 추가
    filename_changed = pyqtSignal(str)
    
    def __init__(self, main_window=None):
        super().__init__(main_window)
        self.main_window = main_window
        self.settings = SupaSettings()
        self.cap_region_window = None
        self.worker = None
        self.thread = None
        
        # 파일명 변경 타이머 설정
        self._filename_timer = QTimer(self)
        self._filename_timer.setInterval(2000)  # 2초 딜레이
        self._filename_timer.setSingleShot(True)  # 한 번만 실행
        self._filename_timer.timeout.connect(self._emit_filename_changed)
        
        self.setup_ui()
        self.create_cap_region_window()  # 시작 시 캡처 영역 창 생성
        self.loadSettings()

    def create_cap_region_window(self):
        """캡처 영역 창을 생성만 하고 보이지 않게 함"""
        if not self.cap_region_window:
            self.cap_region_window = CapRegionWindow(self.main_window)
            self.cap_region_window.window_closed.connect(lambda: self.toggle_modaless_button.setText("캡쳐영역 보이기"))
            
            # 저장된 투명도 적용
            opacity = self.getOpacity() / 100.0
            self.cap_region_window.setWindowOpacity(opacity)
            
            # 저장된 캡처 영역 창 설정 불러오기
            cap_region_geometry = self.settings.value('CapRegionWindow/geometry')
            if cap_region_geometry:
                self.cap_region_window.restoreGeometry(cap_region_geometry)
            else:
                # 기본 위치와 크기 설정
                self.cap_region_window.setGeometry(300, 300, 400, 300)

    def show_cap_region_window(self):
        """캡처 영역 창을 생성하고 보이게 함"""
        if not self.cap_region_window:
            self.create_cap_region_window()
        self.cap_region_window.show()

    def hide_cap_region_window(self):
        """캡처 영역 창을 숨김"""
        if self.cap_region_window is not None:
            self.cap_region_window.hide()

    def toggle_cap_region_window(self):
        """캡처 영역 창 토글"""
        if not self.cap_region_window:
            self.create_cap_region_window()
            
        if self.cap_region_window.isVisible():
            self.hide_cap_region_window()
            self.toggle_modaless_button.setText("캡쳐영역 보이기")
        else:
            self.show_cap_region_window()
            self.toggle_modaless_button.setText("캡쳐영역 숨기기")

    def clear_rectangles(self):
        """캡처 영역 창의 사각형을 초기화"""
        if self.cap_region_window is not None:
            self.cap_region_window.cap_region_rect = None
            self.cap_region_window.can_draw = True
            self.cap_region_window.update()

    def change_opacity(self, value: int) -> None:
        """캡처 영역 창의 투명도를 변경"""
        if self.cap_region_window is not None:
            opacity = value / 100.0
            self.cap_region_window.setWindowOpacity(opacity)

    def on_left_first_changed(self, state):
        """좌측부터 스위치 상태가 변경되면 호출되는 메서드"""
        is_checked = bool(state)
        self.settings.setValue('basic/left_first', is_checked)
        print(f"좌측부터 설정이 변경되었습니다: {is_checked}")

    def on_start_button_clicked(self):
        """시작 버튼 클릭 시 호출되는 메서드"""
        if self.btn_start.text() == "시작":
            self.start_process()
            self.set_start_button_text("중지")
        else:
            self.stop_process()
            self.set_start_button_text("시작")

    def set_start_button_text(self, text: str) -> None:
        """시작 버튼의 텍스트를 설정"""
        self.btn_start.setText(text)

    def reset_start_button(self):
        """시작 버튼을 초기 상태로 되돌립니다."""
        self.set_start_button_text("시작")

    def start_process(self):
        """캡쳐 프로세스를 시작합니다."""
        if not self.cap_region_window or not self.cap_region_window.get_absolute_rect():
            self.log_text_edit.append("캡쳐 영역이 설정되어 있지 않습니다.")
            return

        # 이전 스레드가 실행 중인지 확인
        try:
            if hasattr(self, 'thread') and self.thread and self.thread.isRunning():
                self.log_text_edit.append("이미 캡쳐 프로세스가 실행 중입니다.")
                return
        except RuntimeError:
            # 스레드 객체가 삭제된 경우
            self.thread = None
            self.worker = None

        # 캡쳐 영역이 설정되어 있으면 프로세스 시작
        self.log_text_edit.append("캡쳐 프로세스를 시작합니다...")
        
        # 캡쳐 영역 절대좌표 가져오기
        rect = self.cap_region_window.get_absolute_rect()
        if not rect:
            self.log_text_edit.append("캡쳐 영역이 설정되어 있지 않습니다.")
            return
            
        margins = self.getMargins()
        
        # 워커 스레드 생성 및 시작
        self.thread = QThread()
        self.worker = WorkerCapture(
            main_window=self.main_window,
            file_name=self.file_name_edit.text(),
            page_loop=int(self.page_loop_edit.text() or '0'),
            x1=rect.x(),
            y1=rect.y(),
            x2=rect.x() + rect.width(),
            y2=rect.y() + rect.height(),
            margin=margins,
            diff_width=int(self.diff_width_edit.text() or '0'),
            automation_delay=float(self.delay_edit.text() or '0'),
            left_first=self.left_first_check.isChecked()
        )
        self.worker.moveToThread(self.thread)
        
        # 시그널 연결
        self.thread.started.connect(self.worker.run)
        self.worker.finished.connect(self.thread.quit)
        self.worker.finished.connect(self.reset_start_button)  # 스레드 종료 시 버튼 초기화
        self.worker.log_message_signal.connect(self.log_text_edit.append)
        
        # 스레드 시작
        self.thread.start()

    def stop_process(self):
        """캡쳐 프로세스를 중지합니다."""
        if self.worker:
            self.worker.stop()
            self.log_text_edit.append("캡쳐 프로세스를 중지합니다...")

    def _on_filename_changed(self, text: str):
        """파일명이 변경될 때 호출되는 메서드"""
        # 타이머 재시작
        self._filename_timer.start()
        
    def _emit_filename_changed(self):
        """타이머가 만료되면 현재 파일명으로 시그널 발생"""
        current_filename = self.file_name_edit.text()
        self.filename_changed.emit(current_filename)

    def setOpacity(self, value: int) -> None:
        """투명도 값을 설정하고 라벨을 업데이트"""
        self.opacity_slider.setValue(value)
        self.opacity_label.setText(f'투명도: {value}%')
        
        # 캡처 영역 창의 투명도도 함께 업데이트
        if self.cap_region_window is not None:
            opacity = value / 100.0
            self.cap_region_window.setWindowOpacity(opacity)

    def _on_opacity_changed(self, value: int) -> None:
        """투명도 슬라이더 값이 변경될 때 호출되는 메서드"""
        self.setOpacity(value)

    def getOpacity(self) -> int:
        """현재 투명도 값 반환"""
        return self.opacity_slider.value()

    def getMargins(self) -> dict[str, int]:
        """현재 margin 값들을 반환
        
        Returns:
            dict[str, int]: margin 값들을 담은 딕셔너리
                - top: 상단 여백
                - bottom: 하단 여백
                - right: 우측 여백
                - left: 좌측 여백
        """
        return {
            "top": int(self.margin_top_edit.text() or '0'),
            "right": int(self.margin_right_edit.text() or '0'),
            "bottom": int(self.margin_bottom_edit.text() or '0'),
            "left": int(self.margin_left_edit.text() or '0')
        }

    def on_margin_changed(self):
        """Margin 값이 변경될 때 캡처 영역 창 업데이트"""
        if self.cap_region_window:
            self.cap_region_window.update()

    def loadSettings(self):
        """저장된 설정 불러오기"""
        self.margin_top_edit.setText(self.settings.value('MainWindow/margin_top', '0'))
        self.margin_right_edit.setText(self.settings.value('MainWindow/margin_right', '0'))
        self.margin_bottom_edit.setText(self.settings.value('MainWindow/margin_bottom', '0'))
        self.margin_left_edit.setText(self.settings.value('MainWindow/margin_left', '0'))
        
        self.diff_width_edit.setText(self.settings.value('MainWindow/diff_width', '0'))
        
        # 투명도 슬라이더 값 불러오기
        opacity = int(self.settings.value('MainWindow/opacity', 50))
        self.setOpacity(opacity)
        
        # 기타설정값 불러오기
        self.file_name_edit.setText(self.settings.value('MainWindow/file_name', ''))
        self.page_loop_edit.setText(self.settings.value('MainWindow/page_loop', ''))
        self.delay_edit.setText(self.settings.value('MainWindow/capture_delay', '0'))
        
    def saveSettings(self):
        """현재 설정 저장"""
        self.settings.setValue('MainWindow/margin_top', self.margin_top_edit.text())
        self.settings.setValue('MainWindow/margin_right', self.margin_right_edit.text())
        self.settings.setValue('MainWindow/margin_bottom', self.margin_bottom_edit.text())
        self.settings.setValue('MainWindow/margin_left', self.margin_left_edit.text())
        
        self.settings.setValue('MainWindow/diff_width', self.diff_width_edit.text())
        self.settings.setValue('MainWindow/opacity', self.opacity_slider.value())
        self.settings.setValue('MainWindow/file_name', self.file_name_edit.text())
        self.settings.setValue('MainWindow/page_loop', self.page_loop_edit.text())
        self.settings.setValue('MainWindow/capture_delay', self.delay_edit.text())
        
        # 캡처 영역 창 설정 저장
        if self.cap_region_window:
            self.settings.setValue('CapRegionWindow/geometry', 
                                 self.cap_region_window.saveGeometry())
        
    def getMargin(self) -> str:
        """현재 margin 값 반환"""
        return self.margin_edit.text()
        
    def getDiffWidth(self) -> str:
        """현재 diff_width 값 반환"""
        return self.diff_width_edit.text()
        
    def getFileName(self) -> str:
        """현재 파일명 반환"""
        return self.file_name_edit.text()
        
    def getPageLoop(self) -> str:
        """현재 page_loop 값 반환"""
        return self.page_loop_edit.text()
        
    def getDelay(self) -> str:
        """현재 delay 값 반환"""
        return self.delay_edit.text()

    def setup_ui(self):
        basic_layout = QVBoxLayout(self)

        # 투명도 슬라이더
        slider_layout = QHBoxLayout()
        self.opacity_label = QLabel('투명도: 50%', self)
        self.opacity_label.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)
        self.opacity_slider = QSlider(Qt.Orientation.Horizontal, self)
        self.opacity_slider.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.opacity_slider.setRange(0, 70)
        self.opacity_slider.setValue(50)
        self.opacity_slider.valueChanged.connect(self._on_opacity_changed)
        
        slider_layout.addWidget(self.opacity_label)
        slider_layout.addWidget(self.opacity_slider)
        basic_layout.addLayout(slider_layout)

        # 캡처 영역 가이드 토글 버튼
        self.toggle_modaless_button = QPushButton('캡쳐영역 보이기', self)
        self.toggle_modaless_button.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)
        self.toggle_modaless_button.clicked.connect(self.toggle_cap_region_window)
        basic_layout.addWidget(self.toggle_modaless_button)
        
        # 캡처 영역 재설정 버튼
        clear_button = QPushButton('캡쳐영역 재설정', self)
        clear_button.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)
        clear_button.clicked.connect(self.clear_rectangles)
        basic_layout.addWidget(clear_button)        
        basic_layout.addSpacing(15)

        # 캡쳐영역 설정값 그룹
        cap_region_group = QGroupBox('캡쳐영역 설정값', self)
        cap_region_group.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)
        cap_region_layout = QVBoxLayout()
        
        # margins Grid Layout
        margins_layout = QGridLayout()
        margins_layout.setSpacing(10)
        
        # Top margin
        margin_top_label = QLabel('상단 여백', self)
        margin_top_label.setToolTip('캡쳐 영역의 상단 여백 크기(px)')
        self.margin_top_edit = QLineEdit(self)
        self.margin_top_edit.setPlaceholderText('0')
        self.margin_top_edit.textChanged.connect(self.on_margin_changed)
        margins_layout.addWidget(margin_top_label, 0, 0)
        margins_layout.addWidget(self.margin_top_edit, 0, 1)
        
        # Bottom margin
        margin_bottom_label = QLabel('하단 여백', self)
        margin_bottom_label.setToolTip('캡쳐 영역의 하단 여백 크기(px)')
        self.margin_bottom_edit = QLineEdit(self)
        self.margin_bottom_edit.setPlaceholderText('0')
        self.margin_bottom_edit.textChanged.connect(self.on_margin_changed)
        margins_layout.addWidget(margin_bottom_label, 1, 0)
        margins_layout.addWidget(self.margin_bottom_edit, 1, 1)
        
        # Left margin
        margin_left_label = QLabel('좌측 여백', self)
        margin_left_label.setToolTip('캡쳐 영역의 좌측 여백 크기(px)')
        self.margin_left_edit = QLineEdit(self)
        self.margin_left_edit.setPlaceholderText('0')
        self.margin_left_edit.textChanged.connect(self.on_margin_changed)
        margins_layout.addWidget(margin_left_label, 0, 2)
        margins_layout.addWidget(self.margin_left_edit, 0, 3)
        
        # Right margin
        margin_right_label = QLabel('우측 여백', self)
        margin_right_label.setToolTip('캡쳐 영역의 우측 여백 크기(px)')
        self.margin_right_edit = QLineEdit(self)
        self.margin_right_edit.setPlaceholderText('0')
        self.margin_right_edit.textChanged.connect(self.on_margin_changed)
        margins_layout.addWidget(margin_right_label, 1, 2)
        margins_layout.addWidget(self.margin_right_edit, 1, 3)
        
        cap_region_layout.addLayout(margins_layout)
        
        # diff_width LineEdit
        diff_width_layout = QHBoxLayout()
        diff_width_label = QLabel('Diff Width', self)
        diff_width_label.setToolTip('좌우 캡쳐 영역의 차이값(px)')
        self.diff_width_edit = QLineEdit(self)
        self.diff_width_edit.setPlaceholderText('0')
        self.diff_width_edit.textChanged.connect(self.on_margin_changed)
        diff_width_layout.addWidget(diff_width_label)
        diff_width_layout.addWidget(self.diff_width_edit)
        cap_region_layout.addLayout(diff_width_layout)
        
        cap_region_group.setLayout(cap_region_layout)
        basic_layout.addWidget(cap_region_group)
        basic_layout.addSpacing(15)

        # 기타 설정값 그룹
        param_group = QGroupBox('기타 설정값', self)
        param_group.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)
        param_layout = QVBoxLayout()

        # file_name LineEdit
        name_layout = QHBoxLayout()
        name_label = QLabel('File Name', self)
        name_label.setToolTip('생성될 pdf 파일명\n예) 실전에서 바로쓰는 훈민정음 (세종 저) - 조선출판')
        self.file_name_edit = QLineEdit(self)
        # 파일명이 변경될 때 시그널 발생
        self.file_name_edit.textChanged.connect(self._on_filename_changed)
        name_layout.addWidget(name_label)
        name_layout.addWidget(self.file_name_edit)
        param_layout.addLayout(name_layout)

        # page_loop LineEdit
        loop_layout = QHBoxLayout()
        loop_label = QLabel('Page Loop', self)
        loop_label.setToolTip('반복할 페이지 수')
        self.page_loop_edit = QLineEdit(self)
        self.page_loop_edit.setPlaceholderText('0')
        loop_layout.addWidget(loop_label)
        loop_layout.addWidget(self.page_loop_edit)
        param_layout.addLayout(loop_layout)

        # delay LineEdit
        delay_layout = QHBoxLayout()
        delay_label = QLabel('Delay', self)
        delay_label.setToolTip('캡쳐 사이 딜레이(초)')
        self.delay_edit = QLineEdit(self)
        self.delay_edit.setPlaceholderText('0')
        delay_layout.addWidget(delay_label)
        delay_layout.addWidget(self.delay_edit)
        param_layout.addLayout(delay_layout)

        # 좌측부터 체크박스
        self.left_first_check = QCheckBox('좌측부터', self)
        self.left_first_check.setToolTip('체크하면 좌측 페이지부터 캡쳐')
        self.left_first_check.stateChanged.connect(self.on_left_first_changed)
        param_layout.addWidget(self.left_first_check)

        param_group.setLayout(param_layout)
        basic_layout.addWidget(param_group)
        basic_layout.addSpacing(10)

        # 시작/중지 버튼
        self.btn_start = QPushButton("시작", self)
        self.btn_start.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)
        self.btn_start.clicked.connect(self.on_start_button_clicked)
        basic_layout.addWidget(self.btn_start)

        # 로그 표시를 위한 QTextEdit
        self.log_text_edit = QTextEdit(self)
        self.log_text_edit.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.log_text_edit.setReadOnly(True)
        self.log_text_edit.setMinimumHeight(200)
        basic_layout.addWidget(self.log_text_edit)

# end of file