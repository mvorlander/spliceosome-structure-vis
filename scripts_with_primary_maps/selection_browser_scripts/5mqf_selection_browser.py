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
  "pdb_id": "5mqf",
  "selectors": [
    {
      "atomspec": "#315.1/T,p",
      "category": "subcomplex",
      "comment": "EJC/mRNP",
      "label": "EJC/mRNP",
      "name": "pdb_5MQF_EJC_mRNP",
      "section": "Named selections for subcomplexes using original deposited chain IDs."
    },
    {
      "atomspec": "#315.1/C,M,N,O,P,Q,U,V,o",
      "category": "subcomplex",
      "comment": "NTC/NTR related",
      "label": "NTC/NTR related",
      "name": "pdb_5MQF_NTC_NTR_related",
      "section": "Named selections for subcomplexes using original deposited chain IDs."
    },
    {
      "atomspec": "#315.1/D,G,H,I,J,K,L,R",
      "category": "subcomplex",
      "comment": "NTC/PRP19",
      "label": "NTC/PRP19",
      "name": "pdb_5MQF_NTC_PRP19",
      "section": "Named selections for subcomplexes using original deposited chain IDs."
    },
    {
      "atomspec": "#315.1/Y,Z",
      "category": "subcomplex",
      "comment": "RNA/substrate",
      "label": "RNA/substrate",
      "name": "pdb_5MQF_RNA_substrate",
      "section": "Named selections for subcomplexes using original deposited chain IDs."
    },
    {
      "atomspec": "#315.1/S",
      "category": "subcomplex",
      "comment": "SR proteins",
      "label": "SR proteins",
      "name": "pdb_5MQF_SR_proteins",
      "section": "Named selections for subcomplexes using original deposited chain IDs."
    },
    {
      "atomspec": "#315.1/E,q",
      "category": "subcomplex",
      "comment": "Second step factors",
      "label": "Second step factors",
      "name": "pdb_5MQF_Second_step_factors",
      "section": "Named selections for subcomplexes using original deposited chain IDs."
    },
    {
      "atomspec": "#315.1/a,b,c,d,e,f,g",
      "category": "subcomplex",
      "comment": "Sm ring",
      "label": "Sm ring",
      "name": "pdb_5MQF_Sm_ring",
      "section": "Named selections for subcomplexes using original deposited chain IDs."
    },
    {
      "atomspec": "#315.1/h,i,j,k,l,m,n",
      "category": "subcomplex",
      "comment": "U2 Sm ring",
      "label": "U2 Sm ring",
      "name": "pdb_5MQF_U2_Sm_ring",
      "section": "Named selections for subcomplexes using original deposited chain IDs."
    },
    {
      "atomspec": "#315.1/2,W,X",
      "category": "subcomplex",
      "comment": "U2 snRNP",
      "label": "U2 snRNP",
      "name": "pdb_5MQF_U2_snRNP",
      "section": "Named selections for subcomplexes using original deposited chain IDs."
    },
    {
      "atomspec": "#315.1/5,A,B,F",
      "category": "subcomplex",
      "comment": "U5 snRNP",
      "label": "U5 snRNP",
      "name": "pdb_5MQF_U5_snRNP",
      "section": "Named selections for subcomplexes using original deposited chain IDs."
    },
    {
      "atomspec": "#315.1/6",
      "category": "subcomplex",
      "comment": "U6 snRNP",
      "label": "U6 snRNP",
      "name": "pdb_5MQF_U6_snRNP",
      "section": "Named selections for subcomplexes using original deposited chain IDs."
    },
    {
      "atomspec": "#315.1/Y:59-67,135-157|#315.1/Z:47-58",
      "category": "substrate RNA feature",
      "comment": "substrate RNA: residues 47-58; 59-67;135-157, component, medium confidence, validation not_applicable",
      "label": "substrate RNA",
      "name": "Cstar_5MQF_substrate",
      "section": "Named selections for resolved substrate RNA features."
    },
    {
      "atomspec": "#315.1/Y:59-64",
      "category": "substrate RNA feature",
      "comment": "5' splice site: residues 59-64, sequence-motif, medium confidence, validation uncertain uncertain validation",
      "label": "5' splice site",
      "name": "Cstar_5MQF_5SS",
      "section": "Named selections for resolved substrate RNA features."
    },
    {
      "atomspec": "#315.1/Y:59-67,135-157",
      "category": "substrate RNA feature",
      "comment": "intron: residues 59-67;135-157, splice-site-inference, medium confidence, validation not_applicable",
      "label": "intron",
      "name": "Cstar_5MQF_intron",
      "section": "Named selections for resolved substrate RNA features."
    },
    {
      "atomspec": "#315.1/Y:150-156",
      "category": "substrate RNA feature",
      "comment": "branch point region: residues 150-156, network-scored-motif, high confidence, validation validated",
      "label": "branch point region",
      "name": "Cstar_5MQF_branch_region",
      "section": "Named selections for resolved substrate RNA features."
    },
    {
      "atomspec": "#315.1/Y:155",
      "category": "substrate RNA feature",
      "comment": "branch point adenosine: residues 155, network-scored-motif, high confidence, validation validated",
      "label": "branch point adenosine",
      "name": "Cstar_5MQF_branch_A",
      "section": "Named selections for resolved substrate RNA features."
    },
    {
      "atomspec": "#315.1/Z:47-58",
      "category": "substrate RNA feature",
      "comment": "5' exon: residues 47-58, splice-site-inference, medium confidence, validation not_applicable",
      "label": "5' exon",
      "name": "Cstar_5MQF_5exon",
      "section": "Named selections for resolved substrate RNA features."
    },
    {
      "atomspec": "#315.1/2:26-30",
      "category": "snRNA feature",
      "comment": "U2 snRNA U2/U6 helix I partner: residues 26-30, review-region, high confidence",
      "label": "U2 snRNA U2/U6 helix I partner",
      "name": "Cstar_5MQF_U2_U6_helix_I_partner",
      "section": "Named selections for resolved snRNA functional regions."
    },
    {
      "atomspec": "#315.1/2:32-41",
      "category": "snRNA feature",
      "comment": "U2 snRNA branchpoint pairing region: residues 32-41, sequence-motif-neighborhood, medium confidence",
      "label": "U2 snRNA branchpoint pairing region",
      "name": "Cstar_5MQF_U2_branchpoint_pairing_region",
      "section": "Named selections for resolved snRNA functional regions."
    },
    {
      "atomspec": "#315.1/2:46-60",
      "category": "snRNA feature",
      "comment": "U2 snRNA stem IIa: residues 46-60, review-region, low confidence",
      "label": "U2 snRNA stem IIa",
      "name": "Cstar_5MQF_U2_stem_IIa",
      "section": "Named selections for resolved snRNA functional regions."
    },
    {
      "atomspec": "#315.1/2:99-105",
      "category": "snRNA feature",
      "comment": "U2 snRNA Sm site: residues 99-105, sequence-motif, medium confidence",
      "label": "U2 snRNA Sm site",
      "name": "Cstar_5MQF_U2_Sm_site",
      "section": "Named selections for resolved snRNA functional regions."
    },
    {
      "atomspec": "#315.1/5:38-42",
      "category": "snRNA feature",
      "comment": "U5 snRNA loop I: residues 38-42, sequence-motif, medium confidence",
      "label": "U5 snRNA loop I",
      "name": "Cstar_5MQF_U5_loop_I",
      "section": "Named selections for resolved snRNA functional regions."
    },
    {
      "atomspec": "#315.1/6:1-28",
      "category": "snRNA feature",
      "comment": "U6 snRNA 5' terminal stem-loop: residues 1-28, reference-alignment, high confidence",
      "label": "U6 snRNA 5' terminal stem-loop",
      "name": "Cstar_5MQF_U6_5_terminal_stem_loop",
      "section": "Named selections for resolved snRNA functional regions."
    },
    {
      "atomspec": "#315.1/6:36-60",
      "category": "snRNA feature",
      "comment": "U6 snRNA U2/U6 helix I partner: residues 36-60, motif-neighborhood, medium confidence",
      "label": "U6 snRNA U2/U6 helix I partner",
      "name": "Cstar_5MQF_U6_U2_helix_I_partner",
      "section": "Named selections for resolved snRNA functional regions."
    },
    {
      "atomspec": "#315.1/6:38-49",
      "category": "snRNA feature",
      "comment": "U6 snRNA 5' splice-site upstream contact: residues 38-49, motif-neighborhood, medium confidence",
      "label": "U6 snRNA 5' splice-site upstream contact",
      "name": "Cstar_5MQF_U6_5SS_upstream_contact",
      "section": "Named selections for resolved snRNA functional regions."
    },
    {
      "atomspec": "#315.1/6:41-47",
      "category": "snRNA feature",
      "comment": "U6 snRNA ACAGAGA box: residues 41-47, sequence-motif, high confidence",
      "label": "U6 snRNA ACAGAGA box",
      "name": "Cstar_5MQF_U6_ACAGAGA_box",
      "section": "Named selections for resolved snRNA functional regions."
    },
    {
      "atomspec": "#315.1/6:79-96",
      "category": "snRNA feature",
      "comment": "U6 snRNA internal stem-loop: residues 79-96, motif-neighborhood, low confidence",
      "label": "U6 snRNA internal stem-loop",
      "name": "Cstar_5MQF_U6_ISL",
      "section": "Named selections for resolved snRNA functional regions."
    },
    {
      "atomspec": "#315.1/6:92-94",
      "category": "snRNA feature",
      "comment": "U6 snRNA AGC catalytic triad: residues 92-94, sequence-motif, medium confidence",
      "label": "U6 snRNA AGC catalytic triad",
      "name": "Cstar_5MQF_U6_AGC_catalytic_triad",
      "section": "Named selections for resolved snRNA functional regions."
    }
  ],
  "structure_group_id": "315",
  "structure_model_id": "315.1"
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
