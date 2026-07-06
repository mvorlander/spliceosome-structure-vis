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
  "pdb_id": "7oqe",
  "selectors": [
    {
      "atomspec": "#366.1/I:-2,-1,1,2,3,4,5,6,7,8",
      "category": "substrate RNA feature",
      "comment": "5' exon: residues -2,-1,1,2,3,4,5,6,7,8, splice-site-inference, medium confidence, validation not_applicable",
      "label": "5' exon",
      "name": "E_complex_7OQE_5exon",
      "section": "Named selections for resolved substrate RNA features."
    },
    {
      "atomspec": "#366.1/I:-2,-1,1,2,3,4,5,6,7,8,103-128,130-156,246-268",
      "category": "substrate RNA feature",
      "comment": "substrate RNA: residues -2,-1,1,2,3,4,5,6,7,8;103-128;130-156;246-268, component, medium confidence, validation not_applicable",
      "label": "substrate RNA",
      "name": "E_complex_7OQE_substrate",
      "section": "Named selections for resolved substrate RNA features."
    },
    {
      "atomspec": "#366.1/I:103-128,130-156,246-268",
      "category": "substrate RNA feature",
      "comment": "intron: residues 103-128;130-156;246-268, splice-site-inference, medium confidence, validation not_applicable",
      "label": "intron",
      "name": "E_complex_7OQE_intron",
      "section": "Named selections for resolved substrate RNA features."
    },
    {
      "atomspec": "#366.1/1:1-10",
      "category": "snRNA feature",
      "comment": "U1 snRNA 5' splice-site recognition region: residues 1-10, review-region, medium confidence",
      "label": "U1 snRNA 5' splice-site recognition region",
      "name": "E_complex_7OQE_U1_5_5SS_recognition",
      "section": "Named selections for resolved snRNA functional regions."
    },
    {
      "atomspec": "#366.1/1:11-26,34-45",
      "category": "snRNA feature",
      "comment": "U1 snRNA stem-loop 1: residues 11-26;34-45, review-region, low confidence",
      "label": "U1 snRNA stem-loop 1",
      "name": "E_complex_7OQE_U1_SL1",
      "section": "Named selections for resolved snRNA functional regions."
    },
    {
      "atomspec": "#366.1/1:46-95",
      "category": "snRNA feature",
      "comment": "U1 snRNA stem-loop 2: residues 46-95, review-region, low confidence",
      "label": "U1 snRNA stem-loop 2",
      "name": "E_complex_7OQE_U1_SL2",
      "section": "Named selections for resolved snRNA functional regions."
    },
    {
      "atomspec": "#366.1/1:224-230|#366.1/1:241-247|#366.1/1:553-559",
      "category": "snRNA feature",
      "comment": "U1 snRNA Sm site: residues 224-230; 241-247; 553-559, sequence-motif, medium confidence",
      "label": "U1 snRNA Sm site",
      "name": "E_complex_7OQE_U1_Sm_site",
      "section": "Named selections for resolved snRNA functional regions."
    },
    {
      "atomspec": "#366.1/2:33-42",
      "category": "snRNA feature",
      "comment": "U2 snRNA branchpoint pairing region: residues 33-42, sequence-motif-neighborhood, medium confidence",
      "label": "U2 snRNA branchpoint pairing region",
      "name": "E_complex_7OQE_U2_branchpoint_pairing_region",
      "section": "Named selections for resolved snRNA functional regions."
    },
    {
      "atomspec": "#366.1/2:46-74,78-80",
      "category": "snRNA feature",
      "comment": "U2 snRNA stem IIa: residues 46-74;78-80, review-region, low confidence",
      "label": "U2 snRNA stem IIa",
      "name": "E_complex_7OQE_U2_stem_IIa",
      "section": "Named selections for resolved snRNA functional regions."
    }
  ],
  "structure_group_id": "366",
  "structure_model_id": "366.1"
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
