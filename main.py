from PyQt5.QtWidgets import QApplication
import sys
from main_window import MainWindow


if __name__ == '__main__':
    app = QApplication(sys.argv)
    main_window = MainWindow()
    main_window.show()
    sys.exit(app.exec_())

# end of file