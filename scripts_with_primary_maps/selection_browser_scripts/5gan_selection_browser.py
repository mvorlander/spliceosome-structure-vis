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
  "pdb_id": "5gan",
  "selectors": [
    {
      "atomspec": "#305.1/k,l,m,n,p,q,r",
      "category": "subcomplex",
      "comment": "U4 Sm ring",
      "label": "U4 Sm ring",
      "name": "pdb_5GAN_U4_Sm_ring",
      "section": "Named selections for subcomplexes using original deposited chain IDs."
    },
    {
      "atomspec": "#305.1/V",
      "category": "subcomplex",
      "comment": "U4 snRNP",
      "label": "U4 snRNP",
      "name": "pdb_5GAN_U4_snRNP",
      "section": "Named selections for subcomplexes using original deposited chain IDs."
    },
    {
      "atomspec": "#305.1/D,F,G,H,K",
      "category": "subcomplex",
      "comment": "U4/U6 snRNP",
      "label": "U4/U6 snRNP",
      "name": "pdb_5GAN_U4_U6_snRNP",
      "section": "Named selections for subcomplexes using original deposited chain IDs."
    },
    {
      "atomspec": "#305.1/b,d,e,f,g,h,j",
      "category": "subcomplex",
      "comment": "U5 Sm ring",
      "label": "U5 Sm ring",
      "name": "pdb_5GAN_U5_Sm_ring",
      "section": "Named selections for subcomplexes using original deposited chain IDs."
    },
    {
      "atomspec": "#305.1/A,B,C,E,J,U",
      "category": "subcomplex",
      "comment": "U5 snRNP",
      "label": "U5 snRNP",
      "name": "pdb_5GAN_U5_snRNP",
      "section": "Named selections for subcomplexes using original deposited chain IDs."
    },
    {
      "atomspec": "#305.1/2,3,4,5,6,7,8",
      "category": "subcomplex",
      "comment": "U6 LSm",
      "label": "U6 LSm",
      "name": "pdb_5GAN_U6_LSm",
      "section": "Named selections for subcomplexes using original deposited chain IDs."
    },
    {
      "atomspec": "#305.1/W",
      "category": "subcomplex",
      "comment": "U6 snRNP",
      "label": "U6 snRNP",
      "name": "pdb_5GAN_U6_snRNP",
      "section": "Named selections for subcomplexes using original deposited chain IDs."
    },
    {
      "atomspec": "#305.1/x",
      "category": "subcomplex",
      "comment": "other",
      "label": "other",
      "name": "pdb_5GAN_other",
      "section": "Named selections for subcomplexes using original deposited chain IDs."
    },
    {
      "atomspec": "#305.1/V:1-18",
      "category": "snRNA feature",
      "comment": "U4 snRNA U4/U6 stem I partner: residues 1-18, reference-alignment, high confidence",
      "label": "U4 snRNA U4/U6 stem I partner",
      "name": "U5_tri_snRNP_5GAN_U4_U6_stem_I_partner",
      "section": "Named selections for resolved snRNA functional regions."
    },
    {
      "atomspec": "#305.1/V:57-64",
      "category": "snRNA feature",
      "comment": "U4 snRNA U4/U6 stem II partner: residues 57-64, reference-alignment, high confidence",
      "label": "U4 snRNA U4/U6 stem II partner",
      "name": "U5_tri_snRNP_5GAN_U4_U6_stem_II_partner",
      "section": "Named selections for resolved snRNA functional regions."
    },
    {
      "atomspec": "#305.1/V:60-67,73-95",
      "category": "snRNA feature",
      "comment": "U4 snRNA Brr2 loading region: residues 60-67;73-95, review-region, low confidence",
      "label": "U4 snRNA Brr2 loading region",
      "name": "U5_tri_snRNP_5GAN_U4_Brr2_loading_region",
      "section": "Named selections for resolved snRNA functional regions."
    },
    {
      "atomspec": "#305.1/V:144-150",
      "category": "snRNA feature",
      "comment": "U4 snRNA Sm site: residues 144-150, sequence-motif, medium confidence",
      "label": "U4 snRNA Sm site",
      "name": "U5_tri_snRNP_5GAN_U4_Sm_site",
      "section": "Named selections for resolved snRNA functional regions."
    },
    {
      "atomspec": "#305.1/U:53",
      "category": "snRNA feature",
      "comment": "U5 snRNA loop I: residues 53, sequence-motif, medium confidence",
      "label": "U5 snRNA loop I",
      "name": "U5_tri_snRNP_5GAN_U5_loop_I",
      "section": "Named selections for resolved snRNA functional regions."
    },
    {
      "atomspec": "#305.1/W:1-9,16-30",
      "category": "snRNA feature",
      "comment": "U6 snRNA 5' terminal stem-loop: residues 1-9;16-30, reference-alignment, high confidence",
      "label": "U6 snRNA 5' terminal stem-loop",
      "name": "U5_tri_snRNP_5GAN_U6_5_terminal_stem_loop",
      "section": "Named selections for resolved snRNA functional regions."
    },
    {
      "atomspec": "#305.1/W:44-51,55-66",
      "category": "snRNA feature",
      "comment": "U6 snRNA U2/U6 helix I partner: residues 44-51;55-66, motif-neighborhood, medium confidence",
      "label": "U6 snRNA U2/U6 helix I partner",
      "name": "U5_tri_snRNP_5GAN_U6_U2_helix_I_partner",
      "section": "Named selections for resolved snRNA functional regions."
    },
    {
      "atomspec": "#305.1/W:44-51,55",
      "category": "snRNA feature",
      "comment": "U6 snRNA 5' splice-site upstream contact: residues 44-51;55, motif-neighborhood, medium confidence",
      "label": "U6 snRNA 5' splice-site upstream contact",
      "name": "U5_tri_snRNP_5GAN_U6_5SS_upstream_contact",
      "section": "Named selections for resolved snRNA functional regions."
    },
    {
      "atomspec": "#305.1/W:46-51,55-73",
      "category": "snRNA feature",
      "comment": "U6 snRNA internal stem-loop: residues 46-51;55-73, motif-neighborhood, low confidence",
      "label": "U6 snRNA internal stem-loop",
      "name": "U5_tri_snRNP_5GAN_U6_ISL",
      "section": "Named selections for resolved snRNA functional regions."
    },
    {
      "atomspec": "#305.1/W:47-51",
      "category": "snRNA feature",
      "comment": "U6 snRNA ACAGAGA box: residues 47-51, sequence-motif, high confidence",
      "label": "U6 snRNA ACAGAGA box",
      "name": "U5_tri_snRNP_5GAN_U6_ACAGAGA_box",
      "section": "Named selections for resolved snRNA functional regions."
    },
    {
      "atomspec": "#305.1/W:55-68",
      "category": "snRNA feature",
      "comment": "U6 snRNA U4/U6 stem II partner: residues 55-68, reference-alignment, high confidence",
      "label": "U6 snRNA U4/U6 stem II partner",
      "name": "U5_tri_snRNP_5GAN_U6_U4_stem_II_partner",
      "section": "Named selections for resolved snRNA functional regions."
    },
    {
      "atomspec": "#305.1/W:59-61",
      "category": "snRNA feature",
      "comment": "U6 snRNA AGC catalytic triad: residues 59-61, sequence-motif, medium confidence",
      "label": "U6 snRNA AGC catalytic triad",
      "name": "U5_tri_snRNP_5GAN_U6_AGC_catalytic_triad",
      "section": "Named selections for resolved snRNA functional regions."
    },
    {
      "atomspec": "#305.1/W:70-80",
      "category": "snRNA feature",
      "comment": "U6 snRNA U4/U6 stem I partner: residues 70-80, reference-alignment, high confidence",
      "label": "U6 snRNA U4/U6 stem I partner",
      "name": "U5_tri_snRNP_5GAN_U6_U4_stem_I_partner",
      "section": "Named selections for resolved snRNA functional regions."
    },
    {
      "atomspec": "#305.1/W:108-112",
      "category": "snRNA feature",
      "comment": "U6 snRNA LSm site: residues 108-112, terminal-region, low confidence",
      "label": "U6 snRNA LSm site",
      "name": "U5_tri_snRNP_5GAN_U6_LSm_site",
      "section": "Named selections for resolved snRNA functional regions."
    }
  ],
  "structure_group_id": "305",
  "structure_model_id": "305.1"
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
