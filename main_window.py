from PyQt5.QtWidgets import (QMainWindow, QPushButton, QWidget, 
                           QVBoxLayout, QSlider, QLabel, QHBoxLayout, QLineEdit, QSpinBox, QGroupBox, QTextEdit, QTabWidget)
from PyQt5.QtCore import Qt, QRect, QPoint, QSettings, QThread
from modaless_window import ModalessWindow
from worker_cap import WorkerCapture


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.settings = QSettings('MyCompany', 'RectangleApp')  # 설정 객체 생성
        self.modaless_window = None
        self.initUI()
        self.show_modaless()  # 시작 시 모달리스 창 자동 생성
        self.loadSettings()   # 설정 불러오기
        
    def initUI(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        
        # 투명도 슬라이더
        slider_layout = QHBoxLayout()
        self.opacity_label = QLabel('투명도: 50%', self)
        self.opacity_slider = QSlider(Qt.Orientation.Horizontal, self)
        self.opacity_slider.setRange(0, 70)
        self.opacity_slider.setValue(50)
        self.opacity_slider.valueChanged.connect(self.change_opacity)
        
        slider_layout.addWidget(self.opacity_label)
        slider_layout.addWidget(self.opacity_slider)
        layout.addLayout(slider_layout)

        # 모달리스 창 보이기/숨기기 토글 버튼
        self.toggle_modaless_button = QPushButton('캡쳐영역 가이드', self)
        self.toggle_modaless_button.clicked.connect(self.toggle_modaless)
        layout.addWidget(self.toggle_modaless_button)
        
        clear_button = QPushButton('캡쳐영역 재설정', self)
        clear_button.clicked.connect(self.clear_rectangles)
        layout.addWidget(clear_button)        
        layout.addSpacing(15)

        # 파라미터 그룹
        param_group = QGroupBox("기타 설정값")
        param_layout = QHBoxLayout()
        
        # margin LineEdit
        margin_layout = QVBoxLayout()
        margin_label = QLabel('Margin', self)
        margin_label.setToolTip('사각형의 여백을 설정하여 실제 캡쳐 영역을 확장합니다.')
        self.margin_edit = QLineEdit(self)
        self.margin_edit.setText('0')
        self.margin_edit.textChanged.connect(self.on_margin_changed)
        margin_layout.addWidget(margin_label)
        margin_layout.addWidget(self.margin_edit)
        
        # diff_width LineEdit
        diff_width_layout = QVBoxLayout()
        diff_width_label = QLabel('Diff Width', self)
        diff_width_label.setToolTip('좌우페이지 여백 차이를 보정하여 캡쳐하기 위한 값')
        self.diff_width_edit = QLineEdit(self)
        self.diff_width_edit.setText('0')
        self.diff_width_edit.textChanged.connect(self.on_diff_width_changed)
        diff_width_layout.addWidget(diff_width_label)
        diff_width_layout.addWidget(self.diff_width_edit)

        # page_loop LineEdit 추가
        page_loop_layout = QVBoxLayout()
        page_loop_label = QLabel('Page Loop', self)
        page_loop_label.setToolTip('캡쳐 반복 횟수 (캡쳐 페이지수)')
        self.page_loop_edit = QLineEdit(self)
        page_loop_layout.addWidget(page_loop_label)
        page_loop_layout.addWidget(self.page_loop_edit)

        # delay LineEdit 추가
        delay_layout = QVBoxLayout()
        delay_label = QLabel('Delay (1/1000sec)', self)
        delay_label.setToolTip('각 페이지 캡쳐 사이의 지연 시간 (1/1000초 단위)')
        self.delay_edit = QLineEdit(self)
        self.delay_edit.setText('0.2')  # 기본값 설정
        delay_layout.addWidget(delay_label)
        delay_layout.addWidget(self.delay_edit)

        # 파라미터 레이아웃에 추가
        param_layout.addLayout(margin_layout)
        param_layout.addLayout(diff_width_layout)
        param_layout.addLayout(page_loop_layout)
        param_layout.addLayout(delay_layout)  # delay 추가
        param_group.setLayout(param_layout)
        
        # 뷰포트 기준 좌표 그룹
        coord_group = QGroupBox("캡쳐영역 좌표 설정")
        coord_layout = QHBoxLayout()
        
        x1_layout = QVBoxLayout()
        x1_label = QLabel('X1:', self)
        self.x1_spin = QSpinBox(self)
        self.x1_spin.setRange(0, 9999)
        self.x1_spin.valueChanged.connect(self.on_coordinate_changed)
        x1_layout.addWidget(x1_label)
        x1_layout.addWidget(self.x1_spin)
        
        y1_layout = QVBoxLayout()
        y1_label = QLabel('Y1:', self)
        self.y1_spin = QSpinBox(self)
        self.y1_spin.setRange(0, 9999)
        self.y1_spin.valueChanged.connect(self.on_coordinate_changed)
        y1_layout.addWidget(y1_label)
        y1_layout.addWidget(self.y1_spin)
        
        x2_layout = QVBoxLayout()
        x2_label = QLabel('X2:', self)
        self.x2_spin = QSpinBox(self)
        self.x2_spin.setRange(0, 9999)
        self.x2_spin.valueChanged.connect(self.on_coordinate_changed)
        x2_layout.addWidget(x2_label)
        x2_layout.addWidget(self.x2_spin)
        
        y2_layout = QVBoxLayout()
        y2_label = QLabel('Y2:', self)
        self.y2_spin = QSpinBox(self)
        self.y2_spin.setRange(0, 9999)
        self.y2_spin.valueChanged.connect(self.on_coordinate_changed)
        y2_layout.addWidget(y2_label)
        y2_layout.addWidget(self.y2_spin)
        
        coord_layout.addLayout(x1_layout)
        coord_layout.addLayout(y1_layout)
        coord_layout.addLayout(x2_layout)
        coord_layout.addLayout(y2_layout)
        coord_group.setLayout(coord_layout)
        
        # 메인 레이아웃에 그룹 추가
        layout.addWidget(coord_group)
        layout.addSpacing(10)
        layout.addWidget(param_group)
        layout.addSpacing(10)
        
        # file_name LineEdit
        file_name_layout = QVBoxLayout()
        file_name_label = QLabel('File Name:', self)
        file_name_label.setToolTip('캡쳐될 pdf 파일명 | 형식 : "책이름(저자등) - 출판사"')
        self.file_name_edit = QLineEdit(self)
        file_name_layout.addWidget(file_name_label)
        file_name_layout.addWidget(self.file_name_edit)

        # 시작 버튼
        start_button = QPushButton('시작', self)
        start_button.clicked.connect(self.start_process)  # 시작 버튼 클릭 시 호출할 함수

        # 레이아웃에 추가
        layout.addLayout(file_name_layout)
        layout.addLayout(page_loop_layout)
        layout.addWidget(start_button)

        # 로그 표시를 위한 QTextEdit 추가
        self.log_text_edit = QTextEdit(self)
        self.log_text_edit.setReadOnly(True)  # 읽기 전용 설정
        self.log_text_edit.setFixedHeight(200)  # 고정 높이 설정
        layout.addWidget(self.log_text_edit)  # 레이아웃에 추가

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
        
        self.x1_spin.setValue(x1)
        self.y1_spin.setValue(y1)
        self.x2_spin.setValue(x2)
        self.y2_spin.setValue(y2)
        
        # LineEdit 값들 불러오기
        self.margin_edit.setText(self.settings.value('MainWindow/margin', '0'))
        self.diff_width_edit.setText(self.settings.value('MainWindow/diff_width', '0'))
        
        # 투명도 슬라이더 값 불러오기
        opacity = int(self.settings.value('MainWindow/opacity', 50))
        self.opacity_slider.setValue(opacity)
        self.opacity_label.setText(f'투명도: {opacity}%')
        
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
        
        # file_name과 page_loop 값 불러오기
        self.file_name_edit.setText(self.settings.value('MainWindow/file_name', ''))
        self.page_loop_edit.setText(self.settings.value('MainWindow/page_loop', ''))

    def saveSettings(self):
        """현재 설정 저장"""
        # 창 위치/크기 저장
        self.settings.setValue('MainWindow/geometry', self.saveGeometry())
        
        # SpinBox 값들 저장
        self.settings.setValue('MainWindow/x1', self.x1_spin.value())
        self.settings.setValue('MainWindow/y1', self.y1_spin.value())
        self.settings.setValue('MainWindow/x2', self.x2_spin.value())
        self.settings.setValue('MainWindow/y2', self.y2_spin.value())
        
        # LineEdit 값들 저장
        self.settings.setValue('MainWindow/margin', self.margin_edit.text())
        self.settings.setValue('MainWindow/diff_width', self.diff_width_edit.text())
        
        # 투명도 슬라이더 값 저장
        self.settings.setValue('MainWindow/opacity', self.opacity_slider.value())
        
        # 모달리스 창 설정 저장
        if self.modaless_window:
            self.settings.setValue('ModalessWindow/geometry', 
                                 self.modaless_window.saveGeometry())
        
        # file_name과 page_loop 값 저장
        self.settings.setValue('MainWindow/file_name', self.file_name_edit.text())
        self.settings.setValue('MainWindow/page_loop', self.page_loop_edit.text())

    def closeEvent(self, event):
        """프로그램 종료 시 설정 저장"""
        self.saveSettings()
        if self.modaless_window:
            self.modaless_window.close()
        event.accept()

    def show_modaless(self):
        if self.modaless_window is None:
            self.modaless_window = ModalessWindow(parent=self)
            
            # 저장된 투명도 적용
            opacity = self.opacity_slider.value() / 100.0
            self.modaless_window.setWindowOpacity(opacity)
            
            # 저장된 모달리스 창 설정 불러오기
            modaless_geometry = self.settings.value('ModalessWindow/geometry')
            if modaless_geometry:
                self.modaless_window.restoreGeometry(modaless_geometry)
            else:
                # 기본 위치와 크기 설정
                self.modaless_window.setGeometry(300, 300, 400, 300)
        
        self.modaless_window.show()
        
    def change_opacity(self, value):
        if self.modaless_window is not None:
            opacity = value / 100.0
            self.modaless_window.setWindowOpacity(opacity)
            self.opacity_label.setText(f'투명도: {value}%')
            
    def clear_rectangles(self):
        if self.modaless_window is not None:
            self.modaless_window.rectangle = None
            self.modaless_window.can_draw = True  # 초기화 후 다시 그리기 가능 상태로 변경
            self.modaless_window.update()
            
    def on_coordinate_changed(self):
        if self.modaless_window and self.modaless_window.rectangle: # type: ignore
            # 시그널 블록
            self.x1_spin.blockSignals(True)
            self.y1_spin.blockSignals(True)
            self.x2_spin.blockSignals(True)
            self.y2_spin.blockSignals(True)

            try:
                # 절대 좌표에서 상대 좌표로 변환
                window_pos = self.modaless_window.mapToGlobal(QPoint(0, 0))
                
                # 새로운 상대 좌표 계산
                new_rect = QRect(
                    self.x1_spin.value() - window_pos.x(),
                    self.y1_spin.value() - window_pos.y(),
                    self.x2_spin.value() - self.x1_spin.value(),
                    self.y2_spin.value() - self.y1_spin.value()
                )
                
                # 사각형 업데이트
                self.modaless_window.rectangle = new_rect
                self.modaless_window.update()
            
            finally:
                # 시그널 언블록
                self.x1_spin.blockSignals(False)
                self.y1_spin.blockSignals(False)
                self.x2_spin.blockSignals(False)
                self.y2_spin.blockSignals(False)

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
            self.modaless_window = ModalessWindow(parent=self)
            self.modaless_window.setWindowOpacity(self.opacity_slider.value() / 100.0)
            self.modaless_window.show()
        else:
            if self.modaless_window.isVisible():
                self.modaless_window.hide()
            else:
                self.modaless_window.show()

    def log_message(self, message):
        """로그 메시지를 추가하는 메서드"""
        self.log_text_edit.append(message)  # 메시지를 추가
        self.log_text_edit.verticalScrollBar().setValue(self.log_text_edit.verticalScrollBar().maximum()) # type: ignore

    def start_process(self):
        self.modaless_window.hide() # type: ignore
        # QThread를 사용하여 auto_pdf_capture를 비동기로 실행
        self.thread = QThread() # type: ignore
        self.worker = WorkerCapture(self,
                             self.file_name_edit.text(), 
                             int(self.page_loop_edit.text()),
                             int(self.x1_spin.value()), 
                             int(self.y1_spin.value()),
                             int(self.x2_spin.value()), 
                             int(self.y2_spin.value()),
                             int(self.margin_edit.text()), 
                             int(self.diff_width_edit.text()),
                             float(self.delay_edit.text()))
        self.worker.moveToThread(self.thread) # type: ignore

        self.thread.started.connect(self.worker.run)
        self.worker.finished.connect(self.thread.quit)
        self.worker.finished.connect(self.worker.deleteLater)
        self.thread.finished.connect(self.thread.deleteLater)

        self.thread.start()