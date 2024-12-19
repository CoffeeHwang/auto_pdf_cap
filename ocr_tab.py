from PyQt5.QtWidgets import QWidget, QVBoxLayout

class OcrTab(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.main_window = parent
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        # OCR 탭의 UI 요소들을 여기에 추가합니다.
