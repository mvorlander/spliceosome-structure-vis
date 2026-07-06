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
  "pdb_id": "5zwm",
  "selectors": [
    {
      "atomspec": "#326.1/G",
      "category": "subcomplex",
      "comment": "RNA/substrate",
      "label": "RNA/substrate",
      "name": "pdb_5ZWM_RNA_substrate",
      "section": "Named selections for subcomplexes using original deposited chain IDs."
    },
    {
      "atomspec": "#326.1/h,i,j,k,l,m,n",
      "category": "subcomplex",
      "comment": "U2 Sm ring",
      "label": "U2 Sm ring",
      "name": "pdb_5ZWM_U2_Sm_ring",
      "section": "Named selections for subcomplexes using original deposited chain IDs."
    },
    {
      "atomspec": "#326.1/H,o,p",
      "category": "subcomplex",
      "comment": "U2 snRNP",
      "label": "U2 snRNP",
      "name": "pdb_5ZWM_U2_snRNP",
      "section": "Named selections for subcomplexes using original deposited chain IDs."
    },
    {
      "atomspec": "#326.1/1,2,3,4,5,6,u,v,w",
      "category": "subcomplex",
      "comment": "U2/SF3B",
      "label": "U2/SF3B",
      "name": "pdb_5ZWM_U2_SF3B",
      "section": "Named selections for subcomplexes using original deposited chain IDs."
    },
    {
      "atomspec": "#326.1/P,Q,R,S,T,U,V",
      "category": "subcomplex",
      "comment": "U4 Sm ring",
      "label": "U4 Sm ring",
      "name": "pdb_5ZWM_U4_Sm_ring",
      "section": "Named selections for subcomplexes using original deposited chain IDs."
    },
    {
      "atomspec": "#326.1/I",
      "category": "subcomplex",
      "comment": "U4 snRNP",
      "label": "U4 snRNP",
      "name": "pdb_5ZWM_U4_snRNP",
      "section": "Named selections for subcomplexes using original deposited chain IDs."
    },
    {
      "atomspec": "#326.1/E,J,K,L,M",
      "category": "subcomplex",
      "comment": "U4/U6 snRNP",
      "label": "U4/U6 snRNP",
      "name": "pdb_5ZWM_U4_U6_snRNP",
      "section": "Named selections for subcomplexes using original deposited chain IDs."
    },
    {
      "atomspec": "#326.1/a,b,c,d,e,f,g",
      "category": "subcomplex",
      "comment": "U5 Sm ring",
      "label": "U5 Sm ring",
      "name": "pdb_5ZWM_U5_Sm_ring",
      "section": "Named selections for subcomplexes using original deposited chain IDs."
    },
    {
      "atomspec": "#326.1/A,B,C,D,N,O",
      "category": "subcomplex",
      "comment": "U5 snRNP",
      "label": "U5 snRNP",
      "name": "pdb_5ZWM_U5_snRNP",
      "section": "Named selections for subcomplexes using original deposited chain IDs."
    },
    {
      "atomspec": "#326.1/q,r,s,t,x,y,z",
      "category": "subcomplex",
      "comment": "U6 LSm",
      "label": "U6 LSm",
      "name": "pdb_5ZWM_U6_LSm",
      "section": "Named selections for subcomplexes using original deposited chain IDs."
    },
    {
      "atomspec": "#326.1/F",
      "category": "subcomplex",
      "comment": "U6 snRNP",
      "label": "U6 snRNP",
      "name": "pdb_5ZWM_U6_snRNP",
      "section": "Named selections for subcomplexes using original deposited chain IDs."
    },
    {
      "atomspec": "#326.1/X,Y,Z",
      "category": "subcomplex",
      "comment": "other",
      "label": "other",
      "name": "pdb_5ZWM_other",
      "section": "Named selections for subcomplexes using original deposited chain IDs."
    },
    {
      "atomspec": "#326.1/G:479-522",
      "category": "substrate RNA feature",
      "comment": "substrate RNA: residues 479-522, component, medium confidence, validation not_applicable",
      "label": "substrate RNA",
      "name": "pre_B_5ZWM_substrate",
      "section": "Named selections for resolved substrate RNA features."
    },
    {
      "atomspec": "#326.1/G:493-503",
      "category": "substrate RNA feature",
      "comment": "branch point region: residues 493-503, network-scored-motif, high confidence, validation validated",
      "label": "branch point region",
      "name": "pre_B_5ZWM_branch_region",
      "section": "Named selections for resolved substrate RNA features."
    },
    {
      "atomspec": "#326.1/G:501",
      "category": "substrate RNA feature",
      "comment": "branch point adenosine: residues 501, network-scored-motif, high confidence, validation validated",
      "label": "branch point adenosine",
      "name": "pre_B_5ZWM_branch_A",
      "section": "Named selections for resolved substrate RNA features."
    },
    {
      "atomspec": "#326.1/H:33-42",
      "category": "snRNA feature",
      "comment": "U2 snRNA branchpoint pairing region: residues 33-42, sequence-motif-neighborhood, medium confidence",
      "label": "U2 snRNA branchpoint pairing region",
      "name": "pre_B_5ZWM_U2_branchpoint_pairing_region",
      "section": "Named selections for resolved snRNA functional regions."
    },
    {
      "atomspec": "#326.1/H:46-73,79-80",
      "category": "snRNA feature",
      "comment": "U2 snRNA stem IIa: residues 46-73;79-80, review-region, low confidence",
      "label": "U2 snRNA stem IIa",
      "name": "pre_B_5ZWM_U2_stem_IIa",
      "section": "Named selections for resolved snRNA functional regions."
    },
    {
      "atomspec": "#326.1/I:1-18",
      "category": "snRNA feature",
      "comment": "U4 snRNA U4/U6 stem I partner: residues 1-18, reference-alignment, high confidence",
      "label": "U4 snRNA U4/U6 stem I partner",
      "name": "pre_B_5ZWM_U4_U6_stem_I_partner",
      "section": "Named selections for resolved snRNA functional regions."
    },
    {
      "atomspec": "#326.1/I:57-64",
      "category": "snRNA feature",
      "comment": "U4 snRNA U4/U6 stem II partner: residues 57-64, reference-alignment, high confidence",
      "label": "U4 snRNA U4/U6 stem II partner",
      "name": "pre_B_5ZWM_U4_U6_stem_II_partner",
      "section": "Named selections for resolved snRNA functional regions."
    },
    {
      "atomspec": "#326.1/I:60-64,71-79,90-95",
      "category": "snRNA feature",
      "comment": "U4 snRNA Brr2 loading region: residues 60-64;71-79;90-95, review-region, low confidence",
      "label": "U4 snRNA Brr2 loading region",
      "name": "pre_B_5ZWM_U4_Brr2_loading_region",
      "section": "Named selections for resolved snRNA functional regions."
    },
    {
      "atomspec": "#326.1/I:144-150",
      "category": "snRNA feature",
      "comment": "U4 snRNA Sm site: residues 144-150, sequence-motif, medium confidence",
      "label": "U4 snRNA Sm site",
      "name": "pre_B_5ZWM_U4_Sm_site",
      "section": "Named selections for resolved snRNA functional regions."
    },
    {
      "atomspec": "#326.1/B:53",
      "category": "snRNA feature",
      "comment": "U5 snRNA loop I: residues 53, sequence-motif, medium confidence",
      "label": "U5 snRNA loop I",
      "name": "pre_B_5ZWM_U5_loop_I",
      "section": "Named selections for resolved snRNA functional regions."
    },
    {
      "atomspec": "#326.1/F:1-30",
      "category": "snRNA feature",
      "comment": "U6 snRNA 5' terminal stem-loop: residues 1-30, reference-alignment, high confidence",
      "label": "U6 snRNA 5' terminal stem-loop",
      "name": "pre_B_5ZWM_U6_5_terminal_stem_loop",
      "section": "Named selections for resolved snRNA functional regions."
    },
    {
      "atomspec": "#326.1/F:41-51,56-66",
      "category": "snRNA feature",
      "comment": "U6 snRNA U2/U6 helix I partner: residues 41-51;56-66, motif-neighborhood, medium confidence",
      "label": "U6 snRNA U2/U6 helix I partner",
      "name": "pre_B_5ZWM_U6_U2_helix_I_partner",
      "section": "Named selections for resolved snRNA functional regions."
    },
    {
      "atomspec": "#326.1/F:44-51",
      "category": "snRNA feature",
      "comment": "U6 snRNA 5' splice-site upstream contact: residues 44-51, motif-neighborhood, medium confidence",
      "label": "U6 snRNA 5' splice-site upstream contact",
      "name": "pre_B_5ZWM_U6_5SS_upstream_contact",
      "section": "Named selections for resolved snRNA functional regions."
    },
    {
      "atomspec": "#326.1/F:46-51,56-73",
      "category": "snRNA feature",
      "comment": "U6 snRNA internal stem-loop: residues 46-51;56-73, motif-neighborhood, low confidence",
      "label": "U6 snRNA internal stem-loop",
      "name": "pre_B_5ZWM_U6_ISL",
      "section": "Named selections for resolved snRNA functional regions."
    },
    {
      "atomspec": "#326.1/F:47-51",
      "category": "snRNA feature",
      "comment": "U6 snRNA ACAGAGA box: residues 47-51, sequence-motif, high confidence",
      "label": "U6 snRNA ACAGAGA box",
      "name": "pre_B_5ZWM_U6_ACAGAGA_box",
      "section": "Named selections for resolved snRNA functional regions."
    },
    {
      "atomspec": "#326.1/F:56-68",
      "category": "snRNA feature",
      "comment": "U6 snRNA U4/U6 stem II partner: residues 56-68, reference-alignment, high confidence",
      "label": "U6 snRNA U4/U6 stem II partner",
      "name": "pre_B_5ZWM_U6_U4_stem_II_partner",
      "section": "Named selections for resolved snRNA functional regions."
    },
    {
      "atomspec": "#326.1/F:59-61",
      "category": "snRNA feature",
      "comment": "U6 snRNA AGC catalytic triad: residues 59-61, sequence-motif, medium confidence",
      "label": "U6 snRNA AGC catalytic triad",
      "name": "pre_B_5ZWM_U6_AGC_catalytic_triad",
      "section": "Named selections for resolved snRNA functional regions."
    },
    {
      "atomspec": "#326.1/F:70-80",
      "category": "snRNA feature",
      "comment": "U6 snRNA U4/U6 stem I partner: residues 70-80, reference-alignment, high confidence",
      "label": "U6 snRNA U4/U6 stem I partner",
      "name": "pre_B_5ZWM_U6_U4_stem_I_partner",
      "section": "Named selections for resolved snRNA functional regions."
    },
    {
      "atomspec": "#326.1/F:108-112",
      "category": "snRNA feature",
      "comment": "U6 snRNA LSm site: residues 108-112, terminal-region, low confidence",
      "label": "U6 snRNA LSm site",
      "name": "pre_B_5ZWM_U6_LSm_site",
      "section": "Named selections for resolved snRNA functional regions."
    }
  ],
  "structure_group_id": "326",
  "structure_model_id": "326.1"
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
