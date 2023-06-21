import ctypes
import sys

from PyQt6.QtWidgets import QApplication
from qdarktheme import setup_theme

from RVM.mainWindow import MainWindow

if __name__ == "__main__":
    myappid = "rootlab.rootvideomanager.v.1"
    ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)
    app = QApplication(sys.argv)
    qss = """
    * {
        font-size: 12px;
    }
    QToolTip {
        font-size: 12px;
        color: #000000;
    }
    QTreeWidget {
        font-size: 15px;
        font-weight: 400;
    }
    QTreeWidget::item {
        height: 30px;
    }
    QListWidget {
        font-size: 15px;
        font-weight: 400;
    }
    QLabel {
        font-size: 15px;
        font-weight: 600;
    }
    """
    setup_theme("auto", additional_qss=qss)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
