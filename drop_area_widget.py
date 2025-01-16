from PyQt5.QtWidgets import QLabel
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QDragEnterEvent, QDropEvent
import os

class DropAreaWidget(QLabel):
    def __init__(self, accept_extensions, parent=None):
        super().__init__(parent)
        self.accept_extensions = accept_extensions
        self.file_path = ""
        
        # 스타일 설정
        self.setAlignment(Qt.AlignCenter)
        
        # 드래그 앤 드롭 활성화
        self.setAcceptDrops(True)
        
        # 초기 텍스트 설정
        self.update_text()
        
    def update_text(self):
        if not self.file_path:
            extensions = ", ".join(self.accept_extensions)
            self.setText(f"{extensions} 파일을 여기에 드래그하세요")
        else:
            filename = os.path.basename(self.file_path)
            self.setText(filename)
            
    def dragEnterEvent(self, event: QDragEnterEvent):
        if event.mimeData().hasUrls():
            file_path = event.mimeData().urls()[0].toLocalFile()
            file_ext = file_path.lower().split('.')[-1]
            if file_ext in self.accept_extensions:
                event.acceptProposedAction()
                
    def dropEvent(self, event: QDropEvent):
        file_path = event.mimeData().urls()[0].toLocalFile()
        self.file_path = file_path
        self.update_text()
        event.acceptProposedAction()

    def set_file_path(self, file_path: str) -> None:
        """파일 경로를 설정하고 표시 텍스트를 업데이트합니다."""
        if os.path.exists(file_path):
            file_ext = file_path.lower().split('.')[-1]
            if file_ext in self.accept_extensions:
                self.file_path = file_path
                self.update_text()

# end of file