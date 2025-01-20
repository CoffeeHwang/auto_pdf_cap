from PyQt6.QtWidgets import QTextEdit
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QDragEnterEvent, QDropEvent, QKeyEvent
import os

class CustomTextEdit(QTextEdit):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent
        self.setup_editor()
        
        # 자동 저장 타이머 설정
        self._save_timer = QTimer(self)
        self._save_timer.setInterval(2000)  # 2초 딜레이
        self._save_timer.setSingleShot(True)  # 한 번만 실행
        self._save_timer.timeout.connect(self.save_if_needed)
        
        self.textChanged.connect(self._on_content_changed)
        
    def setup_editor(self):
        """에디터 설정"""
        # 탭 간격 설정 (스페이스 4개 크기)
        self.setTabStopDistance(self.fontMetrics().horizontalAdvance(' ') * 4)
        # 드래그 앤 드롭 활성화
        self.setAcceptDrops(True)
        # 읽기 전용 해제
        self.setReadOnly(False)
        
    def dragEnterEvent(self, event: QDragEnterEvent) -> None:
        if event.mimeData().hasUrls():
            event.accept()
        else:
            event.ignore()

    def dragMoveEvent(self, event: QDragEnterEvent) -> None:
        if event.mimeData().hasUrls():
            event.setDropAction(Qt.DropAction.CopyAction)
            event.accept()
        else:
            event.ignore()            

    def dropEvent(self, event: QDropEvent) -> None:
        """드롭 이벤트"""
        if event.mimeData().hasUrls():
            event.setDropAction(Qt.DropAction.CopyAction)
            event.accept()
                
            file_path = event.mimeData().urls()[0].toLocalFile()
            try:
                # 파일 내용 읽기
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # 텍스트 설정 및 편집 가능하게 설정
                self.setPlainText(content)
                
                # 부모 위젯(SummaryTab)의 파일명 및 경로 업데이트
                if hasattr(self.parent, 'set_current_filename'):
                    filename = file_path.split('/')[-1]  # 파일명 추출
                    self.parent.set_current_filename(filename)
                    self.parent.current_file_path = file_path  # 경로 업데이트
                    self.parent.status_label.setText(f"파일을 불러왔습니다: {filename}")
                    
            except Exception as e:
                if hasattr(self.parent, 'status_label'):
                    self.parent.status_label.setText(f"파일 불러오기 실패: {str(e)}")
        else:
            event.ignore()

    def _on_content_changed(self):
        # 타이머 재시작 (이전 타이머가 있다면 취소하고 새로 시작)
        self._save_timer.start()
        if hasattr(self.parent, 'status_label'):
            self.parent.status_label.setText("편집 중...")
            
    def save_if_needed(self):
        """필요한 경우에만 저장 수행"""            
        file_path = self.parent.current_file_path
        if not file_path:
            self.parent.status_label.setText("저장할 파일이 지정되지 않았습니다.")
            return False
            
        try:
            if not os.path.exists(os.path.dirname(file_path)):
                if hasattr(self.parent, 'status_label'):
                    self.parent.status_label.setText("저장할 디렉토리가 존재하지 않습니다.")
                return False
                
            # 파일 감시 일시 중단
            if hasattr(self.parent, 'file_watcher'):
                was_watching = file_path in self.parent.file_watcher.files()
                if was_watching:
                    self.parent.file_watcher.removePath(file_path)
            
            # 파일 저장
            content = self.toPlainText()
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            # 파일 감시 재시작
            if hasattr(self.parent, 'file_watcher') and was_watching:
                self.parent.file_watcher.addPath(file_path)
            
            if hasattr(self.parent, 'status_label'):
                self.parent.status_label.setText("자동 저장됨")
            return True
            
        except PermissionError:
            if hasattr(self.parent, 'status_label'):
                self.parent.status_label.setText("파일 저장 권한이 없습니다.")
        except Exception as e:
            if hasattr(self.parent, 'status_label'):
                self.parent.status_label.setText(f"저장 실패: {str(e)}")
        return False
            
    def keyPressEvent(self, event: QKeyEvent) -> None:
        """키 입력 이벤트를 처리합니다."""
        cursor = self.textCursor()
        
        # Tab 키 처리
        if event.key() == Qt.Key.Key_Tab:
            cursor.insertText("    ")  # 4칸 스페이스
            return
            
        # Enter 키 처리
        if event.key() == Qt.Key.Key_Return:
            # 현재 줄의 들여쓰기를 유지
            block = cursor.block()
            text = block.text()
            indentation = ""
            for char in text:
                if char.isspace():
                    indentation += char
                else:
                    break
            
            # Enter와 들여쓰기 삽입
            cursor.insertText("\n" + indentation)
            return
            
        # CMD+A (전체 선택)
        if event.key() == Qt.Key.Key_A and event.modifiers() & Qt.KeyboardModifier.ControlModifier:
            self.selectAll()
            return
            
        super().keyPressEvent(event)

# end of file