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
  "pdb_id": "8y6o",
  "selectors": [
    {
      "atomspec": "#416.1/V",
      "category": "subcomplex",
      "comment": "RNA-binding",
      "label": "RNA-binding",
      "name": "pdb_8Y6O_RNA_binding",
      "section": "Named selections for subcomplexes using original deposited chain IDs."
    },
    {
      "atomspec": "#416.1/A",
      "category": "subcomplex",
      "comment": "RNA/substrate",
      "label": "RNA/substrate",
      "name": "pdb_8Y6O_RNA_substrate",
      "section": "Named selections for subcomplexes using original deposited chain IDs."
    },
    {
      "atomspec": "#416.1/h,i,j,k,l,m,n,o,p,q,r,s,t,u",
      "category": "subcomplex",
      "comment": "Sm ring",
      "label": "Sm ring",
      "name": "pdb_8Y6O_Sm_ring",
      "section": "Named selections for subcomplexes using original deposited chain IDs."
    },
    {
      "atomspec": "#416.1/P",
      "category": "subcomplex",
      "comment": "U11/U12 snRNP",
      "label": "U11/U12 snRNP",
      "name": "pdb_8Y6O_U11_U12_snRNP",
      "section": "Named selections for subcomplexes using original deposited chain IDs."
    },
    {
      "atomspec": "#416.1/I,L,M,N,O,Q,U",
      "category": "subcomplex",
      "comment": "U4/U6 snRNP",
      "label": "U4/U6 snRNP",
      "name": "pdb_8Y6O_U4_U6_snRNP",
      "section": "Named selections for subcomplexes using original deposited chain IDs."
    },
    {
      "atomspec": "#416.1/J,K",
      "category": "subcomplex",
      "comment": "U4atac/U6atac snRNP",
      "label": "U4atac/U6atac snRNP",
      "name": "pdb_8Y6O_U4atac_U6atac_snRNP",
      "section": "Named selections for subcomplexes using original deposited chain IDs."
    },
    {
      "atomspec": "#416.1/a,b,c,d,e,f,g",
      "category": "subcomplex",
      "comment": "U5 Sm ring",
      "label": "U5 Sm ring",
      "name": "pdb_8Y6O_U5_Sm_ring",
      "section": "Named selections for subcomplexes using original deposited chain IDs."
    },
    {
      "atomspec": "#416.1/B,C,D,E,F,G,S",
      "category": "subcomplex",
      "comment": "U5 snRNP",
      "label": "U5 snRNP",
      "name": "pdb_8Y6O_U5_snRNP",
      "section": "Named selections for subcomplexes using original deposited chain IDs."
    },
    {
      "atomspec": "#416.1/H,R,W,X,Y,Z",
      "category": "subcomplex",
      "comment": "other",
      "label": "other",
      "name": "pdb_8Y6O_other",
      "section": "Named selections for subcomplexes using original deposited chain IDs."
    },
    {
      "atomspec": "#416.1/A:-1-0",
      "category": "substrate RNA feature",
      "comment": "5' exon: residues -1-0, five-ss-inference, medium confidence, validation not_applicable",
      "label": "5' exon",
      "name": "pre_B_8Y6O_5exon",
      "section": "Named selections for resolved substrate RNA features."
    },
    {
      "atomspec": "#416.1/A:-1-11",
      "category": "substrate RNA feature",
      "comment": "substrate RNA: residues -1-11, component, medium confidence, validation not_applicable",
      "label": "substrate RNA",
      "name": "pre_B_8Y6O_substrate",
      "section": "Named selections for resolved substrate RNA features."
    },
    {
      "atomspec": "#416.1/A:1-10",
      "category": "substrate RNA feature",
      "comment": "5' splice site: residues 1-10, minor-snrna-basepair, high confidence, validation validated",
      "label": "5' splice site",
      "name": "pre_B_8Y6O_5SS",
      "section": "Named selections for resolved substrate RNA features."
    },
    {
      "atomspec": "#416.1/A:1-11",
      "category": "substrate RNA feature",
      "comment": "intron from 5' splice site: residues 1-11, five-ss-inference, low confidence, validation not_applicable",
      "label": "intron from 5' splice site",
      "name": "pre_B_8Y6O_intron",
      "section": "Named selections for resolved substrate RNA features."
    },
    {
      "atomspec": "#416.1/P:1-7",
      "category": "snRNA feature",
      "comment": "U11 snRNA 5' splice-site recognition region: residues 1-7, reference-alignment, high confidence",
      "label": "U11 snRNA 5' splice-site recognition region",
      "name": "pre_B_8Y6O_U11_5_5SS_recognition",
      "section": "Named selections for resolved snRNA functional regions."
    },
    {
      "atomspec": "#416.1/P:11-39,43-45",
      "category": "snRNA feature",
      "comment": "U11 snRNA stem-loop 1: residues 11-39;43-45, review-region, low confidence",
      "label": "U11 snRNA stem-loop 1",
      "name": "pre_B_8Y6O_U11_SL1",
      "section": "Named selections for resolved snRNA functional regions."
    },
    {
      "atomspec": "#416.1/P:46-95",
      "category": "snRNA feature",
      "comment": "U11 snRNA stem-loop 2: residues 46-95, review-region, low confidence",
      "label": "U11 snRNA stem-loop 2",
      "name": "pre_B_8Y6O_U11_SL2",
      "section": "Named selections for resolved snRNA functional regions."
    },
    {
      "atomspec": "#416.1/J:3-18",
      "category": "snRNA feature",
      "comment": "U4atac snRNA U4atac/U6atac stem I partner: residues 3-18, reference-alignment, medium confidence",
      "label": "U4atac snRNA U4atac/U6atac stem I partner",
      "name": "pre_B_8Y6O_U4atac_U6_stem_I_partner",
      "section": "Named selections for resolved snRNA functional regions."
    },
    {
      "atomspec": "#416.1/J:60-64",
      "category": "snRNA feature",
      "comment": "U4atac snRNA U4atac/U6atac stem II partner: residues 60-64, reference-alignment, medium confidence",
      "label": "U4atac snRNA U4atac/U6atac stem II partner",
      "name": "pre_B_8Y6O_U4atac_U6_stem_II_partner",
      "section": "Named selections for resolved snRNA functional regions."
    },
    {
      "atomspec": "#416.1/J:83-96",
      "category": "snRNA feature",
      "comment": "U4atac snRNA Brr2 loading region: residues 83-96, review-region, low confidence",
      "label": "U4atac snRNA Brr2 loading region",
      "name": "pre_B_8Y6O_U4atac_Brr2_loading_region",
      "section": "Named selections for resolved snRNA functional regions."
    },
    {
      "atomspec": "#416.1/J:116-122",
      "category": "snRNA feature",
      "comment": "U4atac snRNA Sm site: residues 116-122, sequence-motif, medium confidence",
      "label": "U4atac snRNA Sm site",
      "name": "pre_B_8Y6O_U4atac_Sm_site",
      "section": "Named selections for resolved snRNA functional regions."
    },
    {
      "atomspec": "#416.1/B:38-42",
      "category": "snRNA feature",
      "comment": "U5 snRNA loop I: residues 38-42, sequence-motif, medium confidence",
      "label": "U5 snRNA loop I",
      "name": "pre_B_8Y6O_U5_loop_I",
      "section": "Named selections for resolved snRNA functional regions."
    },
    {
      "atomspec": "#416.1/K:23-29",
      "category": "snRNA feature",
      "comment": "U6atac snRNA U6atac/U12 helix I partner: residues 23-29, reference-alignment, high confidence",
      "label": "U6atac snRNA U6atac/U12 helix I partner",
      "name": "pre_B_8Y6O_U6atac_U12_helix_I_partner",
      "section": "Named selections for resolved snRNA functional regions."
    },
    {
      "atomspec": "#416.1/K:26-28",
      "category": "snRNA feature",
      "comment": "U6atac snRNA AGC catalytic triad: residues 26-28, reference-alignment, high confidence",
      "label": "U6atac snRNA AGC catalytic triad",
      "name": "pre_B_8Y6O_U6atac_AGC_catalytic_triad",
      "section": "Named selections for resolved snRNA functional regions."
    },
    {
      "atomspec": "#416.1/K:52-58,60-65",
      "category": "snRNA feature",
      "comment": "U6atac snRNA internal stem-loop: residues 52-58;60-65, reference-alignment, medium confidence",
      "label": "U6atac snRNA internal stem-loop",
      "name": "pre_B_8Y6O_U6atac_ISL",
      "section": "Named selections for resolved snRNA functional regions."
    }
  ],
  "structure_group_id": "416",
  "structure_model_id": "416.1"
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
