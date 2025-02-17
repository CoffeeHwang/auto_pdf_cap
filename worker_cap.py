from PyQt6.QtCore import QObject, pyqtSignal
from auto_pdf_capture import auto_pdf_capture

class WorkerCapture(QObject):
    finished = pyqtSignal()  # 작업 완료 시그널
    log_message_signal = pyqtSignal(str)  # 로그 메시지 시그널
    
    def __init__(self, main_window, file_name: str, page_loop: int,
                 x1: int, y1: int, x2: int, y2: int,
                 margin: dict[str, int], diff_width: int,
                 automation_delay: float, left_first: bool = True):
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
        self.left_first = left_first
        self._is_running = False

    def run(self):
        """캡쳐 작업을 실행합니다."""
        self._is_running = True
        try:
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
                left_first=self.left_first,
            log_message_signal=self.log_message_signal,   # type: ignore
            is_running=lambda: self._is_running  # 실행 상태를 확인하는 콜백 함수 전달
            )
        except Exception as e:
            self.log_message_signal.emit(f"오류 발생: {str(e)}")
        finally:
            self.finished.emit()

    def stop(self):
        """작업을 중지합니다."""
        self._is_running = False

# end of file