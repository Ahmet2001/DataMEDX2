from __future__ import annotations

import html
import os
import re
import sys
import csv
import webbrowser
from datetime import datetime
from pathlib import Path
from typing import Any

import requests
from dotenv import load_dotenv

try:
    from PySide6.QtCore import QObject, QThread, QTimer, Qt, QUrl, Signal
    from PySide6.QtGui import QFont, QPalette, QTextDocument
    from PySide6.QtPrintSupport import QPrinter
    from PySide6.QtWidgets import (
        QApplication,
        QComboBox,
        QFileDialog,
        QFrame,
        QGridLayout,
        QGroupBox,
        QHBoxLayout,
        QLabel,
        QMainWindow,
        QMenuBar,
        QMessageBox,
        QPushButton,
        QScrollArea,
        QSizePolicy,
        QSlider,
        QSplitter,
        QStatusBar,
        QTabWidget,
        QTextBrowser,
        QTextEdit,
        QVBoxLayout,
        QWidget,
        QStyleFactory,
    )
except ModuleNotFoundError as exc:  # pragma: no cover - only hit before optional install.
    raise SystemExit(
        "PySide6 bulunamadı. Qt paneli için şu komutu çalıştır:\n"
        "  ./run_qt_doctor.sh\n"
        "veya:\n"
        "  .venv/bin/python -m pip install -r requirements-qt.txt"
    ) from exc


try:
    from PySide6.QtWebEngineWidgets import QWebEngineView
except Exception:  # pragma: no cover - optional Qt module.
    QWebEngineView = None


PROJECT_ROOT = Path(__file__).resolve().parents[1]
load_dotenv(PROJECT_ROOT / ".env", override=False)

API_BASE = os.getenv("DATAMEDX_API_BASE", "http://127.0.0.1:8001").rstrip("/")
APP_TITLE = "DataMedX Doctor Workstation"


def escape(value: Any) -> str:
    return html.escape(str(value or ""), quote=True)


def markdown_to_html(text: str) -> str:
    lines = str(text or "").splitlines()
    output: list[str] = []
    in_list = False

    def close_list() -> None:
        nonlocal in_list
        if in_list:
            output.append("</ul>")
            in_list = False

    for raw in lines:
        line = raw.rstrip()
        stripped = line.strip()
        if not stripped:
            close_list()
            continue
        heading = re.match(r"^(#{1,3})\s+(.+)$", stripped)
        if heading:
            close_list()
            level = min(3, len(heading.group(1)))
            output.append(f"<h{level}>{format_inline(heading.group(2))}</h{level}>")
            continue
        bullet = re.match(r"^[-*]\s+(.+)$", stripped)
        if bullet:
            if not in_list:
                output.append("<ul>")
                in_list = True
            output.append(f"<li>{format_inline(bullet.group(1))}</li>")
            continue
        close_list()
        output.append(f"<p>{format_inline(stripped)}</p>")

    close_list()
    return "\n".join(output)


def format_inline(text: str) -> str:
    value = escape(text)
    value = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", value)
    value = re.sub(r"`([^`]+)`", r"<code>\1</code>", value)
    return value


def clean_compact(value: Any, max_chars: int = 80) -> str:
    text = str(value or "").replace("_x000D_", " ").replace("\xa0", " ")
    bracketed = re.findall(r"\[([^\[\]]*?)\]", text, flags=re.S)
    if bracketed:
        text = bracketed[0]
    text = re.sub(r"\s+", " ", text).strip()
    if len(text) > max_chars:
        return text[: max(0, max_chars - 3)].rstrip() + "..."
    return text


def health_data_csv_path() -> Path:
    env_path = os.getenv("HEALTH_DATA_CSV")
    if env_path:
        return Path(env_path).expanduser().resolve()
    return PROJECT_ROOT.parent / "hackathon_veri.csv"


def load_patient_choices() -> list[dict[str, str]]:
    path = health_data_csv_path()
    if not path.exists():
        return []

    choices: list[dict[str, str]] = []
    seen: set[str] = set()
    with path.open("r", encoding="utf-8-sig", newline="") as file:
        reader = csv.DictReader(file)
        for row in reader:
            no = clean_compact(row.get("No"), 24)
            record_id = clean_compact(row.get("id"), 48)
            client_id = clean_compact(row.get("client_id"), 48)
            key = no or client_id or record_id
            if not key or key in seen:
                continue
            seen.add(key)
            gender = clean_compact(row.get("cinsiyet"), 24)
            birth = clean_compact(row.get("doğum tarihi"), 24)
            department = clean_compact(row.get("department"), 42)
            label_parts = [f"No {no}" if no else "", client_id or record_id, gender, birth]
            label = " | ".join(part for part in label_parts if part)
            choices.append(
                {
                    "no": no,
                    "id": record_id,
                    "client_id": client_id,
                    "gender": gender,
                    "birth": birth,
                    "department": department,
                    "label": label or key,
                    "lookup_id": no or client_id or record_id,
                }
            )
    return choices


class ChatWorker(QObject):
    finished = Signal(dict)
    failed = Signal(str)

    def __init__(self, prompt: str, patient_id: str = ""):
        super().__init__()
        self.prompt = prompt
        self.patient_id = patient_id

    def run(self) -> None:
        try:
            response = requests.post(
                f"{API_BASE}/api/doctor/chat",
                json={
                    "prompt": self.prompt,
                    "patient_id": self.patient_id,
                    "output_style": "qt_doctor_panel",
                },
                timeout=180,
            )
            response.raise_for_status()
            self.finished.emit(response.json())
        except Exception as exc:
            self.failed.emit(str(exc))


class MetricBox(QFrame):
    def __init__(self, title: str, value: str = "0", note: str = ""):
        super().__init__()
        self.setObjectName("metricBox")
        self.setFrameShape(QFrame.Panel)
        self.setFrameShadow(QFrame.Sunken)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 6, 8, 6)
        layout.setSpacing(2)
        self.value_label = QLabel(value)
        self.value_label.setObjectName("metricValue")
        self.title_label = QLabel(title)
        self.title_label.setObjectName("metricTitle")
        self.note_label = QLabel(note)
        self.note_label.setObjectName("metricNote")
        self.note_label.setWordWrap(True)
        layout.addWidget(self.value_label)
        layout.addWidget(self.title_label)
        layout.addWidget(self.note_label)

    def set_metric(self, value: str, note: str = "") -> None:
        self.value_label.setText(value)
        self.note_label.setText(note)


class OrchestrationWindow(QMainWindow):
    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        self.setWindowTitle("DataMedX Orchestration Command Center")
        self.resize(1180, 760)
        self.setMinimumSize(900, 620)

        root = QWidget()
        layout = QVBoxLayout(root)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(8)

        header = QFrame()
        header.setFrameShape(QFrame.Panel)
        header.setFrameShadow(QFrame.Sunken)
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(8, 5, 8, 5)
        title = QLabel("Orchestration")
        title.setObjectName("windowHeader")
        self.url_label = QLabel(f"{API_BASE}/panel")
        self.url_label.setObjectName("mutedLabel")
        self.reload_button = QPushButton("Reload")
        self.reload_button.clicked.connect(self.reload_panel)
        self.browser_button = QPushButton("Open Browser")
        self.browser_button.clicked.connect(lambda: webbrowser.open(f"{API_BASE}/panel"))
        header_layout.addWidget(title)
        header_layout.addWidget(self.url_label, 1)
        header_layout.addWidget(self.reload_button)
        header_layout.addWidget(self.browser_button)
        layout.addWidget(header)

        if QWebEngineView is None:
            fallback = QTextBrowser()
            fallback.setHtml(
                "<p><b>Qt WebEngine bulunamadı.</b></p>"
                f"<p>Komuta merkezi için tarayıcıda aç: <code>{escape(API_BASE)}/panel</code></p>"
            )
            layout.addWidget(fallback, 1)
            self.web_view = None
        else:
            self.web_view = QWebEngineView()
            self.web_view.setUrl(QUrl(f"{API_BASE}/panel"))
            layout.addWidget(self.web_view, 1)

        self.setCentralWidget(root)
        self.setStatusBar(QStatusBar())
        self.statusBar().showMessage("Command center ready.")

    def reload_panel(self) -> None:
        if self.web_view is not None:
            self.web_view.setUrl(QUrl(f"{API_BASE}/panel"))
            self.web_view.reload()
            self.statusBar().showMessage("Command center reloaded.")


class DataMedXQtDoctor(QMainWindow):
    def __init__(self):
        super().__init__()
        self.payload: dict[str, Any] = {}
        self.clinical_panel: dict[str, Any] = {}
        self.report_markdown = ""
        self.worker_thread: QThread | None = None
        self.patient_choices = load_patient_choices()
        self.selected_patient_index: int | None = None
        self._syncing_patient_controls = False
        self._active_patient_prompt_prefix = ""
        self._last_auto_prompt = ""
        self.orchestration_window: OrchestrationWindow | None = None

        self.setWindowTitle(APP_TITLE)
        self.resize(1380, 820)
        self.setMinimumSize(1100, 680)
        self._build_menu()
        self._build_ui()
        self._apply_classic_style()
        self._setup_status_timer()

    def _build_menu(self) -> None:
        menu = QMenuBar(self)
        file_menu = menu.addMenu("&File")
        file_menu.addAction("Save Report...", self.save_markdown_report)
        file_menu.addSeparator()
        file_menu.addAction("Exit", self.close)

        tools_menu = menu.addMenu("&Tools")
        tools_menu.addAction("Check Backend Status", self.check_backend_status)
        tools_menu.addAction("Demo Prompt", self.fill_demo_prompt)

        orchestration_menu = menu.addMenu("&Orchestration")
        orchestration_menu.addAction("Open Command Center", self.open_orchestration_center)
        orchestration_menu.addAction("Open Web Panel in Browser", lambda: webbrowser.open(f"{API_BASE}/panel"))

        help_menu = menu.addMenu("&Help")
        help_menu.addAction("About", self.show_about)
        self.setMenuBar(menu)

    def _build_ui(self) -> None:
        root = QWidget()
        root_layout = QVBoxLayout(root)
        root_layout.setContentsMargins(8, 8, 8, 8)
        root_layout.setSpacing(8)

        header = self._sunken_frame()
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(10, 6, 10, 6)
        title = QLabel("DataMedX Clinical Decision Support Workstation")
        title.setObjectName("windowHeader")
        self.backend_status = QLabel("BACKEND: CHECKING")
        self.backend_status.setObjectName("statusLamp")
        header_layout.addWidget(title)
        header_layout.addStretch(1)
        header_layout.addWidget(self.backend_status)
        root_layout.addWidget(header)

        splitter = QSplitter(Qt.Horizontal)
        splitter.setChildrenCollapsible(False)
        splitter.addWidget(self._build_prompt_panel())
        splitter.addWidget(self._build_answer_panel())
        splitter.addWidget(self._build_audit_panel())
        splitter.setSizes([330, 560, 520])
        root_layout.addWidget(splitter, 1)

        self.setCentralWidget(root)
        self.setStatusBar(QStatusBar())
        self.statusBar().showMessage(f"Ready. API: {API_BASE}")

    def _build_prompt_panel(self) -> QWidget:
        box = QGroupBox("Clinical Request")
        layout = QVBoxLayout(box)
        layout.setContentsMargins(10, 14, 10, 10)
        layout.setSpacing(8)

        help_label = QLabel("Serbest doktor prompt'u. Hasta kodu otomatik yakalanır.")
        help_label.setWordWrap(True)
        help_label.setObjectName("mutedLabel")

        patient_selector = QGroupBox("Hasta Seçimi")
        patient_layout = QVBoxLayout(patient_selector)
        patient_layout.setContentsMargins(8, 12, 8, 8)
        patient_layout.setSpacing(6)

        self.patient_combo = QComboBox()
        self.patient_combo.setObjectName("classicCombo")
        self.patient_combo.setEditable(True)
        self.patient_combo.setInsertPolicy(QComboBox.NoInsert)
        self.patient_combo.addItem("Serbest prompt / hasta seçilmedi", None)
        for patient in self.patient_choices:
            self.patient_combo.addItem(patient["label"], patient)
        self.patient_combo.setEnabled(bool(self.patient_choices))
        self.patient_combo.currentIndexChanged.connect(self.on_patient_combo_changed)

        self.patient_slider = QSlider(Qt.Horizontal)
        self.patient_slider.setObjectName("classicSlider")
        self.patient_slider.setMinimum(0)
        self.patient_slider.setMaximum(max(0, len(self.patient_choices) - 1))
        self.patient_slider.setSingleStep(1)
        self.patient_slider.setPageStep(1)
        self.patient_slider.setTickPosition(QSlider.TicksBelow)
        self.patient_slider.setTickInterval(max(1, len(self.patient_choices) // 20) if self.patient_choices else 1)
        self.patient_slider.setEnabled(bool(self.patient_choices))
        self.patient_slider.valueChanged.connect(self.on_patient_slider_changed)

        nav_row = QHBoxLayout()
        self.prev_patient_button = QPushButton("<<")
        self.prev_patient_button.clicked.connect(lambda: self.move_patient(-1))
        self.next_patient_button = QPushButton(">>")
        self.next_patient_button.clicked.connect(lambda: self.move_patient(1))
        self.prev_patient_button.setEnabled(bool(self.patient_choices))
        self.next_patient_button.setEnabled(bool(self.patient_choices))
        self.patient_nav_label = QLabel()
        self.patient_nav_label.setObjectName("mutedLabel")
        self.patient_nav_label.setWordWrap(True)
        nav_row.addWidget(self.prev_patient_button)
        nav_row.addWidget(self.patient_nav_label, 1)
        nav_row.addWidget(self.next_patient_button)

        patient_layout.addWidget(self.patient_combo)
        patient_layout.addWidget(self.patient_slider)
        patient_layout.addLayout(nav_row)
        self._refresh_patient_nav_label()

        self.prompt_edit = QTextEdit()
        self.prompt_edit.setObjectName("classicTextEdit")
        self.prompt_edit.setPlaceholderText(
            "Örn: No 501 hastasını kısa özetle; kritik riskleri, kanıtları ve timeline'ı göster."
        )
        self.prompt_edit.setMinimumHeight(245)

        self.send_button = QPushButton("&Send to Agent")
        self.send_button.clicked.connect(self.send_prompt)
        self.demo_button = QPushButton("&Demo Prompt")
        self.demo_button.clicked.connect(self.fill_demo_prompt)
        self.clear_button = QPushButton("&Clear")
        self.clear_button.clicked.connect(self.clear_all)

        button_row = QGridLayout()
        button_row.addWidget(self.send_button, 0, 0, 1, 2)
        button_row.addWidget(self.demo_button, 1, 0)
        button_row.addWidget(self.clear_button, 1, 1)

        note = QLabel(
            "Kabul edilen örnekler: ADN_10016905, L1_ADN_10016905, "
            "adn-10016905, No 501, 501 nolu hasta."
        )
        note.setWordWrap(True)
        note.setObjectName("mutedLabel")

        layout.addWidget(help_label)
        layout.addWidget(patient_selector)
        layout.addWidget(self.prompt_edit, 1)
        layout.addLayout(button_row)
        layout.addWidget(note)
        return box

    def _build_answer_panel(self) -> QWidget:
        box = QGroupBox("Live Clinical Response")
        layout = QVBoxLayout(box)
        layout.setContentsMargins(10, 14, 10, 10)
        layout.setSpacing(8)

        toolbar = QHBoxLayout()
        self.copy_button = QPushButton("Copy Answer")
        self.copy_button.clicked.connect(self.copy_answer)
        self.copy_button.setEnabled(False)
        toolbar.addWidget(self.copy_button)
        toolbar.addStretch(1)

        self.answer_browser = QTextBrowser()
        self.answer_browser.setObjectName("classicBrowser")
        self.answer_browser.setOpenExternalLinks(True)
        self.answer_browser.setHtml(
            "<p><b>DataMedX:</b> Doktor prompt'unu yazıp agent'a gönder.</p>"
        )

        layout.addLayout(toolbar)
        layout.addWidget(self.answer_browser, 1)
        return box

    def _build_audit_panel(self) -> QWidget:
        box = QGroupBox("Clinical Audit Panel")
        layout = QVBoxLayout(box)
        layout.setContentsMargins(10, 14, 10, 10)
        layout.setSpacing(8)
        box.setMinimumWidth(420)

        self.patient_label = QLabel("Patient: waiting")
        self.patient_label.setObjectName("patientStrip")
        self.patient_label.setWordWrap(True)

        metric_grid = QGridLayout()
        self.metric_boxes = {
            "Kanıt": MetricBox("Kanıt", "0", "source/snippet"),
            "Risk": MetricBox("Risk", "0", "clinical warning"),
            "Timeline": MetricBox("Timeline", "0", "event"),
            "Rapor": MetricBox("Rapor", "-", "one click"),
        }
        for index, item in enumerate(self.metric_boxes.values()):
            metric_grid.addWidget(item, index // 2, index % 2)

        self.impact_label = QLabel(
            "Önce: Manuel dosya okuma 10-15 dk\n"
            "Sonra: DataMedX kanıtlı özet, risk ve rapor."
        )
        self.impact_label.setObjectName("impactStrip")
        self.impact_label.setWordWrap(True)

        self.quality_box = QGroupBox("Data Quality")
        self.quality_layout = QVBoxLayout(self.quality_box)
        self.quality_layout.setContentsMargins(8, 12, 8, 8)
        self.quality_summary = QLabel("Hasta kaydı doğrulanınca uç değer kontrolü yapılır.")
        self.quality_summary.setWordWrap(True)
        self.quality_layout.addWidget(self.quality_summary)

        audit_summary_content = QWidget()
        audit_summary_content.setObjectName("auditSummaryContent")
        audit_summary_layout = QVBoxLayout(audit_summary_content)
        audit_summary_layout.setContentsMargins(4, 4, 4, 4)
        audit_summary_layout.setSpacing(8)
        audit_summary_layout.addWidget(self.patient_label)
        audit_summary_layout.addLayout(metric_grid)
        audit_summary_layout.addWidget(self.impact_label)
        audit_summary_layout.addWidget(self.quality_box)
        audit_summary_layout.addStretch(1)

        audit_summary_area = QScrollArea()
        audit_summary_area.setObjectName("auditSummaryScroll")
        audit_summary_area.setWidgetResizable(True)
        audit_summary_area.setMinimumHeight(170)
        audit_summary_area.setMaximumHeight(280)
        audit_summary_area.setWidget(audit_summary_content)

        self.tabs = QTabWidget()
        self.evidence_area, self.evidence_layout = self._scroll_layout()
        self.risk_area, self.risk_layout = self._scroll_layout()
        self.timeline_area, self.timeline_layout = self._scroll_layout()
        self.tabs.setMinimumHeight(360)
        self.report_edit = QTextEdit()
        self.report_edit.setReadOnly(True)
        self.report_edit.setObjectName("classicTextEdit")
        self.report_edit.setPlainText("Rapor için hasta ID içeren bir prompt gönder.")

        report_tab = QWidget()
        report_layout = QVBoxLayout(report_tab)
        report_buttons = QHBoxLayout()
        self.save_md_button = QPushButton("Save .MD")
        self.save_md_button.clicked.connect(self.save_markdown_report)
        self.save_md_button.setEnabled(False)
        self.save_pdf_button = QPushButton("Export PDF")
        self.save_pdf_button.clicked.connect(self.export_pdf_report)
        self.save_pdf_button.setEnabled(False)
        report_buttons.addWidget(self.save_md_button)
        report_buttons.addWidget(self.save_pdf_button)
        report_buttons.addStretch(1)
        report_layout.addLayout(report_buttons)
        report_layout.addWidget(self.report_edit, 1)

        self.tabs.addTab(self.evidence_area, "Kanıt")
        self.tabs.addTab(self.risk_area, "Risk")
        self.tabs.addTab(self.timeline_area, "Timeline")
        self.tabs.addTab(report_tab, "Rapor")

        layout.addWidget(audit_summary_area, 0)
        layout.addWidget(self.tabs, 1)
        return box

    def _scroll_layout(self) -> tuple[QScrollArea, QVBoxLayout]:
        area = QScrollArea()
        area.setWidgetResizable(True)
        content = QWidget()
        layout = QVBoxLayout(content)
        layout.setContentsMargins(6, 6, 6, 6)
        layout.setSpacing(6)
        layout.addStretch(1)
        area.setWidget(content)
        return area, layout

    def _sunken_frame(self) -> QFrame:
        frame = QFrame()
        frame.setFrameShape(QFrame.Panel)
        frame.setFrameShadow(QFrame.Sunken)
        return frame

    def _apply_classic_style(self) -> None:
        QApplication.setStyle(QStyleFactory.create("Windows") or QApplication.style())
        QApplication.setFont(QFont("MS Sans Serif", 9))

        palette = QApplication.palette()
        palette.setColor(QPalette.Window, Qt.lightGray)
        palette.setColor(QPalette.Button, Qt.lightGray)
        palette.setColor(QPalette.Base, Qt.white)
        palette.setColor(QPalette.Text, Qt.black)
        palette.setColor(QPalette.ButtonText, Qt.black)
        QApplication.setPalette(palette)

        self.setStyleSheet(
            """
            QWidget {
                background: #c0c0c0;
                color: #000000;
                font-family: "MS Sans Serif", "Tahoma", sans-serif;
                font-size: 9pt;
            }
            QMenuBar, QMenu {
                background: #c0c0c0;
                border: 1px solid #808080;
            }
            QGroupBox {
                border: 2px groove #f0f0f0;
                margin-top: 8px;
                padding-top: 8px;
                font-weight: bold;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 8px;
                padding: 0 3px;
            }
            QPushButton {
                min-height: 25px;
                background: #c0c0c0;
                border-top: 2px solid #ffffff;
                border-left: 2px solid #ffffff;
                border-right: 2px solid #404040;
                border-bottom: 2px solid #404040;
                padding: 3px 9px;
            }
            QPushButton:pressed {
                border-top: 2px solid #404040;
                border-left: 2px solid #404040;
                border-right: 2px solid #ffffff;
                border-bottom: 2px solid #ffffff;
                padding-top: 5px;
                padding-left: 11px;
            }
            QPushButton:disabled {
                color: #808080;
            }
            QTextEdit, QTextBrowser, QScrollArea {
                background: #ffffff;
                border-top: 2px solid #404040;
                border-left: 2px solid #404040;
                border-right: 2px solid #ffffff;
                border-bottom: 2px solid #ffffff;
            }
            #auditSummaryScroll, #auditSummaryContent {
                background: #c0c0c0;
            }
            QComboBox {
                min-height: 24px;
                background: #ffffff;
                border-top: 2px solid #404040;
                border-left: 2px solid #404040;
                border-right: 2px solid #ffffff;
                border-bottom: 2px solid #ffffff;
                padding: 2px 6px;
            }
            QComboBox QAbstractItemView {
                background: #ffffff;
                selection-background-color: #000080;
                selection-color: #ffffff;
            }
            QSlider::groove:horizontal {
                height: 6px;
                background: #808080;
                border-top: 1px solid #404040;
                border-left: 1px solid #404040;
                border-right: 1px solid #ffffff;
                border-bottom: 1px solid #ffffff;
            }
            QSlider::handle:horizontal {
                width: 16px;
                margin: -6px 0;
                background: #c0c0c0;
                border-top: 2px solid #ffffff;
                border-left: 2px solid #ffffff;
                border-right: 2px solid #404040;
                border-bottom: 2px solid #404040;
            }
            QTabWidget::pane {
                border: 2px groove #f0f0f0;
                background: #c0c0c0;
            }
            QTabBar::tab {
                background: #c0c0c0;
                border: 1px solid #808080;
                padding: 5px 9px;
            }
            QTabBar::tab:selected {
                background: #dcdcdc;
                border-bottom: 1px solid #dcdcdc;
            }
            QSplitter::handle {
                background: #808080;
            }
            #windowHeader {
                font-weight: bold;
                font-size: 10pt;
            }
            #statusLamp, #patientStrip, #impactStrip {
                border-top: 2px solid #404040;
                border-left: 2px solid #404040;
                border-right: 2px solid #ffffff;
                border-bottom: 2px solid #ffffff;
                background: #dcdcdc;
                padding: 5px;
            }
            #metricBox {
                background: #dcdcdc;
            }
            #metricValue {
                font-size: 16pt;
                font-weight: bold;
            }
            #metricTitle {
                color: #000080;
                font-weight: bold;
            }
            #metricNote, #mutedLabel {
                color: #404040;
            }
            """
        )

    def _setup_status_timer(self) -> None:
        self.status_timer = QTimer(self)
        self.status_timer.timeout.connect(self.check_backend_status)
        self.status_timer.start(15000)
        self.check_backend_status()

    def check_backend_status(self) -> None:
        try:
            response = requests.get(f"{API_BASE}/api/system/status", timeout=2)
            response.raise_for_status()
            data = response.json()
            model = data.get("model") or "unknown"
            self.backend_status.setText(f"BACKEND: ONLINE | {model}")
            self.backend_status.setStyleSheet("background: #008000; color: #ffffff; padding: 4px;")
        except Exception:
            self.backend_status.setText("BACKEND: OFFLINE")
            self.backend_status.setStyleSheet("background: #800000; color: #ffffff; padding: 4px;")

    def open_orchestration_center(self) -> None:
        if self.orchestration_window is None:
            self.orchestration_window = OrchestrationWindow(self)
        self.orchestration_window.show()
        self.orchestration_window.raise_()
        self.orchestration_window.activateWindow()

    def on_patient_combo_changed(self, index: int) -> None:
        if self._syncing_patient_controls:
            return
        if index <= 0:
            self.selected_patient_index = None
            self._active_patient_prompt_prefix = ""
            self._refresh_patient_nav_label()
            return
        self._select_patient(index - 1)

    def on_patient_slider_changed(self, value: int) -> None:
        if self._syncing_patient_controls or not self.patient_choices:
            return
        self._select_patient(value)

    def move_patient(self, delta: int) -> None:
        if not self.patient_choices:
            return
        current = self.selected_patient_index
        if current is None:
            current = self.patient_slider.value()
        self._select_patient(current + delta)

    def _select_patient(self, index: int) -> None:
        if not self.patient_choices:
            return
        index = max(0, min(index, len(self.patient_choices) - 1))
        self.selected_patient_index = index

        self._syncing_patient_controls = True
        self.patient_slider.setValue(index)
        self.patient_combo.setCurrentIndex(index + 1)
        self._syncing_patient_controls = False

        patient = self.patient_choices[index]
        self._refresh_patient_nav_label()
        self._apply_patient_to_prompt(patient)
        self.statusBar().showMessage(f"Hasta seçildi: {patient.get('label', '-')}")

    def _find_patient_index(self, needle: str) -> int | None:
        folded = needle.strip().lower()
        for index, patient in enumerate(self.patient_choices):
            values = [
                patient.get("no", ""),
                patient.get("id", ""),
                patient.get("client_id", ""),
                patient.get("lookup_id", ""),
            ]
            if any(str(value).strip().lower() == folded for value in values):
                return index
        return None

    def _refresh_patient_nav_label(self) -> None:
        if not hasattr(self, "patient_nav_label"):
            return
        if not self.patient_choices:
            self.patient_nav_label.setText(
                f"CSV hasta listesi bulunamadı: {health_data_csv_path()}"
            )
            return
        if self.selected_patient_index is None:
            self.patient_nav_label.setText(f"{len(self.patient_choices)} hasta yüklendi. Slider veya box ile seç.")
            return
        patient = self.patient_choices[self.selected_patient_index]
        detail = " | ".join(
            part
            for part in [
                f"{self.selected_patient_index + 1}/{len(self.patient_choices)}",
                patient.get("client_id") or patient.get("id"),
                patient.get("gender"),
                patient.get("birth"),
                patient.get("department"),
            ]
            if part
        )
        self.patient_nav_label.setText(detail)

    def selected_patient_identifier(self) -> str:
        if self.selected_patient_index is None or not self.patient_choices:
            return ""
        patient = self.patient_choices[self.selected_patient_index]
        return patient.get("lookup_id") or patient.get("client_id") or patient.get("id") or ""

    def _patient_prompt_prefix(self, patient: dict[str, str]) -> str:
        if patient.get("no"):
            return f"No {patient['no']}"
        return patient.get("client_id") or patient.get("id") or patient.get("lookup_id") or "Hasta"

    def _default_prompt_for_patient(self, patient: dict[str, str]) -> str:
        prefix = self._patient_prompt_prefix(patient)
        return (
            f"{prefix} hastasını kısa özetle; kritik riskleri, kanıtları, veri kalite uyarılarını "
            "ve timeline'ı göster. SBAR raporu da hazırla."
        )

    def _apply_patient_to_prompt(self, patient: dict[str, str]) -> None:
        prefix = self._patient_prompt_prefix(patient)
        text = self.prompt_edit.toPlainText().strip()
        if not text or text == self._last_auto_prompt:
            new_text = self._default_prompt_for_patient(patient)
        elif self._active_patient_prompt_prefix and self._active_patient_prompt_prefix in text:
            new_text = text.replace(self._active_patient_prompt_prefix, prefix, 1)
        elif re.match(r"^\s*(?:No\s+\d{1,8}|(?:L1_)?[A-Z]{2,5}[_-]\d{3,}|\d{1,8})\b", text, flags=re.I):
            new_text = re.sub(
                r"^\s*(?:No\s+\d{1,8}|(?:L1_)?[A-Z]{2,5}[_-]\d{3,}|\d{1,8})\b",
                prefix,
                text,
                count=1,
                flags=re.I,
            )
        elif prefix in text:
            new_text = text
        else:
            new_text = f"{prefix} için {text}"

        self.prompt_edit.setPlainText(new_text)
        self._active_patient_prompt_prefix = prefix
        self._last_auto_prompt = new_text

    def fill_demo_prompt(self) -> None:
        demo_index = self._find_patient_index("501")
        if demo_index is not None:
            self._select_patient(demo_index)
            return
        self.prompt_edit.setPlainText(
            "No 501 hastasını kısa özetle; kritik riskleri, kanıtları, veri kalite uyarılarını "
            "ve timeline'ı göster. SBAR raporu da hazırla."
        )
        self._last_auto_prompt = self.prompt_edit.toPlainText()

    def clear_all(self) -> None:
        self.prompt_edit.clear()
        self.answer_browser.setHtml("<p><b>DataMedX:</b> Yeni klinik istek bekleniyor.</p>")
        self.copy_button.setEnabled(False)
        self.payload = {}
        self.clinical_panel = {}
        self.report_markdown = ""
        self.selected_patient_index = None
        self._active_patient_prompt_prefix = ""
        self._last_auto_prompt = ""
        if self.patient_choices:
            self._syncing_patient_controls = True
            self.patient_combo.setCurrentIndex(0)
            self.patient_slider.setValue(0)
            self._syncing_patient_controls = False
            self._refresh_patient_nav_label()
        self.patient_label.setText("Patient: waiting")
        self._render_metrics([])
        self._render_quality({})
        self._render_cards(self.evidence_layout, [], "Kanıt bekleniyor.")
        self._render_cards(self.risk_layout, [], "Risk kartı bekleniyor.")
        self._render_timeline([])
        self.report_edit.setPlainText("Rapor için hasta ID içeren bir prompt gönder.")
        self.save_md_button.setEnabled(False)
        self.save_pdf_button.setEnabled(False)
        self.statusBar().showMessage("Ready.")

    def send_prompt(self) -> None:
        if self.selected_patient_index is not None and not self.prompt_edit.toPlainText().strip():
            self._apply_patient_to_prompt(self.patient_choices[self.selected_patient_index])
        prompt = self.prompt_edit.toPlainText().strip()
        if not prompt:
            QMessageBox.warning(self, "Empty prompt", "Doktor prompt'u boş olamaz.")
            return
        if self.worker_thread and self.worker_thread.isRunning():
            return

        self.send_button.setEnabled(False)
        self.statusBar().showMessage("Agent orchestration running...")
        self.answer_browser.setHtml("<p><b>DataMedX:</b> Agentlar çalışıyor...</p>")

        self.worker_thread = QThread(self)
        self.worker = ChatWorker(prompt, self.selected_patient_identifier())
        self.worker.moveToThread(self.worker_thread)
        self.worker_thread.started.connect(self.worker.run)
        self.worker.finished.connect(self._handle_payload)
        self.worker.failed.connect(self._handle_error)
        self.worker.finished.connect(self.worker_thread.quit)
        self.worker.failed.connect(self.worker_thread.quit)
        self.worker_thread.finished.connect(self.worker.deleteLater)
        self.worker_thread.finished.connect(lambda: self.send_button.setEnabled(True))
        self.worker_thread.start()

    def _handle_payload(self, payload: dict) -> None:
        self.payload = payload
        answer = payload.get("answer") or "Yanıt üretilemedi."
        self.answer_browser.setHtml(markdown_to_html(answer))
        self.copy_button.setEnabled(bool(answer))
        self.clinical_panel = payload.get("clinical_panel") or {}
        self._render_clinical_panel(self.clinical_panel)
        self.check_backend_status()
        self.statusBar().showMessage("Completed.")

    def _handle_error(self, message: str) -> None:
        self.answer_browser.setHtml(f"<p><b>Error:</b> {escape(message)}</p>")
        self.statusBar().showMessage("Error.")
        QMessageBox.critical(self, "Agent error", message)

    def _render_clinical_panel(self, panel: dict[str, Any]) -> None:
        status = panel.get("status") or "empty"
        if status == "ready":
            risk = panel.get("risk_summary") or {}
            self.patient_label.setText(
                f"Patient: {panel.get('patient_id') or '-'} | "
                f"Record: {panel.get('record_id') or '-'} | "
                f"{risk.get('red', 0)} red / {risk.get('yellow', 0)} yellow / {risk.get('green', 0)} green"
            )
        else:
            self.patient_label.setText(panel.get("message") or "Patient: waiting")

        self._render_metrics(panel.get("demo_metrics") or [])
        impact = panel.get("impact") or {}
        self.impact_label.setText(
            f"Önce: {impact.get('before') or 'Manuel dosya okuma: 10-15 dk'}\n"
            f"Sonra: {impact.get('after') or 'DataMedX: kanıtlı özet, risk ve rapor'}"
        )
        self._render_quality(panel.get("data_quality") or {})
        self._render_cards(self.evidence_layout, panel.get("evidence") or [], "Kanıt bulunamadı.")
        self._render_cards(self.risk_layout, panel.get("risk_cards") or [], "Risk sinyali yok.")
        self._render_timeline(panel.get("timeline") or [])

        self.report_markdown = panel.get("report_markdown") or ""
        self.report_edit.setPlainText(self.report_markdown or "Rapor için hasta ID içeren bir prompt gönder.")
        enabled = bool(self.report_markdown)
        self.save_md_button.setEnabled(enabled)
        self.save_pdf_button.setEnabled(enabled)

    def _render_metrics(self, metrics: list[dict[str, Any]]) -> None:
        fallback = [
            {"label": "Kanıt", "value": "0", "note": "source/snippet"},
            {"label": "Risk", "value": "0", "note": "clinical warning"},
            {"label": "Timeline", "value": "0", "note": "event"},
            {"label": "Rapor", "value": "-", "note": "one click"},
        ]
        for item in (metrics or fallback):
            label = item.get("label")
            box = self.metric_boxes.get(label)
            if box:
                box.set_metric(str(item.get("value") or "0"), str(item.get("note") or ""))

    def _render_quality(self, quality: dict[str, Any]) -> None:
        self._clear_layout(self.quality_layout, keep_first=1)
        title = quality.get("title") or "Veri kalitesi bekleniyor"
        summary = quality.get("summary") or "Hasta kaydı doğrulanınca uç değer ve tutarsızlık kontrolü yapılır."
        self.quality_box.setTitle(f"Data Quality - {title}")
        self.quality_summary.setText(summary)

        for item in (quality.get("items") or [])[:8]:
            frame = self._classic_card("verify")
            layout = QVBoxLayout(frame)
            layout.setContentsMargins(7, 5, 7, 5)
            head = QLabel(f"{item.get('metric', 'Lab')}: {item.get('value', '')}")
            head.setObjectName("cardTitle")
            head.setWordWrap(True)
            reason = QLabel(str(item.get("reason") or "Doğrulama önerilir."))
            reason.setWordWrap(True)
            source = QLabel(str(item.get("source") or ""))
            source.setObjectName("mutedLabel")
            source.setWordWrap(True)
            layout.addWidget(head)
            layout.addWidget(reason)
            layout.addWidget(source)
            self.quality_layout.addWidget(frame)

    def _render_cards(self, layout: QVBoxLayout, items: list[dict[str, Any]], empty: str) -> None:
        self._clear_layout(layout)
        if not items:
            layout.addWidget(QLabel(empty))
            layout.addStretch(1)
            return
        for item in items:
            tone = item.get("tone") or "info"
            frame = self._classic_card(tone)
            frame_layout = QVBoxLayout(frame)
            frame_layout.setContentsMargins(7, 5, 7, 5)
            title = item.get("title") or item.get("signal") or "Kayıt"
            source = item.get("source") or item.get("label") or item.get("level") or ""
            snippet = item.get("snippet") or item.get("evidence") or ""
            title_label = QLabel(str(title))
            title_label.setObjectName("cardTitle")
            title_label.setWordWrap(True)
            source_label = QLabel(str(source))
            source_label.setObjectName("mutedLabel")
            source_label.setWordWrap(True)
            snippet_label = QLabel(str(snippet))
            snippet_label.setWordWrap(True)
            frame_layout.addWidget(title_label)
            frame_layout.addWidget(source_label)
            frame_layout.addWidget(snippet_label)
            layout.addWidget(frame)
        layout.addStretch(1)

    def _render_timeline(self, items: list[dict[str, Any]]) -> None:
        self._clear_layout(self.timeline_layout)
        if not items:
            self.timeline_layout.addWidget(QLabel("Timeline bekleniyor."))
            self.timeline_layout.addStretch(1)
            return
        for item in items[:100]:
            frame = self._classic_card("timeline")
            frame_layout = QVBoxLayout(frame)
            frame_layout.setContentsMargins(7, 5, 7, 5)
            date = QLabel(str(item.get("date") or "Tarih yok"))
            date.setObjectName("timelineDate")
            title = QLabel(str(item.get("title") or "Olay"))
            title.setObjectName("cardTitle")
            title.setWordWrap(True)
            meta = QLabel(f"{item.get('category') or 'kategori'} | {item.get('source') or 'kaynak'}")
            meta.setObjectName("mutedLabel")
            meta.setWordWrap(True)
            frame_layout.addWidget(date)
            frame_layout.addWidget(title)
            frame_layout.addWidget(meta)
            self.timeline_layout.addWidget(frame)
        self.timeline_layout.addStretch(1)

    def _classic_card(self, tone: str) -> QFrame:
        frame = QFrame()
        frame.setFrameShape(QFrame.Panel)
        frame.setFrameShadow(QFrame.Raised)
        colors = {
            "critical": "#ffe0e0",
            "red": "#ffe0e0",
            "warning": "#fff0c0",
            "yellow": "#fff0c0",
            "verify": "#fff0c0",
            "green": "#e0ffe0",
            "timeline": "#e8e8e8",
            "info": "#e0e8ff",
        }
        frame.setStyleSheet(f"QFrame {{ background: {colors.get(tone, '#e8e8e8')}; }}")
        return frame

    def _clear_layout(self, layout: QVBoxLayout, keep_first: int = 0) -> None:
        while layout.count() > keep_first:
            item = layout.takeAt(keep_first)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()

    def copy_answer(self) -> None:
        answer = self.payload.get("answer") or ""
        if answer:
            QApplication.clipboard().setText(answer)
            self.statusBar().showMessage("Answer copied.")

    def report_filename(self, extension: str) -> str:
        patient = self.clinical_panel.get("patient_id") or "hasta"
        safe_patient = re.sub(r"[^A-Za-z0-9_-]+", "_", str(patient))[:48] or "hasta"
        date = datetime.now().strftime("%Y-%m-%d")
        return f"datamedx-{safe_patient}-{date}.{extension}"

    def save_markdown_report(self) -> None:
        if not self.report_markdown:
            QMessageBox.information(self, "No report", "Kaydedilecek rapor yok.")
            return
        path, _ = QFileDialog.getSaveFileName(
            self,
            "Save Markdown Report",
            self.report_filename("md"),
            "Markdown Files (*.md);;Text Files (*.txt)",
        )
        if not path:
            return
        with open(path, "w", encoding="utf-8") as file:
            file.write(self.report_markdown)
        self.statusBar().showMessage(f"Report saved: {path}")

    def export_pdf_report(self) -> None:
        if not self.report_markdown:
            QMessageBox.information(self, "No report", "PDF için rapor yok.")
            return
        path, _ = QFileDialog.getSaveFileName(
            self,
            "Export PDF Report",
            self.report_filename("pdf"),
            "PDF Files (*.pdf)",
        )
        if not path:
            return
        if not path.lower().endswith(".pdf"):
            path += ".pdf"
        printer = QPrinter(QPrinter.HighResolution)
        printer.setOutputFormat(QPrinter.PdfFormat)
        printer.setOutputFileName(path)
        document = QTextDocument()
        document.setHtml(markdown_to_html(self.report_markdown))
        document.print_(printer)
        self.statusBar().showMessage(f"PDF exported: {path}")

    def show_about(self) -> None:
        QMessageBox.information(
            self,
            "About DataMedX",
            "DataMedX Qt Doctor Workstation\n"
            "Classic Windows styled clinical orchestration frontend.\n\n"
            f"Backend API: {API_BASE}",
        )


def main() -> int:
    app = QApplication(sys.argv)
    window = DataMedXQtDoctor()
    window.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
