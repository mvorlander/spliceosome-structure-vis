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
  "pdb_id": "5mps",
  "selectors": [
    {
      "atomspec": "#313.1/H",
      "category": "subcomplex",
      "comment": "EJC/mRNP",
      "label": "EJC/mRNP",
      "name": "pdb_5MPS_EJC_mRNP",
      "section": "Named selections for subcomplexes using original deposited chain IDs."
    },
    {
      "atomspec": "#313.1/K,L,M,N,S,T,y",
      "category": "subcomplex",
      "comment": "NTC/NTR related",
      "label": "NTC/NTR related",
      "name": "pdb_5MPS_NTC_NTR_related",
      "section": "Named selections for subcomplexes using original deposited chain IDs."
    },
    {
      "atomspec": "#313.1/J,O,P",
      "category": "subcomplex",
      "comment": "NTC/PRP19",
      "label": "NTC/PRP19",
      "name": "pdb_5MPS_NTC_PRP19",
      "section": "Named selections for subcomplexes using original deposited chain IDs."
    },
    {
      "atomspec": "#313.1/6,E,I",
      "category": "subcomplex",
      "comment": "RNA/substrate",
      "label": "RNA/substrate",
      "name": "pdb_5MPS_RNA_substrate",
      "section": "Named selections for subcomplexes using original deposited chain IDs."
    },
    {
      "atomspec": "#313.1/c,o",
      "category": "subcomplex",
      "comment": "Second step factors",
      "label": "Second step factors",
      "name": "pdb_5MPS_Second_step_factors",
      "section": "Named selections for subcomplexes using original deposited chain IDs."
    },
    {
      "atomspec": "#313.1/2",
      "category": "subcomplex",
      "comment": "U2 snRNP",
      "label": "U2 snRNP",
      "name": "pdb_5MPS_U2_snRNP",
      "section": "Named selections for subcomplexes using original deposited chain IDs."
    },
    {
      "atomspec": "#313.1/b,d,e,f,g,h,j",
      "category": "subcomplex",
      "comment": "U5 Sm ring",
      "label": "U5 Sm ring",
      "name": "pdb_5MPS_U5_Sm_ring",
      "section": "Named selections for subcomplexes using original deposited chain IDs."
    },
    {
      "atomspec": "#313.1/5,A,C",
      "category": "subcomplex",
      "comment": "U5 snRNP",
      "label": "U5 snRNP",
      "name": "pdb_5MPS_U5_snRNP",
      "section": "Named selections for subcomplexes using original deposited chain IDs."
    },
    {
      "atomspec": "#313.1/R,X,a",
      "category": "subcomplex",
      "comment": "other",
      "label": "other",
      "name": "pdb_5MPS_other",
      "section": "Named selections for subcomplexes using original deposited chain IDs."
    },
    {
      "atomspec": "#313.1/6:1-10,16-104|#313.1/E:-16--1|#313.1/I:1-16,56-73",
      "category": "substrate RNA feature",
      "comment": "substrate RNA: residues -16--1; 1-10;16-104; 1-16;56-73, component, medium confidence, validation not_applicable",
      "label": "substrate RNA",
      "name": "Cstar_5MPS_substrate",
      "section": "Named selections for resolved substrate RNA features."
    },
    {
      "atomspec": "#313.1/E:-16--12",
      "category": "substrate RNA feature",
      "comment": "5' splice site: residues -16--12, sequence-motif, medium confidence, validation uncertain uncertain validation",
      "label": "5' splice site",
      "name": "Cstar_5MPS_5SS",
      "section": "Named selections for resolved substrate RNA features."
    },
    {
      "atomspec": "#313.1/E:-16--1",
      "category": "substrate RNA feature",
      "comment": "intron from 5' splice site: residues -16--1, five-ss-inference, low confidence, validation not_applicable",
      "label": "intron from 5' splice site",
      "name": "Cstar_5MPS_intron",
      "section": "Named selections for resolved substrate RNA features."
    },
    {
      "atomspec": "#313.1/I:62-72",
      "category": "substrate RNA feature",
      "comment": "branch point region: residues 62-72, network-scored-motif, high confidence, validation validated",
      "label": "branch point region",
      "name": "Cstar_5MPS_branch_region",
      "section": "Named selections for resolved substrate RNA features."
    },
    {
      "atomspec": "#313.1/I:70",
      "category": "substrate RNA feature",
      "comment": "branch point adenosine: residues 70, network-scored-motif, high confidence, validation validated",
      "label": "branch point adenosine",
      "name": "Cstar_5MPS_branch_A",
      "section": "Named selections for resolved substrate RNA features."
    },
    {
      "atomspec": "#313.1/2:26-30",
      "category": "snRNA feature",
      "comment": "U2 snRNA U2/U6 helix I partner: residues 26-30, review-region, high confidence",
      "label": "U2 snRNA U2/U6 helix I partner",
      "name": "Cstar_5MPS_U2_U6_helix_I_partner",
      "section": "Named selections for resolved snRNA functional regions."
    },
    {
      "atomspec": "#313.1/2:33-42",
      "category": "snRNA feature",
      "comment": "U2 snRNA branchpoint pairing region: residues 33-42, sequence-motif-neighborhood, medium confidence",
      "label": "U2 snRNA branchpoint pairing region",
      "name": "Cstar_5MPS_U2_branchpoint_pairing_region",
      "section": "Named selections for resolved snRNA functional regions."
    },
    {
      "atomspec": "#313.1/2:46-49",
      "category": "snRNA feature",
      "comment": "U2 snRNA stem IIa: residues 46-49, review-region, low confidence",
      "label": "U2 snRNA stem IIa",
      "name": "Cstar_5MPS_U2_stem_IIa",
      "section": "Named selections for resolved snRNA functional regions."
    },
    {
      "atomspec": "#313.1/5:53",
      "category": "snRNA feature",
      "comment": "U5 snRNA loop I: residues 53, sequence-motif, medium confidence",
      "label": "U5 snRNA loop I",
      "name": "Cstar_5MPS_U5_loop_I",
      "section": "Named selections for resolved snRNA functional regions."
    }
  ],
  "structure_group_id": "313",
  "structure_model_id": "313.1"
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
