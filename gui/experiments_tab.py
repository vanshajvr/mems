from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QPushButton, QLineEdit, QLabel, QMessageBox, QHeaderView, QComboBox
)

import api_client


class ExperimentsTab(QWidget):
    def __init__(self):
        super().__init__()

        layout = QVBoxLayout()

        # -- Project selector --
        selector_layout = QHBoxLayout()
        selector_layout.addWidget(QLabel("Project:"))
        self.project_combo = QComboBox()
        # currentIndexChanged fires whenever the user picks a different
        # project -- that's what triggers reloading the experiments table
        self.project_combo.currentIndexChanged.connect(self.on_project_changed)
        selector_layout.addWidget(self.project_combo, stretch=1)
        refresh_button = QPushButton("Refresh Projects")
        refresh_button.clicked.connect(self.load_projects)
        selector_layout.addWidget(refresh_button)
        layout.addLayout(selector_layout)

        # -- Table of experiments for the selected project --
        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(["ID", "Title", "Instrument", "Freq (Hz)", "Notes"])
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeMode.Stretch)
        layout.addWidget(self.table)

        # -- Form to create a new experiment --
        form_layout = QHBoxLayout()
        self.title_input = QLineEdit()
        self.title_input.setPlaceholderText("Experiment title")
        self.instrument_input = QLineEdit()
        self.instrument_input.setPlaceholderText("Instrument (optional)")
        self.freq_input = QLineEdit()
        self.freq_input.setPlaceholderText("Freq Hz (optional)")
        create_button = QPushButton("Create Experiment")
        create_button.clicked.connect(self.handle_create)

        form_layout.addWidget(self.title_input)
        form_layout.addWidget(self.instrument_input)
        form_layout.addWidget(self.freq_input)
        form_layout.addWidget(create_button)
        layout.addLayout(form_layout)

        self.status_label = QLabel("")
        layout.addWidget(self.status_label)

        self.setLayout(layout)

        self.load_projects()

    def load_projects(self):
        """Populate the project dropdown. Each item's visible text is
        'id - name', but its stored data (currentData()) is just the
        integer id -- that's what we actually send to the API."""
        try:
            projects = api_client.get_projects()
        except Exception as e:
            self.status_label.setText(f"Failed to load projects: {e}")
            return

        # blockSignals prevents on_project_changed from firing repeatedly
        # while we're clearing and re-adding items one at a time
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

    def handle_create(self):
        project_id = self.project_combo.currentData()
        if project_id is None:
            QMessageBox.warning(self, "No project selected", "Create a project first.")
            return

        title = self.title_input.text().strip()
        if not title:
            QMessageBox.warning(self, "Missing title", "Experiment title is required.")
            return

        instrument = self.instrument_input.text().strip() or None

        freq_text = self.freq_input.text().strip()
        freq = None
        if freq_text:
            try:
                freq = float(freq_text)
            except ValueError:
                QMessageBox.warning(self, "Invalid frequency", "Frequency must be a number.")
                return

        try:
            api_client.create_experiment(project_id, title, instrument=instrument, freq=freq)
        except api_client.APIError as e:
            QMessageBox.critical(self, "Error", f"Could not create experiment: {e.detail}")
            return
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Could not reach the API: {e}")
            return

        self.title_input.clear()
        self.instrument_input.clear()
        self.freq_input.clear()
        self.refresh_experiments()