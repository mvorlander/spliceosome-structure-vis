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
  "pdb_id": "6bk8",
  "selectors": [
    {
      "atomspec": "#332.1/L",
      "category": "subcomplex",
      "comment": "EJC/mRNP",
      "label": "EJC/mRNP",
      "name": "pdb_6BK8_EJC_mRNP",
      "section": "Named selections for subcomplexes using original deposited chain IDs."
    },
    {
      "atomspec": "#332.1/E,F,G,I,R,T,U",
      "category": "subcomplex",
      "comment": "NTC/NTR related",
      "label": "NTC/NTR related",
      "name": "pdb_6BK8_NTC_NTR_related",
      "section": "Named selections for subcomplexes using original deposited chain IDs."
    },
    {
      "atomspec": "#332.1/D,H,S,u,v,w,x",
      "category": "subcomplex",
      "comment": "NTC/PRP19",
      "label": "NTC/PRP19",
      "name": "pdb_6BK8_NTC_PRP19",
      "section": "Named selections for subcomplexes using original deposited chain IDs."
    },
    {
      "atomspec": "#332.1/e,i",
      "category": "subcomplex",
      "comment": "RNA/substrate",
      "label": "RNA/substrate",
      "name": "pdb_6BK8_RNA_substrate",
      "section": "Named selections for subcomplexes using original deposited chain IDs."
    },
    {
      "atomspec": "#332.1/M,O,P",
      "category": "subcomplex",
      "comment": "Second step factors",
      "label": "Second step factors",
      "name": "pdb_6BK8_Second_step_factors",
      "section": "Named selections for subcomplexes using original deposited chain IDs."
    },
    {
      "atomspec": "#332.1/k,l,m,n,o,p,q",
      "category": "subcomplex",
      "comment": "U2 Sm ring",
      "label": "U2 Sm ring",
      "name": "pdb_6BK8_U2_Sm_ring",
      "section": "Named selections for subcomplexes using original deposited chain IDs."
    },
    {
      "atomspec": "#332.1/2,r,s",
      "category": "subcomplex",
      "comment": "U2 snRNP",
      "label": "U2 snRNP",
      "name": "pdb_6BK8_U2_snRNP",
      "section": "Named selections for subcomplexes using original deposited chain IDs."
    },
    {
      "atomspec": "#332.1/a,b,c,d,f,g,h",
      "category": "subcomplex",
      "comment": "U5 Sm ring",
      "label": "U5 Sm ring",
      "name": "pdb_6BK8_U5_Sm_ring",
      "section": "Named selections for subcomplexes using original deposited chain IDs."
    },
    {
      "atomspec": "#332.1/5,A,B",
      "category": "subcomplex",
      "comment": "U5 snRNP",
      "label": "U5 snRNP",
      "name": "pdb_6BK8_U5_snRNP",
      "section": "Named selections for subcomplexes using original deposited chain IDs."
    },
    {
      "atomspec": "#332.1/6",
      "category": "subcomplex",
      "comment": "U6 snRNP",
      "label": "U6 snRNP",
      "name": "pdb_6BK8_U6_snRNP",
      "section": "Named selections for subcomplexes using original deposited chain IDs."
    },
    {
      "atomspec": "#332.1/K,N,X,Y,y",
      "category": "subcomplex",
      "comment": "other",
      "label": "other",
      "name": "pdb_6BK8_other",
      "section": "Named selections for subcomplexes using original deposited chain IDs."
    },
    {
      "atomspec": "#332.1/e:-13,-12,-11,-10,-9,-8,-7,-6,-5,-4,-3,-2,-1,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21|#332.1/i:1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,501,502,503,504,505,506,507,508,509,510,511,512,513,514,515,516,517,518,620,621,622,623,624,625,626,627,628,1001,1002,1003,1004,1005,1006,1007,1008,1110,1111,1112,1113,1114,1115,1116,1117,1118",
      "category": "substrate RNA feature",
      "comment": "substrate RNA: residues -13,-12,-11,-10,-9,-8,-7,-6,-5,-4,-3,-2,-1,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21; 1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,501,502,503,504,505,506,507,508,509,510,511,512,513,514,515,516,517,518,620,621,622,623,624,625,626,627,628,1001,1002,1003,1004,1005,1006,1007,1008,1110,1111,1112,1113,1114,1115,1116,1117,1118, component, medium confidence, validation not_applicable",
      "label": "substrate RNA",
      "name": "P_6BK8_substrate",
      "section": "Named selections for resolved substrate RNA features."
    },
    {
      "atomspec": "#332.1/i:507-517",
      "category": "substrate RNA feature",
      "comment": "branch point region: residues 507-517, network-scored-motif, high confidence, validation validated",
      "label": "branch point region",
      "name": "P_6BK8_branch_region",
      "section": "Named selections for resolved substrate RNA features."
    },
    {
      "atomspec": "#332.1/i:515",
      "category": "substrate RNA feature",
      "comment": "branch point adenosine: residues 515, network-scored-motif, high confidence, validation validated",
      "label": "branch point adenosine",
      "name": "P_6BK8_branch_A",
      "section": "Named selections for resolved substrate RNA features."
    },
    {
      "atomspec": "#332.1/i:518,620,621,622,623,624,625,626,627,628",
      "category": "substrate RNA feature",
      "comment": "polypyrimidine tract: residues 518,620,621,622,623,624,625,626,627,628, sequence-motif, medium confidence, validation uncertain uncertain validation",
      "label": "polypyrimidine tract",
      "name": "P_6BK8_PPT",
      "section": "Named selections for resolved substrate RNA features."
    },
    {
      "atomspec": "#332.1/i:1116-1118",
      "category": "substrate RNA feature",
      "comment": "3' splice site: residues 1116-1118, sequence-motif, medium confidence, validation validated",
      "label": "3' splice site",
      "name": "P_6BK8_3SS",
      "section": "Named selections for resolved substrate RNA features."
    },
    {
      "atomspec": "#332.1/2:26-30",
      "category": "snRNA feature",
      "comment": "U2 snRNA U2/U6 helix I partner: residues 26-30, review-region, high confidence",
      "label": "U2 snRNA U2/U6 helix I partner",
      "name": "P_6BK8_U2_U6_helix_I_partner",
      "section": "Named selections for resolved snRNA functional regions."
    },
    {
      "atomspec": "#332.1/2:33-42",
      "category": "snRNA feature",
      "comment": "U2 snRNA branchpoint pairing region: residues 33-42, sequence-motif-neighborhood, medium confidence",
      "label": "U2 snRNA branchpoint pairing region",
      "name": "P_6BK8_U2_branchpoint_pairing_region",
      "section": "Named selections for resolved snRNA functional regions."
    },
    {
      "atomspec": "#332.1/2:46-47,55-64",
      "category": "snRNA feature",
      "comment": "U2 snRNA stem IIa: residues 46-47;55-64, review-region, low confidence",
      "label": "U2 snRNA stem IIa",
      "name": "P_6BK8_U2_stem_IIa",
      "section": "Named selections for resolved snRNA functional regions."
    },
    {
      "atomspec": "#332.1/5:53-55",
      "category": "snRNA feature",
      "comment": "U5 snRNA loop I: residues 53-55, sequence-motif, medium confidence",
      "label": "U5 snRNA loop I",
      "name": "P_6BK8_U5_loop_I",
      "section": "Named selections for resolved snRNA functional regions."
    },
    {
      "atomspec": "#332.1/6:1-30",
      "category": "snRNA feature",
      "comment": "U6 snRNA 5' terminal stem-loop: residues 1-30, reference-alignment, high confidence",
      "label": "U6 snRNA 5' terminal stem-loop",
      "name": "P_6BK8_U6_5_terminal_stem_loop",
      "section": "Named selections for resolved snRNA functional regions."
    },
    {
      "atomspec": "#332.1/6:41-66",
      "category": "snRNA feature",
      "comment": "U6 snRNA U2/U6 helix I partner: residues 41-66, motif-neighborhood, medium confidence",
      "label": "U6 snRNA U2/U6 helix I partner",
      "name": "P_6BK8_U6_U2_helix_I_partner",
      "section": "Named selections for resolved snRNA functional regions."
    },
    {
      "atomspec": "#332.1/6:44-55",
      "category": "snRNA feature",
      "comment": "U6 snRNA 5' splice-site upstream contact: residues 44-55, motif-neighborhood, medium confidence",
      "label": "U6 snRNA 5' splice-site upstream contact",
      "name": "P_6BK8_U6_5SS_upstream_contact",
      "section": "Named selections for resolved snRNA functional regions."
    },
    {
      "atomspec": "#332.1/6:46-73",
      "category": "snRNA feature",
      "comment": "U6 snRNA internal stem-loop: residues 46-73, motif-neighborhood, low confidence",
      "label": "U6 snRNA internal stem-loop",
      "name": "P_6BK8_U6_ISL",
      "section": "Named selections for resolved snRNA functional regions."
    },
    {
      "atomspec": "#332.1/6:47-53",
      "category": "snRNA feature",
      "comment": "U6 snRNA ACAGAGA box: residues 47-53, sequence-motif, high confidence",
      "label": "U6 snRNA ACAGAGA box",
      "name": "P_6BK8_U6_ACAGAGA_box",
      "section": "Named selections for resolved snRNA functional regions."
    },
    {
      "atomspec": "#332.1/6:59-61",
      "category": "snRNA feature",
      "comment": "U6 snRNA AGC catalytic triad: residues 59-61, sequence-motif, medium confidence",
      "label": "U6 snRNA AGC catalytic triad",
      "name": "P_6BK8_U6_AGC_catalytic_triad",
      "section": "Named selections for resolved snRNA functional regions."
    }
  ],
  "structure_group_id": "332",
  "structure_model_id": "332.1"
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
