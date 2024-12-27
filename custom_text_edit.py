from PyQt5.QtWidgets import QTextEdit
from PyQt5.QtCore import Qt, QMimeData
from PyQt5.QtGui import QTextCursor, QDragEnterEvent, QDropEvent
import os

class CustomTextEdit(QTextEdit):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent
        self.setup_editor()
        self._content_changed = False  # 내용 변경 플래그
        self.textChanged.connect(self._on_content_changed)
        
    def setup_editor(self):
        """에디터 설정"""
        # 탭 크기 설정
        self.setTabStopWidth(self.fontMetrics().width(' ') * 4)
        # 드래그 앤 드롭 활성화
        self.setAcceptDrops(True)
        # 읽기 전용 해제
        self.setReadOnly(False)
        
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
        """드롭 이벤트"""
        if event.mimeData().hasUrls():
            event.setDropAction(Qt.CopyAction)
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
        """텍스트 내용이 변경되었음을 표시"""
        self._content_changed = True
        if hasattr(self.parent, 'status_label'):
            self.parent.status_label.setText("편집 중...")
            
    def save_if_needed(self):
        """필요한 경우에만 저장 수행"""
        if not self._content_changed:
            return False
            
        if not self.parent or not hasattr(self.parent, 'current_file_path'):
            return False
            
        file_path = self.parent.current_file_path
        if not file_path:
            return False
            
        try:
            if not os.path.exists(os.path.dirname(file_path)):
                if hasattr(self.parent, 'status_label'):
                    self.parent.status_label.setText("저장할 디렉토리가 존재하지 않습니다.")
                return False
                
            content = self.toPlainText()
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            self._content_changed = False  # 저장 완료 후 플래그 초기화
            
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
            
    def focusOutEvent(self, event):
        """포커스를 잃을 때 자동 저장"""
        self.save_if_needed()
        super().focusOutEvent(event)

    def keyPressEvent(self, event):
        """키 입력 이벤트 처리"""            
        cursor = self.textCursor()
        
        # Tab 키 처리
        if event.key() == Qt.Key_Tab:
            cursor.insertText("    ")  # 4칸 스페이스
            return
            
        # Enter 키 처리
        if event.key() == Qt.Key_Return:
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
            
        super().keyPressEvent(event)
