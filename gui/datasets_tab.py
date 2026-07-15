from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QPushButton, QLabel, QMessageBox, QHeaderView, QComboBox, QFileDialog
)

import api_client


class DatasetsTab(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout()

        selector_layout = QHBoxLayout()
        selector_layout.addWidget(QLabel("Experiment:"))
        self.experiment_combo = QComboBox()
        self.experiment_combo.currentIndexChanged.connect(self.on_experiment_changed)
        selector_layout.addWidget(self.experiment_combo, stretch=1)
        refresh_button = QPushButton("Refresh Experiments")
        refresh_button.clicked.connect(self.load_experiments)
        selector_layout.addWidget(refresh_button)
        layout.addLayout(selector_layout)

        self.table = QTableWidget()
        self.table.setColumnCount(3)
        self.table.setHorizontalHeaderLabels(["ID", "Filename", "Uploaded At"])
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.table.itemSelectionChanged.connect(self.on_selection_changed)
        layout.addWidget(self.table)


        self.table.setAlternatingRowColors(True)
        action_layout = QHBoxLayout()
        self.selected_file_label = QLabel("No file selected")
        browse_button = QPushButton("Browse CSV...")
        browse_button.clicked.connect(self.handle_browse)
        upload_button = QPushButton("Upload")
        upload_button.clicked.connect(self.handle_upload)
        delete_button = QPushButton("Delete Selected")
        delete_button.setObjectName("dangerButton")
        delete_button.clicked.connect(self.handle_delete)
        action_layout.addWidget(self.selected_file_label, stretch=1)
        action_layout.addWidget(browse_button)
        action_layout.addWidget(upload_button)
        action_layout.addWidget(delete_button)
        layout.addLayout(action_layout)

        self.status_label = QLabel("")
        layout.addWidget(self.status_label)

        self.setLayout(layout)

        self.selected_filepath = None
        self.selected_dataset_id = None
        self.load_experiments()

    def load_experiments(self):
        try:
            experiments = api_client.get_experiments()
        except Exception as e:
            self.status_label.setText(f"Failed to load experiments: {e}")
            return

        self.experiment_combo.blockSignals(True)
        self.experiment_combo.clear()
        for exp in experiments:
            self.experiment_combo.addItem(f"{exp['id']} - {exp['title']}", exp["id"])
        self.experiment_combo.blockSignals(False)

        if experiments:
            self.refresh_datasets()
        else:
            self.table.setRowCount(0)
            self.status_label.setText("No experiments yet -- create one in the Experiments tab first")

    def on_experiment_changed(self, index):
        self.refresh_datasets()

    def refresh_datasets(self):
        experiment_id = self.experiment_combo.currentData()
        if experiment_id is None:
            self.table.setRowCount(0)
            return

        try:
            datasets = api_client.get_datasets_for_experiment(experiment_id)
        except Exception as e:
            self.status_label.setText(f"Failed to load datasets: {e}")
            return

        self.table.setRowCount(len(datasets))
        for row, ds in enumerate(datasets):
            self.table.setItem(row, 0, QTableWidgetItem(str(ds["id"])))
            self.table.setItem(row, 1, QTableWidgetItem(ds["filename"]))
            self.table.setItem(row, 2, QTableWidgetItem(ds.get("uploaded_at") or ""))

        self.status_label.setText(f"{len(datasets)} dataset(s) loaded")
    
    def _item_text(self, row, col):
        item = self.table.item(row, col)
        return item.text() if item is not None else ""

    def on_selection_changed(self):
        selected_rows = self.table.selectionModel().selectedRows()
        if not selected_rows:
            self.selected_dataset_id = None
            return
        row = selected_rows[0].row()
        self.selected_dataset_id = int(self._item_text(row, 0))

    def handle_browse(self):
        filepath, _ = QFileDialog.getOpenFileName(self, "Select CSV file", "", "CSV Files (*.csv)")
        if filepath:
            self.selected_filepath = filepath
            self.selected_file_label.setText(filepath.split("/")[-1])

    def handle_upload(self):
        experiment_id = self.experiment_combo.currentData()
        if experiment_id is None:
            QMessageBox.warning(self, "No experiment selected", "Create an experiment first.")
            return
        if not self.selected_filepath:
            QMessageBox.warning(self, "No file selected", "Browse for a CSV file first.")
            return
        try:
            api_client.upload_dataset(experiment_id, self.selected_filepath)
        except api_client.APIError as e:
            QMessageBox.critical(self, "Error", f"Could not upload dataset: {e.detail}")
            return
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Could not reach the API: {e}")
            return
        self.selected_filepath = None
        self.selected_file_label.setText("No file selected")
        self.refresh_datasets()

    def handle_delete(self):
        if self.selected_dataset_id is None:
            QMessageBox.warning(self, "No selection", "Select a dataset in the table first.")
            return
        confirm = QMessageBox.question(
            self, "Confirm delete",
            f"Delete dataset {self.selected_dataset_id}? This will also delete "
            "its analysis result, if one exists.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if confirm != QMessageBox.StandardButton.Yes:
            return
        try:
            api_client.delete_dataset(self.selected_dataset_id)
        except api_client.APIError as e:
            QMessageBox.critical(self, "Error", f"Could not delete dataset: {e.detail}")
            return
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Could not reach the API: {e}")
            return
        self.selected_dataset_id = None
        self.refresh_datasets()