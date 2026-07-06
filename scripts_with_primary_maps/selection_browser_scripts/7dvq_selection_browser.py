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
  "pdb_id": "7dvq",
  "selectors": [
    {
      "atomspec": "#361.1/G:-11-0",
      "category": "substrate RNA feature",
      "comment": "5' exon: residues -11-0, five-ss-inference, medium confidence, validation not_applicable",
      "label": "5' exon",
      "name": "Bact_7DVQ_5exon",
      "section": "Named selections for resolved substrate RNA features."
    },
    {
      "atomspec": "#361.1/G:-11-19,191-222",
      "category": "substrate RNA feature",
      "comment": "substrate RNA: residues -11-19;191-222, component, medium confidence, validation not_applicable",
      "label": "substrate RNA",
      "name": "Bact_7DVQ_substrate",
      "section": "Named selections for resolved substrate RNA features."
    },
    {
      "atomspec": "#361.1/G:1-9",
      "category": "substrate RNA feature",
      "comment": "5' splice site: residues 1-9, minor-snrna-basepair, high confidence, validation validated",
      "label": "5' splice site",
      "name": "Bact_7DVQ_5SS",
      "section": "Named selections for resolved substrate RNA features."
    },
    {
      "atomspec": "#361.1/G:1-19,191-222",
      "category": "substrate RNA feature",
      "comment": "intron from 5' splice site: residues 1-19;191-222, five-ss-inference, medium confidence, validation not_applicable",
      "label": "intron from 5' splice site",
      "name": "Bact_7DVQ_intron",
      "section": "Named selections for resolved substrate RNA features."
    },
    {
      "atomspec": "#361.1/G:195-206",
      "category": "substrate RNA feature",
      "comment": "branch point region: residues 195-206, network-scored-motif, high confidence, validation validated",
      "label": "branch point region",
      "name": "Bact_7DVQ_branch_region",
      "section": "Named selections for resolved substrate RNA features."
    },
    {
      "atomspec": "#361.1/G:203",
      "category": "substrate RNA feature",
      "comment": "branch point adenosine: residues 203, network-scored-motif, high confidence, validation validated",
      "label": "branch point adenosine",
      "name": "Bact_7DVQ_branch_A",
      "section": "Named selections for resolved substrate RNA features."
    },
    {
      "atomspec": "#361.1/H:2-11",
      "category": "snRNA feature",
      "comment": "U12 snRNA U12/U6atac helix I partner: residues 2-11, reference-alignment, high confidence",
      "label": "U12 snRNA U12/U6atac helix I partner",
      "name": "Bact_7DVQ_U12_U6atac_helix_I_partner",
      "section": "Named selections for resolved snRNA functional regions."
    },
    {
      "atomspec": "#361.1/H:16-26",
      "category": "snRNA feature",
      "comment": "U12 snRNA branchpoint pairing region: residues 16-26, reference-alignment, high confidence",
      "label": "U12 snRNA branchpoint pairing region",
      "name": "Bact_7DVQ_U12_branchpoint_pairing_region",
      "section": "Named selections for resolved snRNA functional regions."
    },
    {
      "atomspec": "#361.1/H:75-81",
      "category": "snRNA feature",
      "comment": "U12 snRNA Sm site: residues 75-81, sequence-motif, medium confidence",
      "label": "U12 snRNA Sm site",
      "name": "Bact_7DVQ_U12_Sm_site",
      "section": "Named selections for resolved snRNA functional regions."
    },
    {
      "atomspec": "#361.1/B:38-42",
      "category": "snRNA feature",
      "comment": "U5 snRNA loop I: residues 38-42, sequence-motif, medium confidence",
      "label": "U5 snRNA loop I",
      "name": "Bact_7DVQ_U5_loop_I",
      "section": "Named selections for resolved snRNA functional regions."
    },
    {
      "atomspec": "#361.1/F:11-17",
      "category": "snRNA feature",
      "comment": "U6atac snRNA 5' splice-site recognition region: residues 11-17, reference-alignment, high confidence",
      "label": "U6atac snRNA 5' splice-site recognition region",
      "name": "Bact_7DVQ_U6atac_5_5SS_recognition",
      "section": "Named selections for resolved snRNA functional regions."
    },
    {
      "atomspec": "#361.1/F:23-29",
      "category": "snRNA feature",
      "comment": "U6atac snRNA U6atac/U12 helix I partner: residues 23-29, reference-alignment, high confidence",
      "label": "U6atac snRNA U6atac/U12 helix I partner",
      "name": "Bact_7DVQ_U6atac_U12_helix_I_partner",
      "section": "Named selections for resolved snRNA functional regions."
    },
    {
      "atomspec": "#361.1/F:26-28",
      "category": "snRNA feature",
      "comment": "U6atac snRNA AGC catalytic triad: residues 26-28, reference-alignment, high confidence",
      "label": "U6atac snRNA AGC catalytic triad",
      "name": "Bact_7DVQ_U6atac_AGC_catalytic_triad",
      "section": "Named selections for resolved snRNA functional regions."
    },
    {
      "atomspec": "#361.1/F:52-56,61-65",
      "category": "snRNA feature",
      "comment": "U6atac snRNA internal stem-loop: residues 52-56;61-65, reference-alignment, medium confidence",
      "label": "U6atac snRNA internal stem-loop",
      "name": "Bact_7DVQ_U6atac_ISL",
      "section": "Named selections for resolved snRNA functional regions."
    }
  ],
  "structure_group_id": "361",
  "structure_model_id": "361.1"
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
