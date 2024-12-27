from PyQt5.QtWidgets import QLabel
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QDragEnterEvent, QDropEvent

class DropAreaWidget(QLabel):
    def __init__(self, accept_extensions, parent=None):
        super().__init__(parent)
        self.accept_extensions = accept_extensions
        self.current_file = ""
        
        # 스타일 설정
        self.setAlignment(Qt.AlignCenter)
        # self.setStyleSheet("""
        #     QLabel {
        #         border: 2px dashed #aaa;
        #         border-radius: 5px;
        #         padding: 20px;
        #         background-color: #f8f8f8;
        #     }
        #     QLabel:hover {
        #         border-color: #666;
        #         background-color: #f0f0f0;
        #     }
        # """)
        
        # 드래그 앤 드롭 활성화
        self.setAcceptDrops(True)
        
        # 초기 텍스트 설정
        self.update_text()
        
    def update_text(self):
        if not self.current_file:
            extensions = ", ".join(self.accept_extensions)
            self.setText(f"{extensions} 파일을 여기에 드래그하세요")
        else:
            self.setText(f"현재 파일: {self.current_file}")
            
    def dragEnterEvent(self, event: QDragEnterEvent):
        if event.mimeData().hasUrls():
            file_path = event.mimeData().urls()[0].toLocalFile()
            file_ext = file_path.lower().split('.')[-1]
            if file_ext in self.accept_extensions:
                event.acceptProposedAction()
                
    def dropEvent(self, event: QDropEvent):
        file_path = event.mimeData().urls()[0].toLocalFile()
        self.current_file = file_path
        self.update_text()
        event.acceptProposedAction()
