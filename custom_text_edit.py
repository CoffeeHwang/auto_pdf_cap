from PyQt5.QtWidgets import QTextEdit, QSizePolicy
from PyQt5.QtCore import Qt, QSize, QPoint
from PyQt5.QtGui import QTextCursor
import os

class CustomTextEdit(QTextEdit):
    RESIZE_HANDLE_HEIGHT = 10
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_editor()
        self.resize_mode = False
        self.start_pos = None
        self.start_height = None
        self.setMouseTracking(True)
        
    def setup_editor(self):
        """에디터 설정"""
        # 탭 크기 설정 (4칸)
        self.setTabStopWidth(self.fontMetrics().width(' ') * 4)
        # 드래그 앤 드롭 활성화
        self.setAcceptDrops(True)
        # 크기 조절 정책 설정
        size_policy = QSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        size_policy.setVerticalStretch(0)  # 수직 방향으로 확장하지 않음
        size_policy.setHorizontalStretch(1)  # 수평 방향으로는 확장
        self.setSizePolicy(size_policy)
        # 최소/최대 높이 설정
        self.setMinimumHeight(self.fontMetrics().height() * 10)  # 10줄
        self.setMaximumHeight(self.fontMetrics().height() * 100)  # 100줄
        # 크기 조절 활성화
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        
    def mousePressEvent(self, event):
        """마우스 클릭 이벤트"""
        if event.button() == Qt.LeftButton and self.is_in_resize_handle(event.pos()):
            self.resize_mode = True
            self.start_pos = event.globalPos()
            self.start_height = self.height()
            event.accept()
        else:
            super().mousePressEvent(event)
            
    def mouseReleaseEvent(self, event):
        """마우스 릴리즈 이벤트"""
        if self.resize_mode:
            self.resize_mode = False
            self.start_pos = None
            self.start_height = None
            event.accept()
        else:
            super().mouseReleaseEvent(event)
            
    def mouseMoveEvent(self, event):
        """마우스 이동 이벤트"""
        if self.resize_mode and self.start_pos is not None:
            delta = event.globalPos().y() - self.start_pos.y()
            new_height = max(self.minimumHeight(), min(self.maximumHeight(), self.start_height + delta))
            self.resize(self.width(), new_height)
            event.accept()
        else:
            if self.is_in_resize_handle(event.pos()):
                self.viewport().setCursor(Qt.SizeVerCursor)
            else:
                self.viewport().setCursor(Qt.IBeamCursor)
            super().mouseMoveEvent(event)
            
    def is_in_resize_handle(self, pos):
        """크기 조절 핸들 영역인지 확인"""
        return self.height() - self.RESIZE_HANDLE_HEIGHT <= pos.y() <= self.height()
            
    def dragEnterEvent(self, event):
        """드래그 진입 이벤트"""
        if event.mimeData().hasUrls():
            event.accept()
        else:
            super().dragEnterEvent(event)

    def dragMoveEvent(self, event):
        """드래그 이동 이벤트"""
        if event.mimeData().hasUrls():
            event.setDropAction(Qt.CopyAction)
            event.accept()
        else:
            super().dragMoveEvent(event)

    def dropEvent(self, event):
        """드롭 이벤트"""
        if event.mimeData().hasUrls():
            event.setDropAction(Qt.CopyAction)
            event.accept()
            
            for url in event.mimeData().urls():
                file_path = url.toLocalFile()
                if file_path.lower().endswith('.txt'):
                    try:
                        with open(file_path, 'r', encoding='utf-8') as f:
                            content = f.read()
                        self.setPlainText(content)
                        if hasattr(self.parent(), 'status_label'):
                            self.parent().status_label.setText(f"파일을 불러왔습니다: {os.path.basename(file_path)}")
                    except Exception as e:
                        if hasattr(self.parent(), 'status_label'):
                            self.parent().status_label.setText(f"파일 불러오기 실패: {str(e)}")
                    break  # 첫 번째 텍스트 파일만 처리
        else:
            super().dropEvent(event)
            
    def keyPressEvent(self, event):
        """키 입력 이벤트 처리"""
        cursor = self.textCursor()
        
        # Tab 키: 들여쓰기
        if event.key() == Qt.Key_Tab:
            if cursor.hasSelection():
                # 선택된 텍스트의 시작과 끝 위치 저장
                start = cursor.selectionStart()
                end = cursor.selectionEnd()
                
                # 선택된 텍스트의 시작 위치로 이동
                cursor.setPosition(start)
                cursor.movePosition(QTextCursor.StartOfLine)
                
                # 선택 영역의 끝까지 각 줄마다 들여쓰기 적용
                while cursor.position() < end:
                    cursor.insertText('    ')  # 스페이스 4칸 추가
                    if not cursor.movePosition(QTextCursor.NextBlock):
                        break
                    end += 4  # 들여쓰기로 인해 끝 위치가 이동함
            else:
                cursor.insertText('    ')  # 스페이스 4칸
            return
            
        # Shift+Tab: 내어쓰기
        if event.key() == Qt.Key_Backtab:
            if cursor.hasSelection():
                # 선택된 텍스트의 시작과 끝 위치 저장
                start = cursor.selectionStart()
                end = cursor.selectionEnd()
                
                # 선택된 텍스트의 시작 위치로 이동
                cursor.setPosition(start)
                cursor.movePosition(QTextCursor.StartOfLine)
                
                # 선택 영역의 끝까지 각 줄마다 내어쓰기 적용
                while cursor.position() < end:
                    # 현재 줄의 처음 4칸이 공백인지 확인하고 제거
                    line_start = cursor.position()
                    for i in range(4):
                        cursor.movePosition(QTextCursor.NextCharacter, QTextCursor.KeepAnchor)
                        if cursor.selectedText() == ' ':
                            cursor.removeSelectedText()
                            end -= 1  # 내어쓰기로 인해 끝 위치가 이동함
                        else:
                            cursor.setPosition(line_start)  # 원래 위치로 복귀
                            break
                    
                    if not cursor.movePosition(QTextCursor.NextBlock):
                        break
            else:
                cursor.movePosition(QTextCursor.StartOfLine)
                for i in range(4):  # 최대 4칸 제거
                    cursor.movePosition(QTextCursor.NextCharacter, QTextCursor.KeepAnchor)
                    if cursor.selectedText() == ' ':
                        cursor.removeSelectedText()
                    else:
                        break
            return
            
        # Enter 키: 자동 들여쓰기 유지
        if event.key() == Qt.Key_Return:
            # 현재 줄의 들여쓰기 수준 계산
            cursor.movePosition(QTextCursor.StartOfLine)
            spaces = 0
            while cursor.position() < self.textCursor().position():
                cursor.movePosition(QTextCursor.NextCharacter, QTextCursor.KeepAnchor)
                if cursor.selectedText() == ' ':
                    spaces += 1
                else:
                    break
                    
            # 기본 Enter 동작 수행
            super().keyPressEvent(event)
            
            # 이전 줄의 들여쓰기 수준 유지
            if spaces > 0:
                cursor = self.textCursor()
                cursor.insertText(' ' * spaces)
            return
            
        # Ctrl+D: 현재 줄 복제
        if event.key() == Qt.Key_D and event.modifiers() == Qt.ControlModifier:
            cursor.movePosition(QTextCursor.StartOfLine)
            cursor.movePosition(QTextCursor.EndOfLine, QTextCursor.KeepAnchor)
            text = cursor.selectedText()
            cursor.movePosition(QTextCursor.EndOfLine)
            cursor.insertText('\n' + text)
            return
            
        # 기본 키 이벤트 처리
        super().keyPressEvent(event)
