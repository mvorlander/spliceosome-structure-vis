#!/usr/bin/env python3
"""Open a small ChimeraX browser for generated named selections."""

from __future__ import annotations

import json
import sys

from chimerax.core.commands import run


def _ui_available(session) -> bool:
    return bool(getattr(getattr(session, "ui", None), "is_gui", False))


def open_selection_browser(session, spec_path: str) -> None:
    with open(spec_path, "r", encoding="utf-8") as handle:
        spec = json.load(handle)
    selectors = list(spec.get("selectors", []))
    if not selectors:
        session.logger.info("No spliceosome named selections are available for this structure.")
        return
    if not _ui_available(session):
        session.logger.info(
            f"Loaded {len(selectors)} spliceosome named selections; "
            "the selection browser is skipped in no-GUI ChimeraX."
        )
        return

    from chimerax.core.tools import ToolInstance
    from chimerax.ui import MainToolWindow
    from Qt.QtCore import Qt
    from Qt.QtWidgets import (
        QAbstractItemView,
        QHBoxLayout,
        QLabel,
        QLineEdit,
        QListWidget,
        QListWidgetItem,
        QPushButton,
        QVBoxLayout,
        QWidget,
    )

    class SpliceosomeSelectionBrowser(ToolInstance):
        SESSION_ENDURING = False
        SESSION_SAVE = False

        def __init__(self, session, tool_name, spec, selectors):
            super().__init__(session, tool_name)
            self.spec = spec
            self.selectors = selectors
            self.filtered = list(selectors)
            self.tool_window = MainToolWindow(self)
            parent = self.tool_window.ui_area
            layout = QVBoxLayout(parent)
            title = QLabel(
                f"{spec.get('pdb_id', '').upper()} named selections "
                f"({len(selectors)} total)"
            )
            layout.addWidget(title)
            self.search = QLineEdit(parent)
            self.search.setPlaceholderText("Search selector, label, category, residues, or atomspec")
            layout.addWidget(self.search)
            self.list_widget = QListWidget(parent)
            self.list_widget.setSelectionMode(QAbstractItemView.SingleSelection)
            layout.addWidget(self.list_widget)
            buttons = QHBoxLayout()
            self.select_button = QPushButton("Select + Zoom", parent)
            self.clear_button = QPushButton("Clear", parent)
            buttons.addWidget(self.select_button)
            buttons.addWidget(self.clear_button)
            layout.addLayout(buttons)

            self.search.textChanged.connect(self._filter)
            self.list_widget.itemClicked.connect(self._activate_item)
            self.list_widget.itemDoubleClicked.connect(self._activate_item)
            self.select_button.clicked.connect(self._activate_current)
            self.clear_button.clicked.connect(lambda: run(self.session, "select clear"))
            self._populate()
            self.tool_window.manage("side")

        def _filter_text(self, item):
            return " ".join(
                str(item.get(key, ""))
                for key in ("name", "label", "category", "atomspec", "comment")
            ).lower()

        def _filter(self, text):
            needle = text.strip().lower()
            self.filtered = [
                item for item in self.selectors if not needle or needle in self._filter_text(item)
            ]
            self._populate()

        def _populate(self):
            self.list_widget.clear()
            for item in self.filtered:
                label = item.get("label") or item.get("name")
                category = item.get("category") or "selection"
                selector = item.get("name", "")
                atomspec = item.get("atomspec", "")
                row = QListWidgetItem(f"{label}   [{category}]\n{selector}  ->  {atomspec}")
                row.setData(Qt.UserRole, item)
                self.list_widget.addItem(row)

        def _activate_current(self):
            item = self.list_widget.currentItem()
            if item is not None:
                self._activate_item(item)

        def _activate_item(self, item):
            data = item.data(Qt.UserRole)
            selector = data.get("name", "")
            if not selector:
                return
            run(self.session, "select clear")
            run(self.session, f"select {selector}")
            run(self.session, "view sel")

    tool_name = f"Spliceosome Selections {spec.get('pdb_id', '').upper()}".strip()
    SpliceosomeSelectionBrowser(session, tool_name, spec, selectors)
    session.logger.info(f"Opened spliceosome named selection browser with {len(selectors)} entries.")

# Embedded named-selection specification for remote execution from GitHub.
_EMBEDDED_SPEC = {
  "pdb_id": "5mq0",
  "selectors": [
    {
      "atomspec": "#314.1/2:1-49,55-73,78-84,98-104,139-150|#314.1/E:-16--1",
      "category": "substrate RNA feature",
      "comment": "5' exon: residues -16--1; 1-49;55-73;78-84;98-104;139-150, component-name/splice-site-inference, high/medium confidence, validation not_applicable",
      "label": "5' exon",
      "name": "Cstar_5MQ0_5exon",
      "section": "Named selections for resolved substrate RNA features."
    },
    {
      "atomspec": "#314.1/2:1-49,55-73,78-84,98-104,139-150,1089-1108,1117-1129,1138-1154,1159-1169|#314.1/3:1-3|#314.1/5:4-53,62-145,167-173|#314.1/6:1-10,16-104|#314.1/E:-16--1|#314.1/I:1-16,56-73",
      "category": "substrate RNA feature",
      "comment": "substrate RNA: residues -16--1; 1-10;16-104; 1-16;56-73; 1-3; 1-49;55-73;78-84;98-104;139-150;1089-1108;1117-1129;1138-1154;1159-1169; 4-53;62-145;167-173, component, medium confidence, validation not_applicable",
      "label": "substrate RNA",
      "name": "Cstar_5MQ0_substrate",
      "section": "Named selections for resolved substrate RNA features."
    },
    {
      "atomspec": "#314.1/2:1089|#314.1/E:-16--1",
      "category": "substrate RNA feature",
      "comment": "intron: residues -16--1; 1089, five-ss-inference/splice-site-inference, low/medium confidence, validation not_applicable",
      "label": "intron",
      "name": "Cstar_5MQ0_intron",
      "section": "Named selections for resolved substrate RNA features."
    },
    {
      "atomspec": "#314.1/2:1089|#314.1/5:133-135",
      "category": "substrate RNA feature",
      "comment": "3' splice site: residues 1089; 133-135, sequence-motif, medium confidence, validation validated",
      "label": "3' splice site",
      "name": "Cstar_5MQ0_3SS",
      "section": "Named selections for resolved substrate RNA features."
    },
    {
      "atomspec": "#314.1/2:1090-1108,1117-1129,1138-1154,1159-1169|#314.1/3:1-3",
      "category": "substrate RNA feature",
      "comment": "3' exon: residues 1-3; 1090-1108;1117-1129;1138-1154;1159-1169, component-name/splice-site-inference, high/medium confidence, validation not_applicable",
      "label": "3' exon",
      "name": "Cstar_5MQ0_3exon",
      "section": "Named selections for resolved substrate RNA features."
    },
    {
      "atomspec": "#314.1/5:72-76|#314.1/I:65-71",
      "category": "substrate RNA feature",
      "comment": "branch point region: residues 65-71; 72-76, network-scored-motif, medium/review confidence, validation uncertain uncertain validation",
      "label": "branch point region",
      "name": "Cstar_5MQ0_branch_region",
      "section": "Named selections for resolved substrate RNA features."
    },
    {
      "atomspec": "#314.1/5:94-99",
      "category": "substrate RNA feature",
      "comment": "polypyrimidine tract: residues 94-99, sequence-motif, medium confidence, validation uncertain uncertain validation",
      "label": "polypyrimidine tract",
      "name": "Cstar_5MQ0_PPT",
      "section": "Named selections for resolved substrate RNA features."
    },
    {
      "atomspec": "#314.1/E:-16--12",
      "category": "substrate RNA feature",
      "comment": "5' splice site: residues -16--12, sequence-motif, medium confidence, validation uncertain uncertain validation",
      "label": "5' splice site",
      "name": "Cstar_5MQ0_5SS",
      "section": "Named selections for resolved substrate RNA features."
    }
  ],
  "structure_group_id": "314",
  "structure_model_id": "314.1"
}

import os as _os
import tempfile as _tempfile
_fd, _spec_path = _tempfile.mkstemp(prefix='spliceosome_named_selections_', suffix='.json')
try:
    with _os.fdopen(_fd, 'w', encoding='utf-8') as _handle:
        json.dump(_EMBEDDED_SPEC, _handle)
    open_selection_browser(session, _spec_path)
finally:
    try:
        _os.remove(_spec_path)
    except OSError:
        pass
