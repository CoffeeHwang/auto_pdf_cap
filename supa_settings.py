"""
SupaSettings 모듈입니다.
QSettings를 상속받아 간단한 getter/setter를 제공합니다.
"""

from PyQt6.QtCore import QSettings
from typing import Any


class SupaSettings(QSettings):
    """
    QSettings를 상속받아 간단한 getter/setter를 제공하는 클래스입니다.
    모든 설정값은 이 클래스를 통해 접근합니다.
    """
    def __init__(self) -> None:
        """SupaSettings 클래스를 초기화합니다."""
        self.settings = QSettings("supa-apps.auto-pdf-cap", "settings")
        
    def value(self, key: str, defaultValue: Any = "") -> Any:
        return self.settings.value(key, defaultValue)

    def setValue(self, key: str, value: Any) -> None:
        self.settings.setValue(key, value)

# end of file