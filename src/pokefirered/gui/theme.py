"""
Modern, sleek dark-theme stylesheet and color palette for PokeRL Studio.
Inspired by modern developer IDEs and scientific analytics workstations.
Palette: Deep Obsidian (#0B0F17), Midnight Slate (#131B26), Card Dark (#1A2332),
Border Slate (#283548), Accent Cyan (#00E5FF), Emerald (#00E676), Amber (#FFD700), Crimson (#FF5252).
"""

DARK_THEME_QSS = """
QMainWindow {
    background-color: #0B0F17;
    color: #E2E8F0;
    font-family: 'Segoe UI', -apple-system, BlinkMacSystemFont, Roboto, sans-serif;
}

QWidget {
    color: #E2E8F0;
    font-size: 13px;
}

/* Sidebar styling */
#Sidebar {
    background-color: #0F1622;
    border-right: 1px solid #1E293B;
    min-width: 210px;
    max-width: 210px;
}

#SidebarTitle {
    color: #00E5FF;
    font-size: 17px;
    font-weight: 700;
    padding: 18px 12px 6px 16px;
    letter-spacing: 0.5px;
}

#SidebarSubtitle {
    color: #64748B;
    font-size: 11px;
    font-weight: 500;
    padding: 0px 12px 18px 16px;
    border-bottom: 1px solid #1E293B;
}

/* Navigation Buttons */
QPushButton.NavBtn {
    background-color: transparent;
    color: #94A3B8;
    text-align: left;
    padding: 12px 16px;
    border: none;
    border-radius: 6px;
    margin: 3px 8px;
    font-size: 13px;
    font-weight: 600;
}

QPushButton.NavBtn:hover {
    background-color: #1A2333;
    color: #F8FAFC;
}

QPushButton.NavBtn:checked {
    background-color: #1E293B;
    color: #00E5FF;
    border-left: 3px solid #00E5FF;
    font-weight: 700;
}

/* Cards & Containers */
QFrame.Card {
    background-color: #131B26;
    border: 1px solid #1E293B;
    border-radius: 8px;
    padding: 12px;
}

QFrame.Card:hover {
    border: 1px solid #334155;
}

QLabel.CardTitle {
    color: #64748B;
    font-size: 11px;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.8px;
}

QLabel.CardValue {
    color: #F8FAFC;
    font-size: 20px;
    font-weight: 700;
    margin-top: 2px;
}

QLabel.CardSub {
    color: #94A3B8;
    font-size: 11px;
    margin-top: 1px;
}

/* Action Buttons */
QPushButton.ActionBtnPrimary {
    background-color: #00B4D8;
    color: #050B14;
    font-weight: 700;
    border: none;
    border-radius: 6px;
    padding: 9px 18px;
    font-size: 13px;
}

QPushButton.ActionBtnPrimary:hover {
    background-color: #00E5FF;
}

QPushButton.ActionBtnPrimary:pressed {
    background-color: #0096C7;
}

QPushButton.ActionBtnSuccess {
    background-color: #059669;
    color: #FFFFFF;
    font-weight: 700;
    border: none;
    border-radius: 6px;
    padding: 9px 18px;
    font-size: 13px;
}

QPushButton.ActionBtnSuccess:hover {
    background-color: #10B981;
}

QPushButton.ActionBtnDanger {
    background-color: #DC2626;
    color: #FFFFFF;
    font-weight: 700;
    border: none;
    border-radius: 6px;
    padding: 9px 18px;
    font-size: 13px;
}

QPushButton.ActionBtnDanger:hover {
    background-color: #EF4444;
}

QPushButton.ActionBtnSecondary {
    background-color: #1E293B;
    color: #CBD5E1;
    font-weight: 600;
    border: 1px solid #334155;
    border-radius: 6px;
    padding: 8px 16px;
    font-size: 13px;
}

QPushButton.ActionBtnSecondary:hover {
    background-color: #334155;
    color: #FFFFFF;
}

/* Form Controls */
QLineEdit, QSpinBox, QDoubleSpinBox, QComboBox {
    background-color: #0F1622;
    border: 1px solid #334155;
    border-radius: 6px;
    padding: 7px 10px;
    color: #F8FAFC;
    selection-background-color: #00E5FF;
    selection-color: #0B0F17;
}

QLineEdit:focus, QSpinBox:focus, QComboBox:focus {
    border: 1px solid #00E5FF;
}

QComboBox::drop-down {
    border: none;
    padding-right: 8px;
}

QComboBox QAbstractItemView {
    background-color: #131B26;
    border: 1px solid #334155;
    selection-background-color: #1E293B;
    color: #F8FAFC;
}

/* Scrollbars */
QScrollBar:vertical {
    background-color: #0B0F17;
    width: 10px;
    margin: 0px;
}

QScrollBar::handle:vertical {
    background-color: #334155;
    min-height: 20px;
    border-radius: 5px;
}

QScrollBar::handle:vertical:hover {
    background-color: #475569;
}

QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    height: 0px;
}

/* Status Bar */
QStatusBar {
    background-color: #0F1622;
    border-top: 1px solid #1E293B;
    color: #94A3B8;
    font-size: 12px;
}

/* Progress Bar */
QProgressBar {
    background-color: #0F1622;
    border: 1px solid #1E293B;
    border-radius: 4px;
    text-align: center;
    color: #F8FAFC;
    font-size: 11px;
    font-weight: bold;
}

QProgressBar::chunk {
    background-color: #00E5FF;
    border-radius: 3px;
}

/* Log / Console */
QPlainTextEdit.LogConsole {
    background-color: #06090E;
    color: #A5F3FC;
    font-family: 'Consolas', 'Courier New', monospace;
    font-size: 12px;
    border: 1px solid #1E293B;
    border-radius: 6px;
    padding: 8px;
}
"""
