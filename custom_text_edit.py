from PyQt5.QtWidgets import QTextEdit
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QTextCursor

class CustomTextEdit(QTextEdit):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_editor()
        
    def setup_editor(self):
        """에디터 설정"""
        # 탭 크기 설정 (4칸)
        self.setTabStopWidth(self.fontMetrics().width(' ') * 4)
        
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
