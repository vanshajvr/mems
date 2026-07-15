STYLESHEET = """
/* -- Base font, applied to everything unless overridden below -- */
QWidget {
    font-size: 14px;
}

/* -- Table & tree headers: bigger, bold, more padding than the body text -- */
QHeaderView::section {
    font-size: 15px;
    font-weight: 600;
    padding: 10px 8px;
    background-color: #2a2a2a;
    border: none;
    border-bottom: 2px solid #444;
}

/* -- Table/tree rows: taller, more breathing room per cell -- */
QTableWidget::item, QTreeWidget::item {
    padding: 8px;
}
QTableWidget, QTreeWidget {
    gridline-color: #3a3a3a;
    alternate-background-color: #262626;
}

/* -- Tabs: bigger click targets, clearer active-tab distinction -- */
QTabBar::tab {
    font-size: 14px;
    padding: 10px 24px;
    min-width: 100px;
}
QTabBar::tab:selected {
    font-weight: 600;
}

/* -- Buttons: consistent padding, rounded corners, hover feedback -- */
QPushButton {
    font-size: 13px;
    padding: 8px 16px;
    border-radius: 6px;
    border: 1px solid #555;
    background-color: #3a3a3a;
}
QPushButton:hover {
    background-color: #454545;
}
QPushButton:pressed {
    background-color: #2f2f2f;
}

/* -- Inputs & dropdowns: taller, easier to click, matching font size -- */
QLineEdit, QComboBox {
    font-size: 13px;
    padding: 6px 8px;
    min-height: 22px;
    border-radius: 4px;
    border: 1px solid #555;
}

/* -- Group boxes (used in Analysis tab): bold labeled section titles -- */
QGroupBox {
    font-size: 14px;
    font-weight: 600;
    margin-top: 12px;
    padding-top: 12px;
    border: 1px solid #444;
    border-radius: 6px;
}
QGroupBox::title {
    subcontrol-origin: margin;
    left: 10px;
    padding: 0 6px;
}

QPushButton#dangerButton {
    background-color: #5c2626;
    border-color: #8a3a3a;
}
QPushButton#dangerButton:hover {
    background-color: #6e2e2e;
}
"""