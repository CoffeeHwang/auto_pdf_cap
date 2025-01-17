from PyQt5.QtWidgets import (QApplication, QMainWindow, QPushButton, QWidget, 
                           QVBoxLayout, QSlider, QLabel, QHBoxLayout, QLineEdit, QSpinBox, QGroupBox, QTextEdit, QTabWidget,
                           QDesktopWidget)
from PyQt5.QtCore import Qt, QRect, QPoint, QTimer, QObject, pyqtSignal, QThread
from PyQt5.QtGui import QPainter, QPen, QColor, QCursor
from supa_settings import SupaSettings
from supa_common import log


class CapRegionWindow(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent, Qt.Window | Qt.WindowStaysOnTopHint) # type: ignore
        self.begin = None
        self.end = None
        self.is_drawing = False
        self.is_moving = False
        self.is_resizing = False
        self.resize_position = None
        self.cap_region_rect = None
        self.can_draw = False
        self.drag_start_pos = None
        self.rect_start = None
        self.corner_size = 10
        self.main_window = parent
        self.min_size = 100
        self.initUI()
        
    def initUI(self):
        self.setWindowTitle('캡쳐영역 가이드')
        self.setMouseTracking(True)
        self.loadSettings()
        
    def paintEvent(self, event):
        """창에 사각형을 그리는 이벤트"""
        painter = QPainter(self)
        
        # 투명한 배경
        painter.fillRect(self.rect(), QColor(0, 0, 0, 1))
        
        if self.cap_region_rect is not None:
            # 흰색 사각형 그리기
            painter.setPen(QPen(QColor(255, 255, 255), 2))
            painter.drawRect(self.cap_region_rect)

            # 녹색 margin 사각형 그리기
            margins = self.main_window.basic_tab.getMargins()
            if any(margin > 0 for margin in margins.values()):
                painter.setPen(QPen(QColor(0, 255, 0), 1))
                margin_rect = QRect(
                    self.cap_region_rect.x() - margins["left"],
                    self.cap_region_rect.y() - margins["top"],
                    self.cap_region_rect.width() + margins["right"] + margins["left"],
                    self.cap_region_rect.height() + margins["top"] + margins["bottom"]
                )
                painter.drawRect(margin_rect)
            
            # Diff Width가 설정된 경우 수직 점선 그리기
            if self.main_window and self.main_window.basic_tab.diff_width_edit.text():
                try:
                    diff_width = int(self.main_window.basic_tab.diff_width_edit.text())
                    if diff_width > 0:
                        # 점선 스타일 설정
                        pen = QPen(QColor(255, 255, 255), 1)  # 흰색, 1픽 두께
                        pen.setStyle(Qt.PenStyle.DashLine)  # 점선 스타일
                        painter.setPen(pen)
                        
                        # 시작점: 왼쪽 변에서 diff_width 만큼 떨어진 x좌표
                        x = self.cap_region_rect.left() + diff_width
                        
                        # 사각형 내부에 수직선 그리기
                        if x <= self.cap_region_rect.right():  # 사각형 내부에 있을 때만 그리기
                            painter.drawLine(x, self.cap_region_rect.top(), 
                                          x, self.cap_region_rect.bottom())
                        
                except ValueError:
                    pass
            
        if self.begin and self.end and self.is_drawing:
            painter.setPen(QPen(QColor(255, 255, 255), 2))
            rect = QRect(self.begin, self.end)
            painter.drawRect(rect)
    
    def get_edge_or_corner_at(self, pos):
        if self.cap_region_rect is None:
            return None
            
        # 모서리 영역 정의
        corners = {
            'top_left': QRect(self.cap_region_rect.topLeft(), QPoint(
                self.cap_region_rect.topLeft().x() + self.corner_size,
                self.cap_region_rect.topLeft().y() + self.corner_size)),
            'top_right': QRect(
                QPoint(self.cap_region_rect.topRight().x() - self.corner_size, self.cap_region_rect.topRight().y()),
                QPoint(self.cap_region_rect.topRight().x(), self.cap_region_rect.topRight().y() + self.corner_size)),
            'bottom_left': QRect(
                QPoint(self.cap_region_rect.bottomLeft().x(), self.cap_region_rect.bottomLeft().y() - self.corner_size),
                QPoint(self.cap_region_rect.bottomLeft().x() + self.corner_size, self.cap_region_rect.bottomLeft().y())),
            'bottom_right': QRect(
                QPoint(self.cap_region_rect.bottomRight().x() - self.corner_size, 
                      self.cap_region_rect.bottomRight().y() - self.corner_size),
                self.cap_region_rect.bottomRight())
        }
        
        # 변 영역 정의
        edges = {
            'top': QRect(
                QPoint(self.cap_region_rect.left() + self.corner_size, self.cap_region_rect.top()),
                QPoint(self.cap_region_rect.right() - self.corner_size, self.cap_region_rect.top() + self.corner_size)),
            'bottom': QRect(
                QPoint(self.cap_region_rect.left() + self.corner_size, self.cap_region_rect.bottom() - self.corner_size),
                QPoint(self.cap_region_rect.right() - self.corner_size, self.cap_region_rect.bottom())),
            'left': QRect(
                QPoint(self.cap_region_rect.left(), self.cap_region_rect.top() + self.corner_size),
                QPoint(self.cap_region_rect.left() + self.corner_size, self.cap_region_rect.bottom() - self.corner_size)),
            'right': QRect(
                QPoint(self.cap_region_rect.right() - self.corner_size, self.cap_region_rect.top() + self.corner_size),
                QPoint(self.cap_region_rect.right(), self.cap_region_rect.bottom() - self.corner_size))
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
        """
        마우스가 움직일 때 호출되는 함수. 사각형을 그리고 있는 중이거나, 사각형을
        이동시키거나, 사각형을 크기 조정 중이라면 적절한 처리를 수행합니다.
        
        Parameters
        ----------
        event : QMouseEvent
            마우스 이벤트
        """
        # 마우스가 움직이는 중에 사각형을 그리고 있다면
        if self.is_drawing and self.can_draw:
            self.end = event.pos()
            # 마우스가 움직이는 중에 사각형을 그리고 있는 경우, 
            # 사각형의 크기가 최소 크기 이상이 되면 이를 저장
            if self.begin and self.end:
                temp_rect = QRect(self.begin, self.end).normalized()
                if temp_rect.width() >= self.min_size and temp_rect.height() >= self.min_size:
                    if self.cap_region_rect is not None:
                        self.save_rectangle_settings()
            self.update()
            
        # 마우스가 움직이는 중에 사각형을 이동시키고 있다면
        elif self.is_moving and self.cap_region_rect and self.rect_start: # type: ignore
            delta = event.pos() - self.drag_start_pos
            self.cap_region_rect = QRect(self.rect_start)
            self.cap_region_rect.translate(delta)
            # 마우스가 움직이는 중에 사각형을 이동시키는 경우, 
            # 사각형의 크기가 최소 크기 이상이 되면 이를 저장
            if self.cap_region_rect is not None:
                self.save_rectangle_settings()
            self.update()
            
        # 마우스가 움직이는 중에 사각형을 크기 조정하고 있다면
        elif self.is_resizing and self.cap_region_rect and self.rect_start: # type: ignore
            new_rect = QRect(self.cap_region_rect)
            
            # 크기 조정하는 경우, 크기 조정 방향에 따라 적절한 처리를 수행
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
            
            # 크기 조정하는 경우, 크기가 최소 크기 이상이 되면 이를 저장
            new_rect = self.ensure_minimum_size(new_rect.normalized())
            self.cap_region_rect = new_rect
            if self.cap_region_rect is not None:
                self.save_rectangle_settings()
            self.update()
        else:
            # 마우스 커서 업데이트
            position = self.get_edge_or_corner_at(event.pos())
            if position:
                self.setCursor(self.get_cursor_for_position(position))
            elif self.cap_region_rect and self.cap_region_rect.contains(event.pos()): # type: ignore
                self.setCursor(Qt.CursorShape.SizeAllCursor)
            else:
                self.setCursor(Qt.CursorShape.ArrowCursor)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            position = self.get_edge_or_corner_at(event.pos())
            if position and self.cap_region_rect: # type: ignore
                self.is_resizing = True
                self.resize_position = position
                self.drag_start_pos = event.pos()
                self.rect_start = QRect(self.cap_region_rect)  # 현재 사각형 상태 저장
            elif self.can_draw:
                self.begin = event.pos()
                self.end = self.begin
                self.is_drawing = True
            elif self.cap_region_rect and self.cap_region_rect.contains(event.pos()): # type: ignore
                self.is_moving = True
                self.drag_start_pos = event.pos()
                self.rect_start = QRect(self.cap_region_rect)  # QPoint 대신 QRect로 저장

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            if self.is_drawing and self.can_draw:
                self.is_drawing = False
                if self.begin and self.end:
                    temp_rect = QRect(self.begin, self.end).normalized()
                    if temp_rect.width() >= self.min_size and temp_rect.height() >= self.min_size:
                        self.cap_region_rect = temp_rect
                        self.begin = None
                        self.end = None
                        self.can_draw = False
                        if self.cap_region_rect is not None:
                            self.save_rectangle_settings()
                    else:
                        self.begin = None
                        self.end = None
            self.is_moving = False
            self.is_resizing = False
            self.resize_position = None
            self.update()

    def moveEvent(self, event):
        super().moveEvent(event)
        if self.cap_region_rect is not None:
            self.save_rectangle_settings()

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
        self.save_rectangle_settings()
        if isinstance(self.parent(), self.main_window.__class__):
            self.parent().saveSettings() # type: ignore
        event.accept()

    def moveToCenter(self) -> None:
        """창이 화면 밖에 있는지 확인하고 필요한 경우 화면 중앙으로 이동시킵니다."""
        # 현재 화면의 geometry를 가져옵니다
        desktop = QDesktopWidget()
        screen = desktop.screenGeometry()
        
        # 창이 화면 밖에 있는지 확인합니다
        if (self.x() < 0 or self.y() < 0 or 
            self.x() + self.width() > screen.width() or 
            self.y() + self.height() > screen.height()):
            
            # 화면 중앙 좌표를 계산합니다
            center_x = (screen.width() - self.width()) // 2
            center_y = (screen.height() - self.height()) // 2
            
            # 창을 화면 중앙으로 이동시킵니다
            self.move(center_x, center_y)
            
    def loadSettings(self) -> None:
        """저장된 설정을 불러옵니다."""
        settings = SupaSettings()
        geometry = settings.value('geometry')
        if geometry:
            self.setGeometry(geometry)
            # 창 위치가 비정상적인지 확인하고 필요한 경우 중앙으로 이동
            self.moveToCenter()
        self.load_rectangle_settings()

    def keyPressEvent(self, event):
        """키 입력 이벤트를 처리합니다."""
        if event.key() == Qt.Key_Escape:
            self.hide()
        else:
            super().keyPressEvent(event)

    def save_rectangle_settings(self):
        if self.cap_region_rect:
            settings = SupaSettings()
            settings.setValue('cap_region_rect/x', self.cap_region_rect.x())
            settings.setValue('cap_region_rect/y', self.cap_region_rect.y())
            settings.setValue('cap_region_rect/width', self.cap_region_rect.width())
            settings.setValue('cap_region_rect/height', self.cap_region_rect.height())

    def load_rectangle_settings(self):
        settings = SupaSettings()
        x = int(settings.value('cap_region_rect/x', 0))
        y = int(settings.value('cap_region_rect/y', 0))
        width = int(settings.value('cap_region_rect/width', 0))
        height = int(settings.value('cap_region_rect/height', 0))
        if x != 0 and y != 0 and width != 0 and height != 0:
            self.cap_region_rect = QRect(x, y, width, height)
            self.update()

# end of file