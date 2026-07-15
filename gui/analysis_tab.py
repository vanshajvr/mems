from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QComboBox,
    QMessageBox, QTreeWidget, QTreeWidgetItem, QGroupBox
)

import api_client


class AnalysisTab(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout()

        # -- Section 1: Run Analysis --
        # QGroupBox draws a labeled border around its contents -- useful
        # here since this tab genuinely has two separate features in it.
        run_box = QGroupBox("Run Analysis")
        run_layout = QVBoxLayout()

        run_selector = QHBoxLayout()
        run_selector.addWidget(QLabel("Dataset:"))
        self.dataset_combo = QComboBox()
        run_selector.addWidget(self.dataset_combo, stretch=1)
        refresh_ds_button = QPushButton("Refresh Datasets")
        refresh_ds_button.clicked.connect(self.load_datasets)
        run_selector.addWidget(refresh_ds_button)
        run_button = QPushButton("Run Analysis")
        run_button.clicked.connect(self.handle_run_analysis)
        run_selector.addWidget(run_button)
        run_layout.addLayout(run_selector)

        self.result_label = QLabel("No analysis run yet")
        self.result_label.setWordWrap(True)
        run_layout.addWidget(self.result_label)

        run_box.setLayout(run_layout)
        layout.addWidget(run_box)

        # -- Section 2: Full Project Report --
        report_box = QGroupBox("Full Project Report")
        report_layout = QVBoxLayout()

        report_selector = QHBoxLayout()
        report_selector.addWidget(QLabel("Project:"))
        self.project_combo = QComboBox()
        report_selector.addWidget(self.project_combo, stretch=1)
        refresh_proj_button = QPushButton("Refresh Projects")
        refresh_proj_button.clicked.connect(self.load_projects)
        report_selector.addWidget(refresh_proj_button)
        report_button = QPushButton("Get Report")
        report_button.clicked.connect(self.handle_get_report)
        report_selector.addWidget(report_button)
        report_layout.addLayout(report_selector)

        # QTreeWidget mirrors the report's actual nested shape --
        # project -> experiments -> datasets -> analysis -- as real
        # parent/child rows, instead of flattening it into a table.
        self.report_tree = QTreeWidget()
        self.report_tree.setHeaderLabels(["Item", "Details"])
        report_layout.addWidget(self.report_tree)

        report_box.setLayout(report_layout)
        layout.addWidget(report_box)

        self.setLayout(layout)

        self.load_datasets()
        self.load_projects()

    def load_datasets(self):
        try:
            datasets = api_client.get_datasets()
        except Exception as e:
            self.result_label.setText(f"Failed to load datasets: {e}")
            return
        self.dataset_combo.clear()
        for ds in datasets:
            self.dataset_combo.addItem(f"{ds['id']} - {ds['filename']}", ds["id"])

    def load_projects(self):
        try:
            projects = api_client.get_projects()
        except Exception:
            return
        self.project_combo.clear()
        for p in projects:
            self.project_combo.addItem(f"{p['id']} - {p['name']}", p["id"])

    def handle_run_analysis(self):
        dataset_id = self.dataset_combo.currentData()
        if dataset_id is None:
            QMessageBox.warning(self, "No dataset selected", "Upload a dataset first.")
            return

        try:
            result = api_client.run_analysis(dataset_id)
        except api_client.APIError as e:
            QMessageBox.critical(self, "Error", f"Analysis failed: {e.detail}")
            return
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Could not reach the API: {e}")
            return

        self.result_label.setText(
            f"Mean Cp: {result['mean_cp']:.6f}    "
            f"Std Dev: {result['std_dev']:.6f}    "
            f"Mean Loss: {result['mean_loss']:.6f}\n"
            f"Correlation: {result['correlation']:.4f}    "
            f"Expanded U: {result['expanded_u']:.6f}"
        )

    def handle_get_report(self):
        project_id = self.project_combo.currentData()
        if project_id is None:
            QMessageBox.warning(self, "No project selected", "Create a project first.")
            return

        try:
            report = api_client.get_project_report(project_id)
        except api_client.APIError as e:
            QMessageBox.critical(self, "Error", f"Could not load report: {e.detail}")
            return
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Could not reach the API: {e}")
            return

        self.report_tree.clear()

        # Build the tree exactly following the JSON's own nesting --
        # each addChild() call is one level deeper, matching
        # project -> experiments -> datasets -> analysis.
        project_item = QTreeWidgetItem([report["name"], report.get("desc") or ""])
        self.report_tree.addTopLevelItem(project_item)

        for exp in report.get("experiments", []):
            exp_item = QTreeWidgetItem([exp["title"], exp.get("instrument") or ""])
            project_item.addChild(exp_item)

            for ds in exp.get("datasets", []):
                ds_item = QTreeWidgetItem([ds["filename"], ""])
                exp_item.addChild(ds_item)
                
                analysis = ds.get("analysis")
                if analysis:
                    detail = (
                        f"Cp={analysis['mean_cp']:.6f}  "
                        f"std={analysis['std_dev']:.6f}  "
                        f"loss={analysis['mean_loss']:.6f}  "
                        f"corr={analysis['correlation']:.4f}  "
                        f"U={analysis['expanded_u']:.6f}"
                    )
                    ds_item.addChild(QTreeWidgetItem(["Analysis", detail]))
                else:
                    ds_item.addChild(QTreeWidgetItem(["Analysis", "not run yet"]))

        self.report_tree.expandAll()