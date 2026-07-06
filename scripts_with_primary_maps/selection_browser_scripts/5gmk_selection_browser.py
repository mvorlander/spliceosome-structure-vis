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
  "pdb_id": "5gmk",
  "selectors": [
    {
      "atomspec": "#309.1/Z",
      "category": "subcomplex",
      "comment": "EJC/mRNP",
      "label": "EJC/mRNP",
      "name": "pdb_5GMK_EJC_mRNP",
      "section": "Named selections for subcomplexes using original deposited chain IDs."
    },
    {
      "atomspec": "#309.1/H,I,P,Q,R,T,d,v",
      "category": "subcomplex",
      "comment": "NTC/NTR related",
      "label": "NTC/NTR related",
      "name": "pdb_5GMK_NTC_NTR_related",
      "section": "Named selections for subcomplexes using original deposited chain IDs."
    },
    {
      "atomspec": "#309.1/O,S,c,o,p,q,r",
      "category": "subcomplex",
      "comment": "NTC/PRP19",
      "label": "NTC/PRP19",
      "name": "pdb_5GMK_NTC_PRP19",
      "section": "Named selections for subcomplexes using original deposited chain IDs."
    },
    {
      "atomspec": "#309.1/B,M,N",
      "category": "subcomplex",
      "comment": "RNA/substrate",
      "label": "RNA/substrate",
      "name": "pdb_5GMK_RNA_substrate",
      "section": "Named selections for subcomplexes using original deposited chain IDs."
    },
    {
      "atomspec": "#309.1/n",
      "category": "subcomplex",
      "comment": "Second step factors",
      "label": "Second step factors",
      "name": "pdb_5GMK_Second_step_factors",
      "section": "Named selections for subcomplexes using original deposited chain IDs."
    },
    {
      "atomspec": "#309.1/e,s,u,w,x,y,z",
      "category": "subcomplex",
      "comment": "U2 Sm ring",
      "label": "U2 Sm ring",
      "name": "pdb_5GMK_U2_Sm_ring",
      "section": "Named selections for subcomplexes using original deposited chain IDs."
    },
    {
      "atomspec": "#309.1/F,L,a,b",
      "category": "subcomplex",
      "comment": "U2 snRNP",
      "label": "U2 snRNP",
      "name": "pdb_5GMK_U2_snRNP",
      "section": "Named selections for subcomplexes using original deposited chain IDs."
    },
    {
      "atomspec": "#309.1/g,h,i,j,k,l,m",
      "category": "subcomplex",
      "comment": "U5 Sm ring",
      "label": "U5 Sm ring",
      "name": "pdb_5GMK_U5_Sm_ring",
      "section": "Named selections for subcomplexes using original deposited chain IDs."
    },
    {
      "atomspec": "#309.1/A,C,D",
      "category": "subcomplex",
      "comment": "U5 snRNP",
      "label": "U5 snRNP",
      "name": "pdb_5GMK_U5_snRNP",
      "section": "Named selections for subcomplexes using original deposited chain IDs."
    },
    {
      "atomspec": "#309.1/E",
      "category": "subcomplex",
      "comment": "U6 snRNP",
      "label": "U6 snRNP",
      "name": "pdb_5GMK_U6_snRNP",
      "section": "Named selections for subcomplexes using original deposited chain IDs."
    },
    {
      "atomspec": "#309.1/G,J,t",
      "category": "subcomplex",
      "comment": "other",
      "label": "other",
      "name": "pdb_5GMK_other",
      "section": "Named selections for subcomplexes using original deposited chain IDs."
    },
    {
      "atomspec": "#309.1/B:87-99",
      "category": "substrate RNA feature",
      "comment": "5' exon: residues 87-99, component-name, high confidence, validation not_applicable",
      "label": "5' exon",
      "name": "C_5GMK_5exon",
      "section": "Named selections for resolved substrate RNA features."
    },
    {
      "atomspec": "#309.1/B:87-99|#309.1/M:482-510|#309.1/N:100-114",
      "category": "substrate RNA feature",
      "comment": "substrate RNA: residues 100-114; 482-510; 87-99, component, medium confidence, validation not_applicable",
      "label": "substrate RNA",
      "name": "C_5GMK_substrate",
      "section": "Named selections for resolved substrate RNA features."
    },
    {
      "atomspec": "#309.1/M:482-510",
      "category": "substrate RNA feature",
      "comment": "intron: residues 482-510, component-name, high confidence, validation not_applicable",
      "label": "intron",
      "name": "C_5GMK_intron",
      "section": "Named selections for resolved substrate RNA features."
    },
    {
      "atomspec": "#309.1/M:493-503",
      "category": "substrate RNA feature",
      "comment": "branch point region: residues 493-503, network-scored-motif, high confidence, validation validated",
      "label": "branch point region",
      "name": "C_5GMK_branch_region",
      "section": "Named selections for resolved substrate RNA features."
    },
    {
      "atomspec": "#309.1/M:501",
      "category": "substrate RNA feature",
      "comment": "branch point adenosine: residues 501, network-scored-motif, high confidence, validation validated",
      "label": "branch point adenosine",
      "name": "C_5GMK_branch_A",
      "section": "Named selections for resolved substrate RNA features."
    },
    {
      "atomspec": "#309.1/N:100-114",
      "category": "substrate RNA feature",
      "comment": "5' splice site: residues 100-114, component-name, high confidence, validation validated",
      "label": "5' splice site",
      "name": "C_5GMK_5SS",
      "section": "Named selections for resolved substrate RNA features."
    },
    {
      "atomspec": "#309.1/L:26-30",
      "category": "snRNA feature",
      "comment": "U2 snRNA U2/U6 helix I partner: residues 26-30, review-region, high confidence",
      "label": "U2 snRNA U2/U6 helix I partner",
      "name": "C_5GMK_U2_U6_helix_I_partner",
      "section": "Named selections for resolved snRNA functional regions."
    },
    {
      "atomspec": "#309.1/L:33-42",
      "category": "snRNA feature",
      "comment": "U2 snRNA branchpoint pairing region: residues 33-42, sequence-motif-neighborhood, medium confidence",
      "label": "U2 snRNA branchpoint pairing region",
      "name": "C_5GMK_U2_branchpoint_pairing_region",
      "section": "Named selections for resolved snRNA functional regions."
    },
    {
      "atomspec": "#309.1/L:46-48,54-63,66-75,78-80",
      "category": "snRNA feature",
      "comment": "U2 snRNA stem IIa: residues 46-48;54-63;66-75;78-80, review-region, low confidence",
      "label": "U2 snRNA stem IIa",
      "name": "C_5GMK_U2_stem_IIa",
      "section": "Named selections for resolved snRNA functional regions."
    },
    {
      "atomspec": "#309.1/D:53-55",
      "category": "snRNA feature",
      "comment": "U5 snRNA loop I: residues 53-55, sequence-motif, medium confidence",
      "label": "U5 snRNA loop I",
      "name": "C_5GMK_U5_loop_I",
      "section": "Named selections for resolved snRNA functional regions."
    },
    {
      "atomspec": "#309.1/E:1-30",
      "category": "snRNA feature",
      "comment": "U6 snRNA 5' terminal stem-loop: residues 1-30, reference-alignment, high confidence",
      "label": "U6 snRNA 5' terminal stem-loop",
      "name": "C_5GMK_U6_5_terminal_stem_loop",
      "section": "Named selections for resolved snRNA functional regions."
    },
    {
      "atomspec": "#309.1/E:41-66",
      "category": "snRNA feature",
      "comment": "U6 snRNA U2/U6 helix I partner: residues 41-66, motif-neighborhood, medium confidence",
      "label": "U6 snRNA U2/U6 helix I partner",
      "name": "C_5GMK_U6_U2_helix_I_partner",
      "section": "Named selections for resolved snRNA functional regions."
    },
    {
      "atomspec": "#309.1/E:44-55",
      "category": "snRNA feature",
      "comment": "U6 snRNA 5' splice-site upstream contact: residues 44-55, motif-neighborhood, medium confidence",
      "label": "U6 snRNA 5' splice-site upstream contact",
      "name": "C_5GMK_U6_5SS_upstream_contact",
      "section": "Named selections for resolved snRNA functional regions."
    },
    {
      "atomspec": "#309.1/E:46-73",
      "category": "snRNA feature",
      "comment": "U6 snRNA internal stem-loop: residues 46-73, motif-neighborhood, low confidence",
      "label": "U6 snRNA internal stem-loop",
      "name": "C_5GMK_U6_ISL",
      "section": "Named selections for resolved snRNA functional regions."
    },
    {
      "atomspec": "#309.1/E:47-53",
      "category": "snRNA feature",
      "comment": "U6 snRNA ACAGAGA box: residues 47-53, sequence-motif, high confidence",
      "label": "U6 snRNA ACAGAGA box",
      "name": "C_5GMK_U6_ACAGAGA_box",
      "section": "Named selections for resolved snRNA functional regions."
    },
    {
      "atomspec": "#309.1/E:59-61",
      "category": "snRNA feature",
      "comment": "U6 snRNA AGC catalytic triad: residues 59-61, sequence-motif, medium confidence",
      "label": "U6 snRNA AGC catalytic triad",
      "name": "C_5GMK_U6_AGC_catalytic_triad",
      "section": "Named selections for resolved snRNA functional regions."
    },
    {
      "atomspec": "#309.1/E:103",
      "category": "snRNA feature",
      "comment": "U6 snRNA LSm site: residues 103, terminal-region, low confidence",
      "label": "U6 snRNA LSm site",
      "name": "C_5GMK_U6_LSm_site",
      "section": "Named selections for resolved snRNA functional regions."
    }
  ],
  "structure_group_id": "309",
  "structure_model_id": "309.1"
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
