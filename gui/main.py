import sys
from PySide6.QtWidgets import QApplication, QMainWindow, QTabWidget

from projects_tab import ProjectsTab
from experiments_tab import ExperimentsTab
from datasets_tab import DatasetsTab
from analysis_tab import AnalysisTab
from styles import STYLESHEET


class MemsClient(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("MEMS Client")
        self.resize(950, 700)

        tabs = QTabWidget()
        tabs.addTab(ProjectsTab(), "Projects")
        tabs.addTab(ExperimentsTab(), "Experiments")
        tabs.addTab(DatasetsTab(), "Datasets")
        tabs.addTab(AnalysisTab(), "Analysis")

        self.setCentralWidget(tabs)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyleSheet(STYLESHEET)   # <-- the one new line
    window = MemsClient()
    window.show()
    sys.exit(app.exec())