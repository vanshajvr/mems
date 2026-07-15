import sys
from PySide6.QtWidgets import QApplication, QMainWindow, QTabWidget, QWidget, QLabel, QVBoxLayout

from projects_tab import ProjectsTab
from experiments_tab import ExperimentsTab


class MemsClient(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("MEMS Client")
        self.resize(900, 600)

        tabs = QTabWidget()
        tabs.addTab(ProjectsTab(), "Projects")
        tabs.addTab(ExperimentsTab(), "Experiments")
        tabs.addTab(self._placeholder_tab("Upload tab -- coming in Phase 4"), "Datasets")
        tabs.addTab(self._placeholder_tab("Analysis/Report tab -- coming in Phase 5"), "Analysis")

        self.setCentralWidget(tabs)

    def _placeholder_tab(self, text):
        widget = QWidget()
        layout = QVBoxLayout()
        layout.addWidget(QLabel(text))
        widget.setLayout(layout)
        return widget


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MemsClient()
    window.show()
    sys.exit(app.exec())