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
  "pdb_id": "8i0t",
  "selectors": [
    {
      "atomspec": "#387.1/V",
      "category": "subcomplex",
      "comment": "EJC/mRNP",
      "label": "EJC/mRNP",
      "name": "pdb_8I0T_EJC_mRNP",
      "section": "Named selections for subcomplexes using original deposited chain IDs."
    },
    {
      "atomspec": "#387.1/I,J,N,O,Q,R,S,y",
      "category": "subcomplex",
      "comment": "NTC/NTR related",
      "label": "NTC/NTR related",
      "name": "pdb_8I0T_NTC_NTR_related",
      "section": "Named selections for subcomplexes using original deposited chain IDs."
    },
    {
      "atomspec": "#387.1/L,P,T,Z,q,r,s,t",
      "category": "subcomplex",
      "comment": "NTC/PRP19",
      "label": "NTC/PRP19",
      "name": "pdb_8I0T_NTC_PRP19",
      "section": "Named selections for subcomplexes using original deposited chain IDs."
    },
    {
      "atomspec": "#387.1/G",
      "category": "subcomplex",
      "comment": "RNA/substrate",
      "label": "RNA/substrate",
      "name": "pdb_8I0T_RNA_substrate",
      "section": "Named selections for subcomplexes using original deposited chain IDs."
    },
    {
      "atomspec": "#387.1/U",
      "category": "subcomplex",
      "comment": "SR proteins",
      "label": "SR proteins",
      "name": "pdb_8I0T_SR_proteins",
      "section": "Named selections for subcomplexes using original deposited chain IDs."
    },
    {
      "atomspec": "#387.1/W",
      "category": "subcomplex",
      "comment": "Second step factors",
      "label": "Second step factors",
      "name": "pdb_8I0T_Second_step_factors",
      "section": "Named selections for subcomplexes using original deposited chain IDs."
    },
    {
      "atomspec": "#387.1/h,i,j,k,l,m,n",
      "category": "subcomplex",
      "comment": "U2 Sm ring",
      "label": "U2 Sm ring",
      "name": "pdb_8I0T_U2_Sm_ring",
      "section": "Named selections for subcomplexes using original deposited chain IDs."
    },
    {
      "atomspec": "#387.1/H,o,p",
      "category": "subcomplex",
      "comment": "U2 snRNP",
      "label": "U2 snRNP",
      "name": "pdb_8I0T_U2_snRNP",
      "section": "Named selections for subcomplexes using original deposited chain IDs."
    },
    {
      "atomspec": "#387.1/1,2,3,4,5,7,u,v,w",
      "category": "subcomplex",
      "comment": "U2/SF3B",
      "label": "U2/SF3B",
      "name": "pdb_8I0T_U2_SF3B",
      "section": "Named selections for subcomplexes using original deposited chain IDs."
    },
    {
      "atomspec": "#387.1/a,b,c,d,e,f,g",
      "category": "subcomplex",
      "comment": "U5 Sm ring",
      "label": "U5 Sm ring",
      "name": "pdb_8I0T_U5_Sm_ring",
      "section": "Named selections for subcomplexes using original deposited chain IDs."
    },
    {
      "atomspec": "#387.1/A,B,C,D,E",
      "category": "subcomplex",
      "comment": "U5 snRNP",
      "label": "U5 snRNP",
      "name": "pdb_8I0T_U5_snRNP",
      "section": "Named selections for subcomplexes using original deposited chain IDs."
    },
    {
      "atomspec": "#387.1/F",
      "category": "subcomplex",
      "comment": "U6 snRNP",
      "label": "U6 snRNP",
      "name": "pdb_8I0T_U6_snRNP",
      "section": "Named selections for subcomplexes using original deposited chain IDs."
    },
    {
      "atomspec": "#387.1/9,K,X,Y",
      "category": "subcomplex",
      "comment": "other",
      "label": "other",
      "name": "pdb_8I0T_other",
      "section": "Named selections for subcomplexes using original deposited chain IDs."
    },
    {
      "atomspec": "#387.1/G:-12-0",
      "category": "substrate RNA feature",
      "comment": "5' exon: residues -12-0, splice-site-inference, medium confidence, validation not_applicable",
      "label": "5' exon",
      "name": "Bact_8I0T_5exon",
      "section": "Named selections for resolved substrate RNA features."
    },
    {
      "atomspec": "#387.1/G:-12-24,83-117",
      "category": "substrate RNA feature",
      "comment": "substrate RNA: residues -12-24;83-117, component, medium confidence, validation not_applicable",
      "label": "substrate RNA",
      "name": "Bact_8I0T_substrate",
      "section": "Named selections for resolved substrate RNA features."
    },
    {
      "atomspec": "#387.1/G:1-6",
      "category": "substrate RNA feature",
      "comment": "5' splice site: residues 1-6, sequence-motif, medium confidence, validation uncertain uncertain validation",
      "label": "5' splice site",
      "name": "Bact_8I0T_5SS",
      "section": "Named selections for resolved substrate RNA features."
    },
    {
      "atomspec": "#387.1/G:1-24,83-117",
      "category": "substrate RNA feature",
      "comment": "intron: residues 1-24;83-117, splice-site-inference, medium confidence, validation not_applicable",
      "label": "intron",
      "name": "Bact_8I0T_intron",
      "section": "Named selections for resolved substrate RNA features."
    },
    {
      "atomspec": "#387.1/G:92-98",
      "category": "substrate RNA feature",
      "comment": "branch point region: residues 92-98, network-scored-motif, high confidence, validation validated",
      "label": "branch point region",
      "name": "Bact_8I0T_branch_region",
      "section": "Named selections for resolved substrate RNA features."
    },
    {
      "atomspec": "#387.1/G:97",
      "category": "substrate RNA feature",
      "comment": "branch point adenosine: residues 97, network-scored-motif, high confidence, validation validated",
      "label": "branch point adenosine",
      "name": "Bact_8I0T_branch_A",
      "section": "Named selections for resolved substrate RNA features."
    },
    {
      "atomspec": "#387.1/G:103-116",
      "category": "substrate RNA feature",
      "comment": "polypyrimidine tract: residues 103-116, sequence-motif, medium confidence, validation validated",
      "label": "polypyrimidine tract",
      "name": "Bact_8I0T_PPT",
      "section": "Named selections for resolved substrate RNA features."
    },
    {
      "atomspec": "#387.1/H:26-30",
      "category": "snRNA feature",
      "comment": "U2 snRNA U2/U6 helix I partner: residues 26-30, review-region, high confidence",
      "label": "U2 snRNA U2/U6 helix I partner",
      "name": "Bact_8I0T_U2_U6_helix_I_partner",
      "section": "Named selections for resolved snRNA functional regions."
    },
    {
      "atomspec": "#387.1/H:32-41",
      "category": "snRNA feature",
      "comment": "U2 snRNA branchpoint pairing region: residues 32-41, sequence-motif-neighborhood, medium confidence",
      "label": "U2 snRNA branchpoint pairing region",
      "name": "Bact_8I0T_U2_branchpoint_pairing_region",
      "section": "Named selections for resolved snRNA functional regions."
    },
    {
      "atomspec": "#387.1/H:46-65,68-74,78-80",
      "category": "snRNA feature",
      "comment": "U2 snRNA stem IIa: residues 46-65;68-74;78-80, review-region, low confidence",
      "label": "U2 snRNA stem IIa",
      "name": "Bact_8I0T_U2_stem_IIa",
      "section": "Named selections for resolved snRNA functional regions."
    },
    {
      "atomspec": "#387.1/H:99-105",
      "category": "snRNA feature",
      "comment": "U2 snRNA Sm site: residues 99-105, sequence-motif, medium confidence",
      "label": "U2 snRNA Sm site",
      "name": "Bact_8I0T_U2_Sm_site",
      "section": "Named selections for resolved snRNA functional regions."
    },
    {
      "atomspec": "#387.1/B:38-42",
      "category": "snRNA feature",
      "comment": "U5 snRNA loop I: residues 38-42, sequence-motif, medium confidence",
      "label": "U5 snRNA loop I",
      "name": "Bact_8I0T_U5_loop_I",
      "section": "Named selections for resolved snRNA functional regions."
    },
    {
      "atomspec": "#387.1/F:1-30",
      "category": "snRNA feature",
      "comment": "U6 snRNA 5' terminal stem-loop: residues 1-30, reference-alignment, high confidence",
      "label": "U6 snRNA 5' terminal stem-loop",
      "name": "Bact_8I0T_U6_5_terminal_stem_loop",
      "section": "Named selections for resolved snRNA functional regions."
    },
    {
      "atomspec": "#387.1/F:35-60",
      "category": "snRNA feature",
      "comment": "U6 snRNA U2/U6 helix I partner: residues 35-60, motif-neighborhood, medium confidence",
      "label": "U6 snRNA U2/U6 helix I partner",
      "name": "Bact_8I0T_U6_U2_helix_I_partner",
      "section": "Named selections for resolved snRNA functional regions."
    },
    {
      "atomspec": "#387.1/F:38-49",
      "category": "snRNA feature",
      "comment": "U6 snRNA 5' splice-site upstream contact: residues 38-49, motif-neighborhood, medium confidence",
      "label": "U6 snRNA 5' splice-site upstream contact",
      "name": "Bact_8I0T_U6_5SS_upstream_contact",
      "section": "Named selections for resolved snRNA functional regions."
    },
    {
      "atomspec": "#387.1/F:41-47",
      "category": "snRNA feature",
      "comment": "U6 snRNA ACAGAGA box: residues 41-47, sequence-motif, high confidence",
      "label": "U6 snRNA ACAGAGA box",
      "name": "Bact_8I0T_U6_ACAGAGA_box",
      "section": "Named selections for resolved snRNA functional regions."
    },
    {
      "atomspec": "#387.1/F:79-97",
      "category": "snRNA feature",
      "comment": "U6 snRNA internal stem-loop: residues 79-97, motif-neighborhood, low confidence",
      "label": "U6 snRNA internal stem-loop",
      "name": "Bact_8I0T_U6_ISL",
      "section": "Named selections for resolved snRNA functional regions."
    },
    {
      "atomspec": "#387.1/F:92-94",
      "category": "snRNA feature",
      "comment": "U6 snRNA AGC catalytic triad: residues 92-94, sequence-motif, medium confidence",
      "label": "U6 snRNA AGC catalytic triad",
      "name": "Bact_8I0T_U6_AGC_catalytic_triad",
      "section": "Named selections for resolved snRNA functional regions."
    }
  ],
  "structure_group_id": "387",
  "structure_model_id": "387.1"
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
