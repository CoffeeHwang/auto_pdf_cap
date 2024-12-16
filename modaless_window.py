from PyQt5.QtWidgets import (QApplication, QMainWindow, QPushButton, QWidget, 
                           QVBoxLayout, QSlider, QLabel, QHBoxLayout, QLineEdit, QSpinBox, QGroupBox, QTextEdit, QTabWidget)
from PyQt5.QtCore import Qt, QRect, QPoint, QSettings, QTimer, QObject, pyqtSignal, QThread
from PyQt5.QtGui import QPainter, QPen, QColor, QCursor


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
        
        print(self.parent(), " ||| ", self.main_window)
        
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
        if isinstance(self.parent(), self.main_window.__class__):
            self.parent().saveSettings() # type: ignore
        event.accept()