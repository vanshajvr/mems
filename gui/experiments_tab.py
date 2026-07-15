from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QPushButton, QLineEdit, QLabel, QMessageBox, QHeaderView, QComboBox
)

import api_client


class ExperimentsTab(QWidget):
    def __init__(self):
        super().__init__()

        layout = QVBoxLayout()

        selector_layout = QHBoxLayout()
        selector_layout.addWidget(QLabel("Project:"))
        self.project_combo = QComboBox()
        self.project_combo.currentIndexChanged.connect(self.on_project_changed)
        selector_layout.addWidget(self.project_combo, stretch=1)
        refresh_button = QPushButton("Refresh Projects")
        refresh_button.clicked.connect(self.load_projects)
        selector_layout.addWidget(refresh_button)
        layout.addLayout(selector_layout)

        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(["ID", "Title", "Instrument", "Freq (Hz)", "Notes"])
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeMode.Stretch)
        self.table.itemSelectionChanged.connect(self.on_selection_changed)
        layout.addWidget(self.table)
        self.table.setAlternatingRowColors(True)

        form_layout = QHBoxLayout()
        self.title_input = QLineEdit()
        self.title_input.setPlaceholderText("Experiment title")
        self.instrument_input = QLineEdit()
        self.instrument_input.setPlaceholderText("Instrument (optional)")
        self.freq_input = QLineEdit()
        self.freq_input.setPlaceholderText("Freq Hz (optional)")
        create_button = QPushButton("Create Experiment")
        create_button.clicked.connect(self.handle_create)
        update_button = QPushButton("Update Selected")
        update_button.clicked.connect(self.handle_update)
        delete_button = QPushButton("Delete Selected")
        delete_button.setObjectName("dangerButton")
        delete_button.clicked.connect(self.handle_delete)
        clear_button = QPushButton("Clear")
        clear_button.clicked.connect(self.clear_form)

        form_layout.addWidget(self.title_input)
        form_layout.addWidget(self.instrument_input)
        form_layout.addWidget(self.freq_input)
        form_layout.addWidget(create_button)
        form_layout.addWidget(update_button)
        form_layout.addWidget(delete_button)
        form_layout.addWidget(clear_button)
        layout.addLayout(form_layout)

        self.status_label = QLabel("")
        layout.addWidget(self.status_label)

        self.setLayout(layout)

        self.selected_experiment_id = None
        self.load_projects()

    def load_projects(self):
        try:
            projects = api_client.get_projects()
        except Exception as e:
            self.status_label.setText(f"Failed to load projects: {e}")
            return

        self.project_combo.blockSignals(True)
        self.project_combo.clear()
        for p in projects:
            self.project_combo.addItem(f"{p['id']} - {p['name']}", p["id"])
        self.project_combo.blockSignals(False)

        if projects:
            self.refresh_experiments()
        else:
            self.table.setRowCount(0)
            self.status_label.setText("No projects yet -- create one in the Projects tab first")

    def on_project_changed(self, index):
        self.clear_form()
        self.refresh_experiments()

    def refresh_experiments(self):
        project_id = self.project_combo.currentData()
        if project_id is None:
            self.table.setRowCount(0)
            return

        try:
            experiments = api_client.get_experiments_for_project(project_id)
        except Exception as e:
            self.status_label.setText(f"Failed to load experiments: {e}")
            return

        self.table.setRowCount(len(experiments))
        for row, exp in enumerate(experiments):
            self.table.setItem(row, 0, QTableWidgetItem(str(exp["id"])))
            self.table.setItem(row, 1, QTableWidgetItem(exp["title"]))
            self.table.setItem(row, 2, QTableWidgetItem(exp.get("instrument") or ""))
            freq = exp.get("freq")
            self.table.setItem(row, 3, QTableWidgetItem(str(freq) if freq is not None else ""))
            self.table.setItem(row, 4, QTableWidgetItem(exp.get("notes") or ""))

        self.status_label.setText(f"{len(experiments)} experiment(s) loaded")

    def _item_text(self, row, col):
        item = self.table.item(row, col)
        return item.text() if item is not None else ""

    def on_selection_changed(self):
        selected_rows = self.table.selectionModel().selectedRows()
        if not selected_rows:
            return
        row = selected_rows[0].row()
        self.selected_experiment_id = int(self._item_text(row, 0))
        self.title_input.setText(self._item_text(row, 1))
        self.instrument_input.setText(self._item_text(row, 2))
        self.freq_input.setText(self._item_text(row, 3))

    def clear_form(self):
        self.table.clearSelection()
        self.selected_experiment_id = None
        self.title_input.clear()
        self.instrument_input.clear()
        self.freq_input.clear()

    def _parse_freq(self):
        """Shared by create and update -- returns (freq, error_or_None)."""
        freq_text = self.freq_input.text().strip()
        if not freq_text:
            return None, None
        try:
            return float(freq_text), None
        except ValueError:
            return None, "Frequency must be a number."

    def handle_create(self):
        project_id = self.project_combo.currentData()
        if project_id is None:
            QMessageBox.warning(self, "No project selected", "Create a project first.")
            return
        title = self.title_input.text().strip()
        if not title:
            QMessageBox.warning(self, "Missing title", "Experiment title is required.")
            return
        freq, err = self._parse_freq()
        if err:
            QMessageBox.warning(self, "Invalid frequency", err)
            return
        instrument = self.instrument_input.text().strip() or None
        try:
            api_client.create_experiment(project_id, title, instrument=instrument, freq=freq)
        except api_client.APIError as e:
            QMessageBox.critical(self, "Error", f"Could not create experiment: {e.detail}")
            return
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Could not reach the API: {e}")
            return
        self.clear_form()
        self.refresh_experiments()

    def handle_update(self):
        if self.selected_experiment_id is None:
            QMessageBox.warning(self, "No selection", "Select an experiment in the table first.")
            return
        title = self.title_input.text().strip()
        if not title:
            QMessageBox.warning(self, "Missing title", "Experiment title is required.")
            return
        freq, err = self._parse_freq()
        if err:
            QMessageBox.warning(self, "Invalid frequency", err)
            return
        instrument = self.instrument_input.text().strip() or None
        try:
            api_client.update_experiment(self.selected_experiment_id, title, instrument=instrument, freq=freq)
        except api_client.APIError as e:
            QMessageBox.critical(self, "Error", f"Could not update experiment: {e.detail}")
            return
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Could not reach the API: {e}")
            return
        self.clear_form()
        self.refresh_experiments()

    def handle_delete(self):
        if self.selected_experiment_id is None:
            QMessageBox.warning(self, "No selection", "Select an experiment in the table first.")
            return
        confirm = QMessageBox.question(
            self, "Confirm delete",
            f"Delete experiment {self.selected_experiment_id}? This will also delete "
            "all its datasets and analysis results.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if confirm != QMessageBox.StandardButton.Yes:
            return
        try:
            api_client.delete_experiment(self.selected_experiment_id)
        except api_client.APIError as e:
            QMessageBox.critical(self, "Error", f"Could not delete experiment: {e.detail}")
            return
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Could not reach the API: {e}")
            return
        self.clear_form()
        self.refresh_experiments()