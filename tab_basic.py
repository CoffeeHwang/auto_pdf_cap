from PyQt5.QtWidgets import (QWidget, QPushButton, QVBoxLayout, QSlider, 
                           QLabel, QHBoxLayout, QLineEdit, QSpinBox, QGroupBox, QTextEdit,
                           QCheckBox)
from PyQt5.QtCore import Qt, pyqtSignal, QTimer
from supa_settings import SupaSettings

class BasicTab(QWidget):
    # 파일명이 변경될 때 발생하는 시그널 추가
    filename_changed = pyqtSignal(str)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.main_window = parent
        self.settings = SupaSettings()
        
        # 파일명 변경 타이머 설정
        self._filename_timer = QTimer(self)
        self._filename_timer.setInterval(2000)  # 2초 딜레이
        self._filename_timer.setSingleShot(True)  # 한 번만 실행
        self._filename_timer.timeout.connect(self._emit_filename_changed)
        
        self.setup_ui()

    def setup_ui(self):
        basic_layout = QVBoxLayout(self)

        # 투명도 슬라이더
        slider_layout = QHBoxLayout()
        self.opacity_label = QLabel('투명도: 50%', self)
        self.opacity_slider = QSlider(Qt.Orientation.Horizontal, self)
        self.opacity_slider.setRange(0, 70)
        self.opacity_slider.setValue(50)
        self.opacity_slider.valueChanged.connect(lambda: self.main_window.change_opacity(self.opacity_slider.value()))
        
        slider_layout.addWidget(self.opacity_label)
        slider_layout.addWidget(self.opacity_slider)
        basic_layout.addLayout(slider_layout)

        # 모달리스 창 보이기/숨기기 토글 버튼
        self.toggle_modaless_button = QPushButton('캡쳐영역 가이드', self)
        self.toggle_modaless_button.clicked.connect(self.main_window.toggle_modaless)
        basic_layout.addWidget(self.toggle_modaless_button)
        
        clear_button = QPushButton('캡쳐영역 재설정', self)
        clear_button.clicked.connect(self.main_window.clear_rectangles)
        basic_layout.addWidget(clear_button)        
        basic_layout.addSpacing(15)

        # 파라미터 그룹
        param_group = QGroupBox("기타 설정값")
        param_layout = QHBoxLayout()
        
        # margin LineEdit
        margin_layout = QVBoxLayout()
        margin_label = QLabel('Margin', self)
        margin_label.setToolTip('사각형의 여백을 설정하여 실제 캡쳐 영역을 확장합니다.')
        self.margin_edit = QLineEdit(self)
        self.margin_edit.setText('0')
        self.margin_edit.textChanged.connect(self.main_window.on_margin_changed)
        margin_layout.addWidget(margin_label)
        margin_layout.addWidget(self.margin_edit)
        
        # diff_width LineEdit
        diff_width_layout = QVBoxLayout()
        diff_width_label = QLabel('Diff Width', self)
        diff_width_label.setToolTip('좌우페이지 여백 차이를 보정하여 캡쳐하기 위한 값')
        self.diff_width_edit = QLineEdit(self)
        self.diff_width_edit.setText('0')
        self.diff_width_edit.textChanged.connect(self.main_window.on_diff_width_changed)
        diff_width_layout.addWidget(diff_width_label)
        diff_width_layout.addWidget(self.diff_width_edit)

        # page_loop LineEdit
        page_loop_layout = QVBoxLayout()
        page_loop_label = QLabel('Page Loop', self)
        page_loop_label.setToolTip('캡쳐 반복 횟수 (캡쳐 페이지수)')
        self.page_loop_edit = QLineEdit(self)
        page_loop_layout.addWidget(page_loop_label)
        page_loop_layout.addWidget(self.page_loop_edit)

        # delay LineEdit
        delay_layout = QVBoxLayout()
        delay_label = QLabel('Delay(초)', self)
        delay_label.setToolTip('각 페이지 캡쳐 사이의 지연 시간 (초 단위)')
        self.delay_edit = QLineEdit(self)
        self.delay_edit.setText('0.2')
        delay_layout.addWidget(delay_label)
        delay_layout.addWidget(self.delay_edit)

        # 좌측부터 스위치
        left_first_layout = QVBoxLayout()
        left_first_label = QLabel('좌측부터', self)
        left_first_label.setToolTip('캡쳐 순서를 좌측부터 시작할지 여부를 설정합니다.')
        self.left_first_check = QCheckBox(self)
        self.left_first_check.setChecked(self.settings.value('basic/left_first', True))
        self.left_first_check.stateChanged.connect(self.on_left_first_changed)
        left_first_layout.addWidget(left_first_label)
        left_first_layout.addWidget(self.left_first_check)
        
        # 파라미터 레이아웃에 추가
        param_layout.addLayout(margin_layout)
        param_layout.addLayout(diff_width_layout)
        param_layout.addLayout(page_loop_layout)
        param_layout.addLayout(delay_layout)
        param_layout.addLayout(left_first_layout)
        param_group.setLayout(param_layout)
        
        # 뷰포트 기준 좌표 그룹
        coord_group = QGroupBox("캡쳐영역 좌표 설정")
        coord_layout = QHBoxLayout()
        
        x1_layout = QVBoxLayout()
        x1_label = QLabel('X1:', self)
        self.x1_spin = QSpinBox(self)
        self.x1_spin.setRange(0, 9999)
        self.x1_spin.valueChanged.connect(self.main_window.on_coordinate_changed)
        x1_layout.addWidget(x1_label)
        x1_layout.addWidget(self.x1_spin)
        
        y1_layout = QVBoxLayout()
        y1_label = QLabel('Y1:', self)
        self.y1_spin = QSpinBox(self)
        self.y1_spin.setRange(0, 9999)
        self.y1_spin.valueChanged.connect(self.main_window.on_coordinate_changed)
        y1_layout.addWidget(y1_label)
        y1_layout.addWidget(self.y1_spin)
        
        x2_layout = QVBoxLayout()
        x2_label = QLabel('X2:', self)
        self.x2_spin = QSpinBox(self)
        self.x2_spin.setRange(0, 9999)
        self.x2_spin.valueChanged.connect(self.main_window.on_coordinate_changed)
        x2_layout.addWidget(x2_label)
        x2_layout.addWidget(self.x2_spin)
        
        y2_layout = QVBoxLayout()
        y2_label = QLabel('Y2:', self)
        self.y2_spin = QSpinBox(self)
        self.y2_spin.setRange(0, 9999)
        self.y2_spin.valueChanged.connect(self.main_window.on_coordinate_changed)
        y2_layout.addWidget(y2_label)
        y2_layout.addWidget(self.y2_spin)
        
        coord_layout.addLayout(x1_layout)
        coord_layout.addLayout(y1_layout)
        coord_layout.addLayout(x2_layout)
        coord_layout.addLayout(y2_layout)
        coord_group.setLayout(coord_layout)
        
        # 메인 레이아웃에 그룹 추가
        basic_layout.addWidget(coord_group)
        basic_layout.addSpacing(10)
        basic_layout.addWidget(param_group)
        basic_layout.addSpacing(10)
        
        # file_name LineEdit
        name_layout = QVBoxLayout()
        name_label = QLabel('File Name', self)
        name_label.setToolTip('생성될 pdf 파일명\n예) 실전에서 바로쓰는 Next.js (박수현 역) - 한빛미디어')
        self.file_name_edit = QLineEdit(self)
        # 파일명이 변경될 때 시그널 발생
        self.file_name_edit.textChanged.connect(self._on_filename_changed)
        name_layout.addWidget(name_label)
        name_layout.addWidget(self.file_name_edit)

        # 시작/중지 버튼
        self.btn_start = QPushButton("시작", self)
        self.btn_start.clicked.connect(self.on_start_button_clicked)

        # 레이아웃에 추가
        basic_layout.addLayout(name_layout)
        basic_layout.addLayout(page_loop_layout)
        basic_layout.addWidget(self.btn_start)

        # 로그 표시를 위한 QTextEdit
        self.log_text_edit = QTextEdit(self)
        self.log_text_edit.setReadOnly(True)
        self.log_text_edit.setFixedHeight(200)
        basic_layout.addWidget(self.log_text_edit)

    def on_left_first_changed(self, state):
        """좌측부터 스위치 상태가 변경되면 호출되는 메서드"""
        is_checked = bool(state)
        self.settings.setValue('basic/left_first', is_checked)
        print(f"좌측부터 설정이 변경되었습니다: {is_checked}")

    def on_start_button_clicked(self):
        """시작/중지 버튼 클릭 이벤트 핸들러"""
        if self.btn_start.text() == "시작":
            self.btn_start.setText("중지")
            self.main_window.start_process()
        else:
            self.btn_start.setText("시작")
            self.main_window.stop_process()

    def _on_filename_changed(self, text: str):
        """파일명이 변경될 때 호출되는 메서드"""
        # 타이머 재시작
        self._filename_timer.start()
        
    def _emit_filename_changed(self):
        """타이머가 만료되면 현재 파일명으로 시그널 발생"""
        current_filename = self.file_name_edit.text()
        self.filename_changed.emit(current_filename)
