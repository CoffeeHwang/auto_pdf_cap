from PyQt5.QtCore import QThread, pyqtSignal
from outline_ocr import run_ocr


class WorkerOcr(QThread):
    """OCR 작업을 처리하는 워커 쓰레드"""
    
    finished = pyqtSignal(list)  # OCR 처리가 완료되면 결과를 전달하는 시그널
    error = pyqtSignal(str)      # 에러 발생시 에러 메시지를 전달하는 시그널
    log = pyqtSignal(str)        # 로그 메시지를 전달하는 시그널
    
    def __init__(self, secret_key: str, api_url: str, image_files: list):
        super().__init__()
        self.secret_key = secret_key
        self.api_url = api_url
        self.image_files = image_files
        
    def show_log(self, message: str):
        """로그 메시지를 emit"""
        self.log.emit(message)
        
    def run(self):
        """쓰레드 실행"""
        try:
            # OCR 실행
            ocr_lines = run_ocr(self.secret_key, self.api_url, self.image_files, self.show_log)
            self.finished.emit(ocr_lines)
        except Exception as e:
            self.error.emit(str(e))

# end of file