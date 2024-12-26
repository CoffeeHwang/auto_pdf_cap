from PyQt5.QtCore import QObject, pyqtSignal
from auto_pdf_capture import auto_pdf_capture


class WorkerCapture(QObject):
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