from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QPushButton, QLineEdit, QLabel, QMessageBox, QHeaderView
)
from PySide6.QtCore import Qt

import api_client


class ProjectsTab(QWidget):
    def __init__(self):
        super().__init__()

        layout = QVBoxLayout()

        # -- Table showing existing projects --
        self.table = QTableWidget()
        self.table.setColumnCount(3)
        self.table.setHorizontalHeaderLabels(["ID", "Name", "Description"])
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        layout.addWidget(self.table)

        # -- Form to create a new project --
        form_layout = QHBoxLayout()
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("Project name")
        self.desc_input = QLineEdit()
        self.desc_input.setPlaceholderText("Description (optional)")
        create_button = QPushButton("Create Project")
        create_button.clicked.connect(self.handle_create)

        form_layout.addWidget(self.name_input)
        form_layout.addWidget(self.desc_input)
        form_layout.addWidget(create_button)
        layout.addLayout(form_layout)

        self.status_label = QLabel("")
        layout.addWidget(self.status_label)

        self.setLayout(layout)

        # Load whatever's already in the database as soon as the tab opens
        self.refresh_projects()

    def refresh_projects(self):
        """Fetch projects from the API and repopulate the table."""
        try:
            projects = api_client.get_projects()
        except Exception as e:
            self.status_label.setText(f"Failed to load projects: {e}")
            return

        self.table.setRowCount(len(projects))
        for row, project in enumerate(projects):
            self.table.setItem(row, 0, QTableWidgetItem(str(project["id"])))
            self.table.setItem(row, 1, QTableWidgetItem(project["name"]))
            self.table.setItem(row, 2, QTableWidgetItem(project.get("desc") or ""))

        self.status_label.setText(f"{len(projects)} project(s) loaded")

    def handle_create(self):
        """Called when 'Create Project' is clicked."""
        name = self.name_input.text().strip()
        desc = self.desc_input.text().strip() or None

        if not name:
            QMessageBox.warning(self, "Missing name", "Project name is required.")
            return

        try:
            api_client.create_project(name, desc)
        except api_client.APIError as e:
            QMessageBox.critical(self, "Error", f"Could not create project: {e.detail}")
            return
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Could not reach the API: {e}")
            return

        self.name_input.clear()
        self.desc_input.clear()
        self.refresh_projects()  # show the new project immediately
