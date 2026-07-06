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
  "pdb_id": "6qdv",
  "selectors": [
    {
      "atomspec": "#346.1/E:-12--1",
      "category": "substrate RNA feature",
      "comment": "5' exon: residues -12--1, auth-residue-numbering, high confidence, validation not_applicable",
      "label": "5' exon",
      "name": "P_6QDV_5exon",
      "section": "Named selections for resolved substrate RNA features."
    },
    {
      "atomspec": "#346.1/E:-12,-11,-10,-9,-8,-7,-6,-5,-4,-3,-2,-1,1,2",
      "category": "substrate RNA feature",
      "comment": "ligated exons: residues -12,-11,-10,-9,-8,-7,-6,-5,-4,-3,-2,-1,1,2, component-name, high confidence, validation not_applicable",
      "label": "ligated exons",
      "name": "P_6QDV_ligated_exons",
      "section": "Named selections for resolved substrate RNA features."
    },
    {
      "atomspec": "#346.1/E:-12,-11,-10,-9,-8,-7,-6,-5,-4,-3,-2,-1,1,2|#346.1/I:1-20,83-101,111-113",
      "category": "substrate RNA feature",
      "comment": "substrate RNA: residues -12,-11,-10,-9,-8,-7,-6,-5,-4,-3,-2,-1,1,2; 1-20;83-101;111-113, component, medium confidence, validation not_applicable",
      "label": "substrate RNA",
      "name": "P_6QDV_substrate",
      "section": "Named selections for resolved substrate RNA features."
    },
    {
      "atomspec": "#346.1/E:1-2",
      "category": "substrate RNA feature",
      "comment": "3' exon: residues 1-2, auth-residue-numbering, high confidence, validation not_applicable",
      "label": "3' exon",
      "name": "P_6QDV_3exon",
      "section": "Named selections for resolved substrate RNA features."
    },
    {
      "atomspec": "#346.1/I:1-20,83-101,111-113",
      "category": "substrate RNA feature",
      "comment": "intron: residues 1-20;83-101;111-113, component-name, high confidence, validation not_applicable",
      "label": "intron",
      "name": "P_6QDV_intron",
      "section": "Named selections for resolved substrate RNA features."
    },
    {
      "atomspec": "#346.1/I:1-20,83-101,111-113",
      "category": "substrate RNA feature",
      "comment": "intron lariat: residues 1-20;83-101;111-113, component-name, high confidence, validation not_applicable",
      "label": "intron lariat",
      "name": "P_6QDV_intron_lariat",
      "section": "Named selections for resolved substrate RNA features."
    },
    {
      "atomspec": "#346.1/I:93-99",
      "category": "substrate RNA feature",
      "comment": "branch point region: residues 93-99, network-scored-motif, high confidence, validation validated",
      "label": "branch point region",
      "name": "P_6QDV_branch_region",
      "section": "Named selections for resolved substrate RNA features."
    },
    {
      "atomspec": "#346.1/I:97",
      "category": "substrate RNA feature",
      "comment": "branch point adenosine: residues 97, network-scored-motif, high confidence, validation validated",
      "label": "branch point adenosine",
      "name": "P_6QDV_branch_A",
      "section": "Named selections for resolved substrate RNA features."
    },
    {
      "atomspec": "#346.1/I:111-113",
      "category": "substrate RNA feature",
      "comment": "3' splice site: residues 111-113, sequence-motif, medium confidence, validation uncertain uncertain validation",
      "label": "3' splice site",
      "name": "P_6QDV_3SS",
      "section": "Named selections for resolved substrate RNA features."
    },
    {
      "atomspec": "#346.1/2:26-30",
      "category": "snRNA feature",
      "comment": "U2 snRNA U2/U6 helix I partner: residues 26-30, review-region, high confidence",
      "label": "U2 snRNA U2/U6 helix I partner",
      "name": "P_6QDV_U2_U6_helix_I_partner",
      "section": "Named selections for resolved snRNA functional regions."
    },
    {
      "atomspec": "#346.1/2:32-41",
      "category": "snRNA feature",
      "comment": "U2 snRNA branchpoint pairing region: residues 32-41, sequence-motif-neighborhood, medium confidence",
      "label": "U2 snRNA branchpoint pairing region",
      "name": "P_6QDV_U2_branchpoint_pairing_region",
      "section": "Named selections for resolved snRNA functional regions."
    },
    {
      "atomspec": "#346.1/2:46-60",
      "category": "snRNA feature",
      "comment": "U2 snRNA stem IIa: residues 46-60, review-region, low confidence",
      "label": "U2 snRNA stem IIa",
      "name": "P_6QDV_U2_stem_IIa",
      "section": "Named selections for resolved snRNA functional regions."
    },
    {
      "atomspec": "#346.1/2:98-104",
      "category": "snRNA feature",
      "comment": "U2 snRNA Sm site: residues 98-104, sequence-motif, medium confidence",
      "label": "U2 snRNA Sm site",
      "name": "P_6QDV_U2_Sm_site",
      "section": "Named selections for resolved snRNA functional regions."
    },
    {
      "atomspec": "#346.1/5:38-42",
      "category": "snRNA feature",
      "comment": "U5 snRNA loop I: residues 38-42, sequence-motif, medium confidence",
      "label": "U5 snRNA loop I",
      "name": "P_6QDV_U5_loop_I",
      "section": "Named selections for resolved snRNA functional regions."
    },
    {
      "atomspec": "#346.1/6:1-30",
      "category": "snRNA feature",
      "comment": "U6 snRNA 5' terminal stem-loop: residues 1-30, reference-alignment, high confidence",
      "label": "U6 snRNA 5' terminal stem-loop",
      "name": "P_6QDV_U6_5_terminal_stem_loop",
      "section": "Named selections for resolved snRNA functional regions."
    },
    {
      "atomspec": "#346.1/6:35-60",
      "category": "snRNA feature",
      "comment": "U6 snRNA U2/U6 helix I partner: residues 35-60, motif-neighborhood, medium confidence",
      "label": "U6 snRNA U2/U6 helix I partner",
      "name": "P_6QDV_U6_U2_helix_I_partner",
      "section": "Named selections for resolved snRNA functional regions."
    },
    {
      "atomspec": "#346.1/6:38-49",
      "category": "snRNA feature",
      "comment": "U6 snRNA 5' splice-site upstream contact: residues 38-49, motif-neighborhood, medium confidence",
      "label": "U6 snRNA 5' splice-site upstream contact",
      "name": "P_6QDV_U6_5SS_upstream_contact",
      "section": "Named selections for resolved snRNA functional regions."
    },
    {
      "atomspec": "#346.1/6:41-47",
      "category": "snRNA feature",
      "comment": "U6 snRNA ACAGAGA box: residues 41-47, sequence-motif, high confidence",
      "label": "U6 snRNA ACAGAGA box",
      "name": "P_6QDV_U6_ACAGAGA_box",
      "section": "Named selections for resolved snRNA functional regions."
    },
    {
      "atomspec": "#346.1/6:79-97",
      "category": "snRNA feature",
      "comment": "U6 snRNA internal stem-loop: residues 79-97, motif-neighborhood, low confidence",
      "label": "U6 snRNA internal stem-loop",
      "name": "P_6QDV_U6_ISL",
      "section": "Named selections for resolved snRNA functional regions."
    },
    {
      "atomspec": "#346.1/6:92-94",
      "category": "snRNA feature",
      "comment": "U6 snRNA AGC catalytic triad: residues 92-94, sequence-motif, medium confidence",
      "label": "U6 snRNA AGC catalytic triad",
      "name": "P_6QDV_U6_AGC_catalytic_triad",
      "section": "Named selections for resolved snRNA functional regions."
    },
    {
      "atomspec": "#346.1/6:97",
      "category": "snRNA feature",
      "comment": "U6 snRNA LSm site: residues 97, terminal-region, low confidence",
      "label": "U6 snRNA LSm site",
      "name": "P_6QDV_U6_LSm_site",
      "section": "Named selections for resolved snRNA functional regions."
    }
  ],
  "structure_group_id": "346",
  "structure_model_id": "346.1"
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
