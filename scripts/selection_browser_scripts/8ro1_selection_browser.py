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
  "pdb_id": "8ro1",
  "selectors": [
    {
      "atomspec": "#414.1/PX,TF",
      "category": "subcomplex",
      "comment": "Disassembly factors",
      "label": "Disassembly factors",
      "name": "pdb_8RO1_Disassembly_factors",
      "section": "Named selections for subcomplexes using original deposited chain IDs."
    },
    {
      "atomspec": "#414.1/D,I,J,L2,M,N,O,Q,R,S,y",
      "category": "subcomplex",
      "comment": "NTC/NTR related",
      "label": "NTC/NTR related",
      "name": "pdb_8RO1_NTC_NTR_related",
      "section": "Named selections for subcomplexes using original deposited chain IDs."
    },
    {
      "atomspec": "#414.1/K,L,P,T,q,r,s,t",
      "category": "subcomplex",
      "comment": "NTC/PRP19",
      "label": "NTC/PRP19",
      "name": "pdb_8RO1_NTC_PRP19",
      "section": "Named selections for subcomplexes using original deposited chain IDs."
    },
    {
      "atomspec": "#414.1/IN",
      "category": "subcomplex",
      "comment": "RNA/substrate",
      "label": "RNA/substrate",
      "name": "pdb_8RO1_RNA_substrate",
      "section": "Named selections for subcomplexes using original deposited chain IDs."
    },
    {
      "atomspec": "#414.1/W",
      "category": "subcomplex",
      "comment": "Second step factors",
      "label": "Second step factors",
      "name": "pdb_8RO1_Second_step_factors",
      "section": "Named selections for subcomplexes using original deposited chain IDs."
    },
    {
      "atomspec": "#414.1/h,i,j,k,l,m,n",
      "category": "subcomplex",
      "comment": "U2 Sm ring",
      "label": "U2 Sm ring",
      "name": "pdb_8RO1_U2_Sm_ring",
      "section": "Named selections for subcomplexes using original deposited chain IDs."
    },
    {
      "atomspec": "#414.1/2,DX,o,p",
      "category": "subcomplex",
      "comment": "U2 snRNP",
      "label": "U2 snRNP",
      "name": "pdb_8RO1_U2_snRNP",
      "section": "Named selections for subcomplexes using original deposited chain IDs."
    },
    {
      "atomspec": "#414.1/a,b,c,d,e,f,g",
      "category": "subcomplex",
      "comment": "U5 Sm ring",
      "label": "U5 Sm ring",
      "name": "pdb_8RO1_U5_Sm_ring",
      "section": "Named selections for subcomplexes using original deposited chain IDs."
    },
    {
      "atomspec": "#414.1/5,A,C,E",
      "category": "subcomplex",
      "comment": "U5 snRNP",
      "label": "U5 snRNP",
      "name": "pdb_8RO1_U5_snRNP",
      "section": "Named selections for subcomplexes using original deposited chain IDs."
    },
    {
      "atomspec": "#414.1/6",
      "category": "subcomplex",
      "comment": "U6 snRNP",
      "label": "U6 snRNP",
      "name": "pdb_8RO1_U6_snRNP",
      "section": "Named selections for subcomplexes using original deposited chain IDs."
    },
    {
      "atomspec": "#414.1/L1,X,Z",
      "category": "subcomplex",
      "comment": "other",
      "label": "other",
      "name": "pdb_8RO1_other",
      "section": "Named selections for subcomplexes using original deposited chain IDs."
    },
    {
      "atomspec": "#414.1/IN:1-2,10-28,40-51",
      "category": "substrate RNA feature",
      "comment": "intron: residues 1-2;10-28;40-51, component-name, high confidence, validation not_applicable",
      "label": "intron",
      "name": "ILS_disassembly_8RO1_intron",
      "section": "Named selections for resolved substrate RNA features."
    },
    {
      "atomspec": "#414.1/IN:1-2,10-28,40-51",
      "category": "substrate RNA feature",
      "comment": "intron lariat: residues 1-2;10-28;40-51, component-name, high confidence, validation not_applicable",
      "label": "intron lariat",
      "name": "ILS_disassembly_8RO1_intron_lariat",
      "section": "Named selections for resolved substrate RNA features."
    },
    {
      "atomspec": "#414.1/IN:1-2,10-28,40-51",
      "category": "substrate RNA feature",
      "comment": "substrate RNA: residues 1-2;10-28;40-51, component, medium confidence, validation not_applicable",
      "label": "substrate RNA",
      "name": "ILS_disassembly_8RO1_substrate",
      "section": "Named selections for resolved substrate RNA features."
    },
    {
      "atomspec": "#414.1/2:26-30",
      "category": "snRNA feature",
      "comment": "U2 snRNA U2/U6 helix I partner: residues 26-30, review-region, high confidence",
      "label": "U2 snRNA U2/U6 helix I partner",
      "name": "ILS_disassembly_8RO1_U2_U6_helix_I_partner",
      "section": "Named selections for resolved snRNA functional regions."
    },
    {
      "atomspec": "#414.1/2:34-42",
      "category": "snRNA feature",
      "comment": "U2 snRNA branchpoint pairing region: residues 34-42, sequence-motif-neighborhood, medium confidence",
      "label": "U2 snRNA branchpoint pairing region",
      "name": "ILS_disassembly_8RO1_U2_branchpoint_pairing_region",
      "section": "Named selections for resolved snRNA functional regions."
    },
    {
      "atomspec": "#414.1/5:41-45",
      "category": "snRNA feature",
      "comment": "U5 snRNA loop I: residues 41-45, sequence-motif, medium confidence",
      "label": "U5 snRNA loop I",
      "name": "ILS_disassembly_8RO1_U5_loop_I",
      "section": "Named selections for resolved snRNA functional regions."
    },
    {
      "atomspec": "#414.1/5:93-99",
      "category": "snRNA feature",
      "comment": "U5 snRNA Sm site: residues 93-99, sequence-motif, medium confidence",
      "label": "U5 snRNA Sm site",
      "name": "ILS_disassembly_8RO1_U5_Sm_site",
      "section": "Named selections for resolved snRNA functional regions."
    },
    {
      "atomspec": "#414.1/6:30-55",
      "category": "snRNA feature",
      "comment": "U6 snRNA U2/U6 helix I partner: residues 30-55, motif-neighborhood, medium confidence",
      "label": "U6 snRNA U2/U6 helix I partner",
      "name": "ILS_disassembly_8RO1_U6_U2_helix_I_partner",
      "section": "Named selections for resolved snRNA functional regions."
    },
    {
      "atomspec": "#414.1/6:33-44",
      "category": "snRNA feature",
      "comment": "U6 snRNA 5' splice-site upstream contact: residues 33-44, motif-neighborhood, medium confidence",
      "label": "U6 snRNA 5' splice-site upstream contact",
      "name": "ILS_disassembly_8RO1_U6_5SS_upstream_contact",
      "section": "Named selections for resolved snRNA functional regions."
    },
    {
      "atomspec": "#414.1/6:36-42",
      "category": "snRNA feature",
      "comment": "U6 snRNA ACAGAGA box: residues 36-42, sequence-motif, high confidence",
      "label": "U6 snRNA ACAGAGA box",
      "name": "ILS_disassembly_8RO1_U6_ACAGAGA_box",
      "section": "Named selections for resolved snRNA functional regions."
    },
    {
      "atomspec": "#414.1/6:74-101",
      "category": "snRNA feature",
      "comment": "U6 snRNA internal stem-loop: residues 74-101, motif-neighborhood, low confidence",
      "label": "U6 snRNA internal stem-loop",
      "name": "ILS_disassembly_8RO1_U6_ISL",
      "section": "Named selections for resolved snRNA functional regions."
    },
    {
      "atomspec": "#414.1/6:87-89",
      "category": "snRNA feature",
      "comment": "U6 snRNA AGC catalytic triad: residues 87-89, sequence-motif, medium confidence",
      "label": "U6 snRNA AGC catalytic triad",
      "name": "ILS_disassembly_8RO1_U6_AGC_catalytic_triad",
      "section": "Named selections for resolved snRNA functional regions."
    },
    {
      "atomspec": "#414.1/6:92-101",
      "category": "snRNA feature",
      "comment": "U6 snRNA LSm site: residues 92-101, terminal-region, low confidence",
      "label": "U6 snRNA LSm site",
      "name": "ILS_disassembly_8RO1_U6_LSm_site",
      "section": "Named selections for resolved snRNA functional regions."
    }
  ],
  "structure_group_id": "414",
  "structure_model_id": "414.1"
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
