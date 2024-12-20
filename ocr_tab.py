from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QListWidget, QLabel, 
                           QListWidgetItem, QDialog)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPixmap

class ImagePreviewDialog(QDialog):
    def __init__(self, image_path, parent=None):
        super().__init__(parent, Qt.WindowStaysOnTopHint | Qt.FramelessWindowHint | Qt.Tool)  
        self.setStyleSheet("background-color: black;")
        self.setAttribute(Qt.WA_ShowWithoutActivating)  
        
        layout = QVBoxLayout(self)
        
        # 이미지 표시 레이블
        image_label = QLabel()
        pixmap = QPixmap(image_path)
        # 이미지 크기를 적절히 조절 (최대 800x800)
        scaled_pixmap = pixmap.scaled(800, 800, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        image_label.setPixmap(scaled_pixmap)
        layout.addWidget(image_label)
        
        # 창 크기를 이미지에 맞게 조절
        self.resize(scaled_pixmap.width(), scaled_pixmap.height())

class ImageListWidget(QListWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAcceptDrops(True)
        self.setSelectionMode(QListWidget.ExtendedSelection)
        self.preview_dialog = None
        
        # 아이템 선택 변경 시그널 연결
        self.itemSelectionChanged.connect(self.on_selection_changed)

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.accept()
        else:
            event.ignore()

    def dragMoveEvent(self, event):
        if event.mimeData().hasUrls():
            event.setDropAction(Qt.CopyAction)
            event.accept()
        else:
            event.ignore()

    def dropEvent(self, event):
        if event.mimeData().hasUrls():
            event.setDropAction(Qt.CopyAction)
            event.accept()
            
            for url in event.mimeData().urls():
                file_path = url.toLocalFile()
                if file_path.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp', '.gif')):
                    # 리스트 아이템 생성
                    item = QListWidgetItem()
                    item.setData(Qt.UserRole, file_path)  # 전체 파일 경로는 데이터로 저장
                    item.setText(file_path.split('/')[-1])  # 보여지는 부분에는 파일명만 표시
                    
                    self.addItem(item)
        else:
            event.ignore()
            
    def on_selection_changed(self):
        # 기존 미리보기 창이 있다면 닫기
        if self.preview_dialog:
            self.preview_dialog.close()
            self.preview_dialog = None
            
        # 현재 선택된 아이템 확인
        selected_items = self.selectedItems()
        if selected_items:
            # 선택된 첫 번째 아이템의 이미지 경로 가져오기
            image_path = selected_items[0].data(Qt.UserRole)
            
            # 새 미리보기 창 생성 및 표시
            self.preview_dialog = ImagePreviewDialog(image_path, self)
            
            # 현재 마우스 위치에서 약간 오프셋을 준 위치에 창 표시
            cursor_pos = self.cursor().pos()
            self.preview_dialog.move(cursor_pos.x() + 20, cursor_pos.y() + 20)
            self.preview_dialog.show()

    def keyPressEvent(self, event):
        # ESC 키가 눌렸을 때
        if event.key() == Qt.Key_Escape:
            # 미리보기 창이 있다면 닫기
            if self.preview_dialog:
                self.preview_dialog.close()
                self.preview_dialog = None
            event.accept()
        else:
            # 다른 키는 기본 처리
            super().keyPressEvent(event)

class OcrTab(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.main_window = parent
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        # 안내 레이블 추가
        label = QLabel("이미지 파일을 드래그하여 추가하세요")
        layout.addWidget(label)
        
        # 이미지 리스트 위젯 추가
        self.image_list = ImageListWidget(self)
        layout.addWidget(self.image_list)
