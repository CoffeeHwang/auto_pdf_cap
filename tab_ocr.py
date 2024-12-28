from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QListWidget, QLabel, 
                           QListWidgetItem, QDialog, QDesktopWidget, QPushButton, QMessageBox)
from PyQt5.QtCore import Qt, QSettings, QPoint
from PyQt5.QtGui import QPixmap
import os
from outline_ocr import run_ocr

class ImagePreviewDialog(QDialog):
    def __init__(self, image_path, parent=None):
        super().__init__(parent, Qt.WindowStaysOnTopHint | Qt.FramelessWindowHint | Qt.Tool)  
        self.setStyleSheet("background-color: black;")
        self.setAttribute(Qt.WA_ShowWithoutActivating)  
        
        # 마우스 드래그 관련 변수
        self.dragging = False
        self.drag_position = QPoint()
        
        # 설정 객체 생성
        self.settings = QSettings('Coffee.Hwang', 'AutoPdfCap')
        
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
        
        # 창이 닫힐 때 위치 저장
        self.closeEvent = self.on_close
        
    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.dragging = True
            # 현재 마우스 위치와 창의 위치 차이를 저장
            self.drag_position = event.globalPos() - self.frameGeometry().topLeft()
            event.accept()
            
    def mouseMoveEvent(self, event):
        if event.buttons() & Qt.LeftButton and self.dragging:
            # 창을 새로운 위치로 이동
            self.move(event.globalPos() - self.drag_position)
            event.accept()
            
    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.dragging = False
            event.accept()
        
    def get_center_position(self):
        # 화면의 중앙 위치 계산
        screen = QDesktopWidget().screenGeometry()
        size = self.geometry()
        return (screen.width() - size.width()) // 2, (screen.height() - size.height()) // 2
        
    def position_window(self):
        # 저장된 위치 불러오기
        pos = self.settings.value('preview_window_pos')
        
        if pos:
            # 저장된 위치가 있으면 해당 위치로 이동
            self.move(pos)
        else:
            # 저장된 위치가 없으면 화면 중앙으로 이동
            x, y = self.get_center_position()
            self.move(x, y)
            
    def on_close(self, event):
        # 창이 닫힐 때 현재 위치 저장
        self.settings.setValue('preview_window_pos', self.pos())
        event.accept()

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
            self.preview_dialog.position_window()  # 위치 설정
            self.preview_dialog.show()

    def keyPressEvent(self, event):
        # ESC 키가 눌렸을 때
        if event.key() == Qt.Key_Escape:
            # 미리보기 창이 있다면 닫기
            if self.preview_dialog:
                self.preview_dialog.close()
                self.preview_dialog = None
            event.accept()
        # Delete 또는 Backspace 키가 눌렸을 때
        elif event.key() in (Qt.Key_Delete, Qt.Key_Backspace):
            # 선택된 아이템들의 행 번호를 저장
            selected_rows = [self.row(item) for item in self.selectedItems()]
            if not selected_rows:
                return
                
            # 마지막으로 선택된 아이템의 행 번호
            last_selected_row = max(selected_rows)
            
            # 선택된 아이템들을 리스트에서 제거
            for item in self.selectedItems():
                # 미리보기 창이 열려있고, 현재 삭제하려는 아이템의 이미지를 보여주고 있다면 닫기
                if (self.preview_dialog and 
                    self.preview_dialog.isVisible() and 
                    item.data(Qt.UserRole) == self.selectedItems()[0].data(Qt.UserRole)):
                    self.preview_dialog.close()
                    self.preview_dialog = None
                
                # 아이템 삭제
                self.takeItem(self.row(item))
            
            # 삭제 후 아이템이 남아있는 경우
            if self.count() > 0:
                # 하단 아이템이 있는지 확인
                if last_selected_row < self.count():
                    # 하단 아이템 선택
                    self.setCurrentRow(last_selected_row)
                else:
                    # 상단 아이템 선택 (마지막 아이템)
                    self.setCurrentRow(self.count() - 1)
            
            event.accept()
        else:
            # 다른 키는 기본 처리
            super().keyPressEvent(event)

class OcrTab(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.main_window = parent
        self.settings = QSettings('Coffee.Hwang', 'AutoPdfCap')
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        # 안내 레이블 추가
        label = QLabel("이미지 파일을 드래그하여 추가하세요")
        layout.addWidget(label)
        
        # 이미지 리스트 위젯 추가
        self.image_list = ImageListWidget(self)
        self.image_list.model().rowsInserted.connect(self.update_scan_button)
        self.image_list.model().rowsRemoved.connect(self.update_scan_button)
        layout.addWidget(self.image_list)
        
        # OCR 스캔 버튼 추가
        self.scan_button = QPushButton("OCR 스캔")
        self.scan_button.clicked.connect(self.on_scan_button_clicked)
        self.scan_button.setEnabled(False)  # 초기 상태는 비활성화
        layout.addWidget(self.scan_button)
        
    def update_scan_button(self):
        """이미지 리스트의 상태에 따라 스캔 버튼 활성화/비활성화"""
        self.scan_button.setEnabled(self.image_list.count() > 0)

    def on_scan_button_clicked(self):
        """OCR 스캔 버튼 클릭 시 실행되는 임시 메서드"""
        image_files = [self.image_list.item(i) for i in range(self.image_list.count())]
            
        # 파일 경로 리스트 생성
        file_paths = []
        for item in image_files:
            file_path = item.data(Qt.UserRole)  # 아이템에 저장된 파일 경로
            print(f"파일 경로: {file_path}")
            file_paths.append(file_path)

        secret_key = self.settings.value('ocr/secret_key', '')
        api_url = self.settings.value('ocr/api_url', '')
        if secret_key and api_url:
            ocr_lines: list = run_ocr(secret_key, api_url, file_paths)
            
            # OCR 결과를 개요적용 탭으로 전달
            if ocr_lines:
                gen_outline_tab = self.main_window.gen_outline_tab
                # 현재 PDF 파일 정보가 있으면 함께 전달
                current_file = None
                if hasattr(self.main_window, 'basic_tab'):
                    file_name = self.main_window.basic_tab.file_name_edit.text().strip()
                    if file_name:
                        current_file = file_name + ".txt"
                gen_outline_tab.update_from_ocr_tab("\n".join(ocr_lines), current_file)
                # 개요적용 탭으로 전환
                self.main_window.tab_widget.setCurrentWidget(gen_outline_tab)
        else:
            print("OCR 설정이 없습니다. 환경설정에서 설정하세요.")
            QMessageBox.warning(self, "경고", 
                              "OCR 설정이 필요합니다.\n\n"
                              "파일 메뉴 → 환경설정에서 Secret Key와 API URL을 설정해주세요.")
