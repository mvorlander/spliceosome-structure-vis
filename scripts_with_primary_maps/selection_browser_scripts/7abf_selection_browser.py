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
  "pdb_id": "7abf",
  "selectors": [
    {
      "atomspec": "#355.1/Q,v",
      "category": "subcomplex",
      "comment": "NTC/NTR related",
      "label": "NTC/NTR related",
      "name": "pdb_7ABF_NTC_NTR_related",
      "section": "Named selections for subcomplexes using original deposited chain IDs."
    },
    {
      "atomspec": "#355.1/G,R",
      "category": "subcomplex",
      "comment": "NTC/PRP19",
      "label": "NTC/PRP19",
      "name": "pdb_7ABF_NTC_PRP19",
      "section": "Named selections for subcomplexes using original deposited chain IDs."
    },
    {
      "atomspec": "#355.1/Z",
      "category": "subcomplex",
      "comment": "RNA/substrate",
      "label": "RNA/substrate",
      "name": "pdb_7ABF_RNA_substrate",
      "section": "Named selections for subcomplexes using original deposited chain IDs."
    },
    {
      "atomspec": "#355.1/5,A,r",
      "category": "subcomplex",
      "comment": "U5 snRNP",
      "label": "U5 snRNP",
      "name": "pdb_7ABF_U5_snRNP",
      "section": "Named selections for subcomplexes using original deposited chain IDs."
    },
    {
      "atomspec": "#355.1/6",
      "category": "subcomplex",
      "comment": "U6 snRNP",
      "label": "U6 snRNP",
      "name": "pdb_7ABF_U6_snRNP",
      "section": "Named selections for subcomplexes using original deposited chain IDs."
    },
    {
      "atomspec": "#355.1/A4,I,K,N,X,q",
      "category": "subcomplex",
      "comment": "other",
      "label": "other",
      "name": "pdb_7ABF_other",
      "section": "Named selections for subcomplexes using original deposited chain IDs."
    },
    {
      "atomspec": "#355.1/Z:50-58",
      "category": "substrate RNA feature",
      "comment": "5' exon: residues 50-58, splice-site-inference, medium confidence, validation not_applicable",
      "label": "5' exon",
      "name": "pre_Bact_7ABF_5exon",
      "section": "Named selections for resolved substrate RNA features."
    },
    {
      "atomspec": "#355.1/Z:50-78",
      "category": "substrate RNA feature",
      "comment": "substrate RNA: residues 50-78, component, medium confidence, validation not_applicable",
      "label": "substrate RNA",
      "name": "pre_Bact_7ABF_substrate",
      "section": "Named selections for resolved substrate RNA features."
    },
    {
      "atomspec": "#355.1/Z:59-64",
      "category": "substrate RNA feature",
      "comment": "5' splice site: residues 59-64, sequence-motif, medium confidence, validation uncertain uncertain validation",
      "label": "5' splice site",
      "name": "pre_Bact_7ABF_5SS",
      "section": "Named selections for resolved substrate RNA features."
    },
    {
      "atomspec": "#355.1/Z:59-78",
      "category": "substrate RNA feature",
      "comment": "intron: residues 59-78, splice-site-inference, medium confidence, validation not_applicable",
      "label": "intron",
      "name": "pre_Bact_7ABF_intron",
      "section": "Named selections for resolved substrate RNA features."
    },
    {
      "atomspec": "#355.1/5:38-42",
      "category": "snRNA feature",
      "comment": "U5 snRNA loop I: residues 38-42, sequence-motif, medium confidence",
      "label": "U5 snRNA loop I",
      "name": "pre_Bact_7ABF_U5_loop_I",
      "section": "Named selections for resolved snRNA functional regions."
    },
    {
      "atomspec": "#355.1/6:1-30",
      "category": "snRNA feature",
      "comment": "U6 snRNA 5' terminal stem-loop: residues 1-30, reference-alignment, high confidence",
      "label": "U6 snRNA 5' terminal stem-loop",
      "name": "pre_Bact_7ABF_U6_5_terminal_stem_loop",
      "section": "Named selections for resolved snRNA functional regions."
    },
    {
      "atomspec": "#355.1/6:35-46,58-60",
      "category": "snRNA feature",
      "comment": "U6 snRNA U2/U6 helix I partner: residues 35-46;58-60, motif-neighborhood, medium confidence",
      "label": "U6 snRNA U2/U6 helix I partner",
      "name": "pre_Bact_7ABF_U6_U2_helix_I_partner",
      "section": "Named selections for resolved snRNA functional regions."
    },
    {
      "atomspec": "#355.1/6:38-46",
      "category": "snRNA feature",
      "comment": "U6 snRNA 5' splice-site upstream contact: residues 38-46, motif-neighborhood, medium confidence",
      "label": "U6 snRNA 5' splice-site upstream contact",
      "name": "pre_Bact_7ABF_U6_5SS_upstream_contact",
      "section": "Named selections for resolved snRNA functional regions."
    },
    {
      "atomspec": "#355.1/6:41-46",
      "category": "snRNA feature",
      "comment": "U6 snRNA ACAGAGA box: residues 41-46, sequence-motif, high confidence",
      "label": "U6 snRNA ACAGAGA box",
      "name": "pre_Bact_7ABF_U6_ACAGAGA_box",
      "section": "Named selections for resolved snRNA functional regions."
    }
  ],
  "structure_group_id": "355",
  "structure_model_id": "355.1"
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
