from RVM.mainWindow import MainWindow
import sys
from PyQt6.QtWidgets import QApplication
from qdarktheme import setup_theme
import ctypes

if __name__ == "__main__":
    myappid = u'rootlab.rootvideomanager.v.1'
    ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)
    app = QApplication(sys.argv)
    qss = """
    * {
        font-size: 12px;
    }
    QTreeWidget {
        font-size: 15px;
        font-weight: 400;
    }
    QTreeWidget::item {
        height: 30px;
    }
    """
    setup_theme('auto', additional_qss=qss)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())

