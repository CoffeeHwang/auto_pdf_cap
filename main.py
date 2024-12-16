from PyQt5.QtWidgets import (QApplication, QMainWindow, QPushButton, QWidget, 
                           QVBoxLayout, QSlider, QLabel, QHBoxLayout, QLineEdit, QSpinBox, QGroupBox, QTextEdit, QTabWidget)
from PyQt5.QtCore import Qt, QRect, QPoint, QSettings, QTimer, QObject, pyqtSignal, QThread
from PyQt5.QtGui import QPainter, QPen, QColor, QCursor
import sys
from auto_pdf_capture import *
from supa_common import *

class ModalessWindow(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent, Qt.Window | Qt.WindowStaysOnTopHint) # type: ignore
        self.initUI()
        self.begin = None
        self.end = None
        self.is_drawing = False
        self.is_moving = False
        self.is_resizing = False
        self.resize_position = None
        self.rectangle = None
        self.can_draw = True
        self.drag_start_pos = None
        self.rect_start = None
        self.corner_size = 10
        self.main_window = parent
        self.min_size = 100
        
    def initUI(self):
        self.setWindowTitle('캡쳐영역 가이드')
        self.setMouseTracking(True)
        
    def paintEvent(self, event):
        painter = QPainter(self)
        
        if self.rectangle is not None:  # None 체크 추가
            # 기존 흰색 사각형 그리기
            painter.setPen(QPen(QColor(255, 255, 255), 2))
            painter.drawRect(self.rectangle)
            
            # Margin이 설정된 경우 녹색 사각형 그리기
            if self.main_window and self.main_window.margin_edit.text():
                try:
                    margin = int(self.main_window.margin_edit.text())
                    if margin > 0:
                        painter.setPen(QPen(QColor(0, 255, 0), 1))
                        margin_rect = QRect(
                            self.rectangle.x() - margin,
                            self.rectangle.y() - margin,
                            self.rectangle.width() + (margin * 2),
                            self.rectangle.height() + (margin * 2)
                        )
                        painter.drawRect(margin_rect)
                except ValueError:
                    pass  # 숫자가 아닌 값이 입력된 경우 무시
            
            # Diff Width가 설정된 경우 수직 점선 그리기
            if self.main_window and self.main_window.diff_width_edit.text():
                try:
                    diff_width = int(self.main_window.diff_width_edit.text())
                    if diff_width > 0:
                        # 점선 스타일 설정
                        pen = QPen(QColor(255, 255, 255), 1)  # 흰색, 1픽 두께
                        pen.setStyle(Qt.PenStyle.DashLine)  # 점선 스타일
                        painter.setPen(pen)
                        
                        # 시작점: 왼쪽 변에서 diff_width 만큼 떨어진 x좌표
                        x = self.rectangle.left() + diff_width
                        
                        # 사각형 내부에 수직선 그리기
                        if x <= self.rectangle.right():  # 사각형 내부에 있을 때만 그리기
                            painter.drawLine(x, self.rectangle.top(), 
                                          x, self.rectangle.bottom())
                        
                except ValueError:
                    pass
            
        if self.begin and self.end and self.is_drawing:
            painter.setPen(QPen(QColor(255, 255, 255), 2))
            rect = QRect(self.begin, self.end)
            painter.drawRect(rect)
    
    def get_edge_or_corner_at(self, pos):
        if self.rectangle is None:
            return None
            
        # 모서리 영역 정의
        corners = {
            'top_left': QRect(self.rectangle.topLeft(), QPoint(
                self.rectangle.topLeft().x() + self.corner_size,
                self.rectangle.topLeft().y() + self.corner_size)),
            'top_right': QRect(
                QPoint(self.rectangle.topRight().x() - self.corner_size, self.rectangle.topRight().y()),
                QPoint(self.rectangle.topRight().x(), self.rectangle.topRight().y() + self.corner_size)),
            'bottom_left': QRect(
                QPoint(self.rectangle.bottomLeft().x(), self.rectangle.bottomLeft().y() - self.corner_size),
                QPoint(self.rectangle.bottomLeft().x() + self.corner_size, self.rectangle.bottomLeft().y())),
            'bottom_right': QRect(
                QPoint(self.rectangle.bottomRight().x() - self.corner_size, 
                      self.rectangle.bottomRight().y() - self.corner_size),
                self.rectangle.bottomRight())
        }
        
        # 변 영역 정의
        edges = {
            'top': QRect(
                QPoint(self.rectangle.left() + self.corner_size, self.rectangle.top()),
                QPoint(self.rectangle.right() - self.corner_size, self.rectangle.top() + self.corner_size)),
            'bottom': QRect(
                QPoint(self.rectangle.left() + self.corner_size, self.rectangle.bottom() - self.corner_size),
                QPoint(self.rectangle.right() - self.corner_size, self.rectangle.bottom())),
            'left': QRect(
                QPoint(self.rectangle.left(), self.rectangle.top() + self.corner_size),
                QPoint(self.rectangle.left() + self.corner_size, self.rectangle.bottom() - self.corner_size)),
            'right': QRect(
                QPoint(self.rectangle.right() - self.corner_size, self.rectangle.top() + self.corner_size),
                QPoint(self.rectangle.right(), self.rectangle.bottom() - self.corner_size))
        }
        
        # 모서리 확인
        for corner, rect in corners.items():
            if rect.contains(pos):
                return corner
                
        # 변 확인
        for edge, rect in edges.items():
            if rect.contains(pos):
                return edge
                
        return None

    def get_cursor_for_position(self, position):
        if position in ['top_left', 'bottom_right']:
            return Qt.CursorShape.SizeFDiagCursor
        elif position in ['top_right', 'bottom_left']:
            return Qt.CursorShape.SizeBDiagCursor
        elif position in ['left', 'right']:
            return Qt.CursorShape.SizeHorCursor
        elif position in ['top', 'bottom']:
            return Qt.CursorShape.SizeVerCursor
        return Qt.CursorShape.ArrowCursor

    def mouseMoveEvent(self, event):
        if self.is_drawing and self.can_draw:
            self.end = event.pos()
            if self.begin and self.end:
                temp_rect = QRect(self.begin, self.end).normalized()
                if temp_rect.width() >= self.min_size and temp_rect.height() >= self.min_size:
                    absolute_rect = self.get_absolute_coordinates(temp_rect)
                    if self.main_window and absolute_rect is not None:
                        self.main_window.x1_spin.setValue(absolute_rect.left())
                        self.main_window.y1_spin.setValue(absolute_rect.top())
                        self.main_window.x2_spin.setValue(absolute_rect.right())
                        self.main_window.y2_spin.setValue(absolute_rect.bottom())
            self.update()
        elif self.is_moving and self.rectangle and self.rect_start: # type: ignore
            delta = event.pos() - self.drag_start_pos
            self.rectangle = QRect(self.rect_start)
            self.rectangle.translate(delta)
            self.update_parent_coordinates()
            self.update()
        elif self.is_resizing and self.rectangle and self.rect_start: # type: ignore
            new_rect = QRect(self.rectangle)
            
            if self.resize_position == 'top_left':
                new_rect = QRect(event.pos(), self.rect_start.bottomRight())
            elif self.resize_position == 'top_right':
                new_rect = QRect(
                    QPoint(self.rect_start.left(), event.pos().y()),
                    QPoint(event.pos().x(), self.rect_start.bottom())
                )
            elif self.resize_position == 'bottom_left':
                new_rect = QRect(
                    QPoint(event.pos().x(), self.rect_start.top()),
                    QPoint(self.rect_start.right(), event.pos().y())
                )
            elif self.resize_position == 'bottom_right':
                new_rect = QRect(
                    self.rect_start.topLeft(),
                    event.pos()
                )
            elif self.resize_position == 'top':
                new_rect = QRect(
                    QPoint(self.rect_start.left(), event.pos().y()),
                    self.rect_start.bottomRight()
                )
            elif self.resize_position == 'bottom':
                new_rect = QRect(
                    self.rect_start.topLeft(),
                    QPoint(self.rect_start.right(), event.pos().y())
                )
            elif self.resize_position == 'left':
                new_rect = QRect(
                    QPoint(event.pos().x(), self.rect_start.top()),
                    self.rect_start.bottomRight()
                )
            elif self.resize_position == 'right':
                new_rect = QRect(
                    self.rect_start.topLeft(),
                    QPoint(event.pos().x(), self.rect_start.bottom())
                )
            
            new_rect = self.ensure_minimum_size(new_rect.normalized())
            self.rectangle = new_rect
            
            self.update_parent_coordinates()
            self.update()
        else:
            # 마우스 커서 업데이트
            position = self.get_edge_or_corner_at(event.pos())
            if position:
                self.setCursor(self.get_cursor_for_position(position))
            elif self.rectangle and self.rectangle.contains(event.pos()): # type: ignore
                self.setCursor(Qt.CursorShape.SizeAllCursor)
            else:
                self.setCursor(Qt.CursorShape.ArrowCursor)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            position = self.get_edge_or_corner_at(event.pos())
            if position and self.rectangle: # type: ignore
                self.is_resizing = True
                self.resize_position = position
                self.drag_start_pos = event.pos()
                self.rect_start = QRect(self.rectangle)  # 현재 사각형 상태 저장
            elif self.can_draw:
                self.begin = event.pos()
                self.end = self.begin
                self.is_drawing = True
            elif self.rectangle and self.rectangle.contains(event.pos()): # type: ignore
                self.is_moving = True
                self.drag_start_pos = event.pos()
                self.rect_start = QRect(self.rectangle)  # QPoint 대신 QRect로 저장

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            if self.is_drawing and self.can_draw:
                self.is_drawing = False
                if self.begin and self.end:
                    temp_rect = QRect(self.begin, self.end).normalized()
                    if temp_rect.width() >= self.min_size and temp_rect.height() >= self.min_size:
                        self.rectangle = temp_rect
                        self.begin = None
                        self.end = None
                        self.can_draw = False
                        self.update_parent_coordinates()
                    else:
                        self.begin = None
                        self.end = None
            self.is_moving = False
            self.is_resizing = False
            self.resize_position = None
            self.update()

    def update_parent_coordinates(self):
        if self.main_window and self.rectangle: # type: ignore
            absolute_rect = self.get_absolute_coordinates(self.rectangle)
            if absolute_rect: # type: ignore
                # SpinBox 업데이트
                self.main_window.x1_spin.blockSignals(True)
                self.main_window.y1_spin.blockSignals(True)
                self.main_window.x2_spin.blockSignals(True)
                self.main_window.y2_spin.blockSignals(True)
                
                try:
                    # 뷰포트 기준 좌표 업데이트
                    self.main_window.x1_spin.setValue(absolute_rect.left())
                    self.main_window.y1_spin.setValue(absolute_rect.top())
                    self.main_window.x2_spin.setValue(absolute_rect.right())
                    self.main_window.y2_spin.setValue(absolute_rect.bottom())
                    
                finally:
                    # 모든 시그널 언블록
                    self.main_window.x1_spin.blockSignals(False)
                    self.main_window.y1_spin.blockSignals(False)
                    self.main_window.x2_spin.blockSignals(False)
                    self.main_window.y2_spin.blockSignals(False)

    def get_absolute_coordinates(self, rect):
        if not rect:
            return None
            
        # 윈도우의 절대 위치 얻기
        window_pos = self.mapToGlobal(QPoint(0, 0))
        
        # 사각형의 상대 좌표를 절대 좌표로 변환
        absolute_rect = QRect(
            window_pos.x() + rect.left(),
            window_pos.y() + rect.top(),
            rect.width(),
            rect.height()
        )
        return absolute_rect

    def moveEvent(self, event):
        # 창이 이동할 때마다 좌표 업데이트
        super().moveEvent(event)
        self.update_parent_coordinates()

    def ensure_minimum_size(self, new_rect):
        """사각형이 최소 크기 이상을 유지하도록 보장"""
        if new_rect.width() < self.min_size:
            if self.resize_position in ['left', 'top_left', 'bottom_left']:
                new_rect.setLeft(new_rect.right() - self.min_size)
            else:
                new_rect.setRight(new_rect.left() + self.min_size)
                
        if new_rect.height() < self.min_size:
            if self.resize_position in ['top', 'top_left', 'top_right']:
                new_rect.setTop(new_rect.bottom() - self.min_size)
            else:
                new_rect.setBottom(new_rect.top() + self.min_size)
                
        return new_rect

    def closeEvent(self, event):
        """모달리스 창이 닫힐 때 설정 저장"""
        if isinstance(self.parent(), MainWindow):
            self.parent().saveSettings() # type: ignore
        event.accept()

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
        self.worker = Worker(self,
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

class Worker(QObject):
    finished = pyqtSignal()
    log_message_signal  = pyqtSignal(str)  # 로그 메시지를 전달할 신호 추가

    def __init__(self, main_window, file_name, page_loop, x1, y1, x2, y2, margin, diff_width, automation_delay):
        super().__init__()
        self.main_window = main_window
        self.file_name = file_name
        self.page_loop = page_loop
        self.x1 = x1
        self.y1 = y1
        self.x2 = x2
        self.y2 = y2
        self.margin = margin
        self.diff_width = diff_width
        self.automation_delay = automation_delay

        # 로그 메시지 신호를 메인 윈도우의 log_message 슬롯에 연결
        self.log_message_signal.connect(self.main_window.log_message)

    def run(self):
        auto_pdf_capture(
            file_name=self.file_name,
            page_loop=self.page_loop,
            x1=self.x1,
            y1=self.y1,
            x2=self.x2,
            y2=self.y2,
            margin=self.margin,
            diff_width=self.diff_width,
            res=1,
            automation_delay=self.automation_delay,
            log_message_signal=self.log_message_signal   # type: ignore
        )
        self.finished.emit()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    main_window = MainWindow()
    main_window.show()
    sys.exit(app.exec_())

# end of file