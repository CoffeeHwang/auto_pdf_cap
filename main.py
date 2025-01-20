from PyQt6.QtWidgets import QApplication
import sys
from main_window import MainWindow

if __name__ == "__main__":
    app = QApplication(sys.argv)
    main_window = MainWindow()
    main_window.show()
    sys.exit(app.exec())  # PyQt6에서는 exec_() -> exec()로 변경

# end of file