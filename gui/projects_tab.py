from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QPushButton, QLineEdit, QLabel, QMessageBox, QHeaderView
)

import api_client


class ProjectsTab(QWidget):
    def __init__(self):
        super().__init__()

        layout = QVBoxLayout()

        self.table = QTableWidget()
        self.table.setColumnCount(3)
        self.table.setHorizontalHeaderLabels(["ID", "Name", "Description"])
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        # Selecting a row loads it into the form below, so the same
        # fields double as both "create new" and "edit this one".
        self.table.itemSelectionChanged.connect(self.on_selection_changed)
        layout.addWidget(self.table)

        form_layout = QHBoxLayout()
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("Project name")
        self.desc_input = QLineEdit()
        self.desc_input.setPlaceholderText("Description (optional)")
        create_button = QPushButton("Create Project")
        create_button.clicked.connect(self.handle_create)
        update_button = QPushButton("Update Selected")
        update_button.clicked.connect(self.handle_update)
        delete_button = QPushButton("Delete Selected")
        delete_button.clicked.connect(self.handle_delete)
        clear_button = QPushButton("Clear")
        clear_button.clicked.connect(self.clear_form)

        form_layout.addWidget(self.name_input)
        form_layout.addWidget(self.desc_input)
        form_layout.addWidget(create_button)
        form_layout.addWidget(update_button)
        form_layout.addWidget(delete_button)
        form_layout.addWidget(clear_button)
        layout.addLayout(form_layout)

        self.status_label = QLabel("")
        layout.addWidget(self.status_label)

        self.setLayout(layout)

        self.selected_project_id = None
        self.refresh_projects()

    def refresh_projects(self):
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

    def on_selection_changed(self):
        selected_rows = self.table.selectionModel().selectedRows()
        if not selected_rows:
            return
        row = selected_rows[0].row()
        self.selected_project_id = int(self.table.item(row, 0).text())
        self.name_input.setText(self.table.item(row, 1).text())
        self.desc_input.setText(self.table.item(row, 2).text())

    def clear_form(self):
        self.table.clearSelection()
        self.selected_project_id = None
        self.name_input.clear()
        self.desc_input.clear()

    def handle_create(self):
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
        self.clear_form()
        self.refresh_projects()

    def handle_update(self):
        if self.selected_project_id is None:
            QMessageBox.warning(self, "No selection", "Select a project in the table first.")
            return
        name = self.name_input.text().strip()
        desc = self.desc_input.text().strip() or None
        if not name:
            QMessageBox.warning(self, "Missing name", "Project name is required.")
            return
        try:
            api_client.update_project(self.selected_project_id, name, desc)
        except api_client.APIError as e:
            QMessageBox.critical(self, "Error", f"Could not update project: {e.detail}")
            return
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Could not reach the API: {e}")
            return
        self.clear_form()
        self.refresh_projects()

    def handle_delete(self):
        if self.selected_project_id is None:
            QMessageBox.warning(self, "No selection", "Select a project in the table first.")
            return
        # Confirm before a cascade delete -- this removes every
        # Experiment/Dataset/Analysis under this project too.
        confirm = QMessageBox.question(
            self, "Confirm delete",
            f"Delete project {self.selected_project_id}? This will also delete "
            "all its experiments, datasets, and analysis results.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if confirm != QMessageBox.StandardButton.Yes:
            return
        try:
            api_client.delete_project(self.selected_project_id)
        except api_client.APIError as e:
            QMessageBox.critical(self, "Error", f"Could not delete project: {e.detail}")
            return
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Could not reach the API: {e}")
            return
        self.clear_form()
        self.refresh_projects()