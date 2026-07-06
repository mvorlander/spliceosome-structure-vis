#!/usr/bin/env python3
"""Open a small ChimeraX browser for generated named selections."""

from __future__ import annotations

import json
import sys

from chimerax.core.commands import run


def _ui_available(session) -> bool:
    return bool(getattr(getattr(session, "ui", None), "is_gui", False))


def _id_tuple(model_id: str) -> tuple[int, ...]:
    return tuple(int(part) for part in str(model_id).split(".") if part)


def _model_by_id(session, model_id: str):
    if not model_id:
        return None
    models = session.models.list(model_id=_id_tuple(model_id))
    return models[0] if models else None


def _parent_model_ids(model_id: str) -> list[str]:
    parts = str(model_id).split(".")
    return [".".join(parts[:idx]) for idx in range(1, len(parts))]


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
    from Qt.QtGui import QColor, QBrush, QFont
    from Qt.QtWidgets import (
        QHBoxLayout,
        QLabel,
        QLineEdit,
        QPushButton,
        QTreeWidget,
        QTreeWidgetItem,
        QVBoxLayout,
    )

    class SpliceosomeSelectionBrowser(ToolInstance):
        SESSION_ENDURING = False
        SESSION_SAVE = False

        def __init__(self, session, tool_name, spec, selectors):
            super().__init__(session, tool_name)
            self.spec = spec
            self.selectors = selectors
            self.filtered = list(selectors)
            self._populating = False
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
            self.tree = QTreeWidget(parent)
            self.tree.setColumnCount(4)
            self.tree.setHeaderLabels(["Selection", "Target", "Selector", "Label"])
            self.tree.setAlternatingRowColors(True)
            self.tree.setRootIsDecorated(True)
            self.tree.setUniformRowHeights(False)
            layout.addWidget(self.tree)
            buttons = QHBoxLayout()
            self.select_button = QPushButton("Select + Zoom", parent)
            self.show_labels_button = QPushButton("Show Labels", parent)
            self.hide_labels_button = QPushButton("Hide Labels", parent)
            self.clear_button = QPushButton("Clear", parent)
            buttons.addWidget(self.select_button)
            buttons.addWidget(self.show_labels_button)
            buttons.addWidget(self.hide_labels_button)
            buttons.addWidget(self.clear_button)
            layout.addLayout(buttons)

            self.search.textChanged.connect(self._filter)
            self.tree.itemClicked.connect(self._activate_item)
            self.tree.itemDoubleClicked.connect(self._activate_item)
            self.tree.itemChanged.connect(self._label_checkbox_changed)
            self.select_button.clicked.connect(self._activate_current)
            self.show_labels_button.clicked.connect(lambda: self._set_all_filtered_labels(True))
            self.hide_labels_button.clicked.connect(lambda: self._set_all_filtered_labels(False))
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
            self._populating = True
            self.tree.clear()
            grouped = {}
            for item in self.filtered:
                family = item.get("family") or (
                    "RNA" if "RNA" in item.get("category", "") else "Protein/RNP groups"
                )
                group = item.get("group") or item.get("category") or "other selections"
                grouped.setdefault(family, {}).setdefault(group, []).append(item)

            family_order = ["RNA", "Protein/RNP groups", "Other"]
            for family in sorted(grouped, key=lambda value: (family_order.index(value) if value in family_order else 99, value)):
                family_count = sum(len(items) for items in grouped[family].values())
                family_item = QTreeWidgetItem([f"{family} ({family_count})", "", "", ""])
                self._style_group_item(family_item, family)
                self.tree.addTopLevelItem(family_item)
                for group in sorted(grouped[family]):
                    rows = sorted(grouped[family][group], key=lambda value: (value.get("label") or value.get("name", "")).lower())
                    group_item = QTreeWidgetItem([f"{group} ({len(rows)})", "", "", ""])
                    self._style_group_item(group_item, group)
                    family_item.addChild(group_item)
                    for data in rows:
                        label = data.get("label") or data.get("name")
                        atomspec = data.get("atomspec", "")
                        selector = data.get("name", "")
                        has_label = bool(data.get("label_model_id"))
                        row = QTreeWidgetItem([f"  {label}", atomspec, selector, ""])
                        row.setData(0, Qt.UserRole, data)
                        if has_label:
                            row.setFlags(row.flags() | Qt.ItemIsUserCheckable)
                            row.setCheckState(3, Qt.Checked if self._label_visible(data) else Qt.Unchecked)
                            row.setToolTip(3, "Show or hide the corresponding 3D RNA feature label")
                        else:
                            row.setText(3, "")
                        self._style_leaf_item(row, data)
                        group_item.addChild(row)
            self.tree.expandAll()
            for column in range(3):
                self.tree.resizeColumnToContents(column)
            self.tree.resizeColumnToContents(3)
            self._populating = False

        def _style_group_item(self, item, label):
            font = item.font(0)
            font.setBold(True)
            item.setFont(0, font)
            item.setForeground(0, QBrush(QColor("#20242a")))
            item.setBackground(0, QBrush(QColor("#eef2f7")))

        def _style_leaf_item(self, item, data):
            color = QColor(data.get("color") or "#9CA3AF")
            pale = QColor(color)
            pale.setAlpha(45)
            for column in range(3):
                item.setBackground(column, QBrush(pale))
            item.setForeground(0, QBrush(color))
            font = item.font(0)
            font.setBold(True)
            item.setFont(0, font)
            item.setToolTip(
                0,
                f"{data.get('label') or data.get('name')}\n"
                f"{data.get('category', '')} / {data.get('group', '')}\n"
                f"{data.get('comment', '')}",
            )

        def _label_visible(self, data):
            model_id = data.get("label_model_id", "")
            model = _model_by_id(self.session, model_id)
            if model is None:
                return bool(data.get("label_default_visible"))
            if not getattr(model, "display", True):
                return False
            for parent_id in _parent_model_ids(model_id):
                parent = _model_by_id(self.session, parent_id)
                if parent is not None and not getattr(parent, "display", True):
                    return False
            return True

        def _set_label_visible(self, data, visible):
            model_id = data.get("label_model_id", "")
            model = _model_by_id(self.session, model_id)
            if model is None:
                self.session.logger.warning(f"RNA label model #{model_id} is not open")
                return
            if visible:
                for parent_id in _parent_model_ids(model_id):
                    parent = _model_by_id(self.session, parent_id)
                    if parent is not None:
                        parent.display = True
            model.display = bool(visible)

        def _label_checkbox_changed(self, item, column):
            if self._populating or column != 3:
                return
            data = item.data(0, Qt.UserRole)
            if not data or not data.get("label_model_id"):
                return
            self._set_label_visible(data, item.checkState(3) == Qt.Checked)

        def _set_all_filtered_labels(self, visible):
            self._populating = True
            root = self.tree.invisibleRootItem()
            for item in self._iter_items(root):
                data = item.data(0, Qt.UserRole)
                if not data or not data.get("label_model_id"):
                    continue
                self._set_label_visible(data, visible)
                item.setCheckState(3, Qt.Checked if visible else Qt.Unchecked)
            self._populating = False

        def _iter_items(self, item):
            for index in range(item.childCount()):
                child = item.child(index)
                yield child
                yield from self._iter_items(child)

        def _activate_current(self):
            item = self.tree.currentItem()
            if item is not None:
                self._activate_item(item)

        def _activate_item(self, item, column=0):
            if column == 3:
                return
            data = item.data(0, Qt.UserRole)
            if not data:
                return
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
  "pdb_id": "9l5r",
  "selectors": [
    {
      "atomspec": "#425.1/Cb",
      "category": "subcomplex",
      "color": "#FF69B4",
      "comment": "Disassembly factors",
      "family": "Protein/RNP groups",
      "feature": "",
      "group": "disassembly factors",
      "group_key": "",
      "kind": "subcomplex",
      "label": "Disassembly factors",
      "name": "pdb_9L5R_Disassembly_factors",
      "section": "Named selections for subcomplexes using original deposited chain IDs."
    },
    {
      "atomspec": "#425.1/0,B,Ci,I,J,M,N,R,S,U,Y",
      "category": "subcomplex",
      "color": "#F4BF67",
      "comment": "NTC/NTR related",
      "family": "Protein/RNP groups",
      "feature": "",
      "group": "NTC/NTR groups",
      "group_key": "",
      "kind": "subcomplex",
      "label": "NTC/NTR related",
      "name": "pdb_9L5R_NTC_NTR_related",
      "section": "Named selections for subcomplexes using original deposited chain IDs."
    },
    {
      "atomspec": "#425.1/K,L,P,T,q,r,s,t",
      "category": "subcomplex",
      "color": "#F4BF67",
      "comment": "NTC/PRP19",
      "family": "Protein/RNP groups",
      "feature": "",
      "group": "NTC/NTR groups",
      "group_key": "",
      "kind": "subcomplex",
      "label": "NTC/PRP19",
      "name": "pdb_9L5R_NTC_PRP19",
      "section": "Named selections for subcomplexes using original deposited chain IDs."
    },
    {
      "atomspec": "#425.1/7",
      "category": "subcomplex",
      "color": "#303030",
      "comment": "RNA/substrate",
      "family": "RNA",
      "feature": "",
      "group": "pre-mRNA features",
      "group_key": "",
      "kind": "subcomplex",
      "label": "RNA/substrate",
      "name": "pdb_9L5R_RNA_substrate",
      "section": "Named selections for subcomplexes using original deposited chain IDs."
    },
    {
      "atomspec": "#425.1/W",
      "category": "subcomplex",
      "color": "#9CA3AF",
      "comment": "Second step factors",
      "family": "Protein/RNP groups",
      "feature": "",
      "group": "other protein/RNP groups",
      "group_key": "",
      "kind": "subcomplex",
      "label": "Second step factors",
      "name": "pdb_9L5R_Second_step_factors",
      "section": "Named selections for subcomplexes using original deposited chain IDs."
    },
    {
      "atomspec": "#425.1/a,b,c,d,e,f,g",
      "category": "subcomplex",
      "color": "#BFE6BF",
      "comment": "U2 Sm ring",
      "family": "Protein/RNP groups",
      "feature": "",
      "group": "U2/SF3B groups",
      "group_key": "",
      "kind": "subcomplex",
      "label": "U2 Sm ring",
      "name": "pdb_9L5R_U2_Sm_ring",
      "section": "Named selections for subcomplexes using original deposited chain IDs."
    },
    {
      "atomspec": "#425.1/2,Cc,h,i",
      "category": "subcomplex",
      "color": "#2F8B4D",
      "comment": "U2 snRNP",
      "family": "Protein/RNP groups",
      "feature": "",
      "group": "U2/SF3B groups",
      "group_key": "",
      "kind": "subcomplex",
      "label": "U2 snRNP",
      "name": "pdb_9L5R_U2_snRNP",
      "section": "Named selections for subcomplexes using original deposited chain IDs."
    },
    {
      "atomspec": "#425.1/j,k,l,m,o,p,u",
      "category": "subcomplex",
      "color": "#BFC3E8",
      "comment": "U5 Sm ring",
      "family": "Protein/RNP groups",
      "feature": "",
      "group": "U5 snRNP groups",
      "group_key": "",
      "kind": "subcomplex",
      "label": "U5 Sm ring",
      "name": "pdb_9L5R_U5_Sm_ring",
      "section": "Named selections for subcomplexes using original deposited chain IDs."
    },
    {
      "atomspec": "#425.1/5,A,C,E",
      "category": "subcomplex",
      "color": "#0000CD",
      "comment": "U5 snRNP",
      "family": "Protein/RNP groups",
      "feature": "",
      "group": "U5 snRNP groups",
      "group_key": "",
      "kind": "subcomplex",
      "label": "U5 snRNP",
      "name": "pdb_9L5R_U5_snRNP",
      "section": "Named selections for subcomplexes using original deposited chain IDs."
    },
    {
      "atomspec": "#425.1/6",
      "category": "subcomplex",
      "color": "#DC143C",
      "comment": "U6 snRNP",
      "family": "Protein/RNP groups",
      "feature": "",
      "group": "U6 snRNP groups",
      "group_key": "",
      "kind": "subcomplex",
      "label": "U6 snRNP",
      "name": "pdb_9L5R_U6_snRNP",
      "section": "Named selections for subcomplexes using original deposited chain IDs."
    },
    {
      "atomspec": "#425.1/CY,D,F,H",
      "category": "subcomplex",
      "color": "#9CA3AF",
      "comment": "other",
      "family": "Protein/RNP groups",
      "feature": "",
      "group": "other protein/RNP groups",
      "group_key": "",
      "kind": "subcomplex",
      "label": "other",
      "name": "pdb_9L5R_other",
      "section": "Named selections for subcomplexes using original deposited chain IDs."
    },
    {
      "atomspec": "#425.1/2:26-30",
      "category": "snRNA feature",
      "color": "#047857",
      "comment": "U2 snRNA U2/U6 helix I partner: residues 26-30, review-region, high confidence",
      "family": "RNA",
      "feature": "U2_U6_helix_I_partner",
      "group": "snRNA-snRNA interacting regions",
      "group_key": "snRNA_snRNA_regions",
      "kind": "rna_feature",
      "label": "U2 snRNA U2/U6 helix I partner",
      "label_category_model_id": "425.2.1",
      "label_default_visible": "",
      "label_group_model_id": "425.2",
      "label_model_id": "425.2.1.1",
      "name": "ILS_disassembly_9L5R_U2_U6_helix_I_partner",
      "section": "Named selections for resolved snRNA functional regions."
    },
    {
      "atomspec": "#425.1/2:31-40",
      "category": "snRNA feature",
      "color": "#0B6E2D",
      "comment": "U2 snRNA branchpoint pairing region: residues 31-40, sequence-motif-neighborhood, medium confidence",
      "family": "RNA",
      "feature": "U2_branchpoint_pairing_region",
      "group": "snRNA-pre-mRNA regions",
      "group_key": "snRNA_pre_mRNA_regions",
      "kind": "rna_feature",
      "label": "U2 snRNA branchpoint pairing region",
      "label_category_model_id": "425.2.2",
      "label_default_visible": "true",
      "label_group_model_id": "425.2",
      "label_model_id": "425.2.2.1",
      "name": "ILS_disassembly_9L5R_U2_branchpoint_pairing_region",
      "section": "Named selections for resolved snRNA functional regions."
    },
    {
      "atomspec": "#425.1/2:52-60",
      "category": "snRNA feature",
      "color": "#167A38",
      "comment": "U2 snRNA stem IIa: residues 52-60, review-region, low confidence",
      "family": "RNA",
      "feature": "U2_stem_IIa",
      "group": "internal stem loops",
      "group_key": "internal_stem_loops",
      "kind": "rna_feature",
      "label": "U2 snRNA stem IIa",
      "label_category_model_id": "425.2.3",
      "label_default_visible": "",
      "label_group_model_id": "425.2",
      "label_model_id": "425.2.3.1",
      "name": "ILS_disassembly_9L5R_U2_stem_IIa",
      "section": "Named selections for resolved snRNA functional regions."
    },
    {
      "atomspec": "#425.1/2:98-104",
      "category": "snRNA feature",
      "color": "#2F8B4D",
      "comment": "U2 snRNA Sm site: residues 98-104, sequence-motif, medium confidence",
      "family": "RNA",
      "feature": "U2_Sm_site",
      "group": "other snRNA regions",
      "group_key": "other_snRNA_regions",
      "kind": "rna_feature",
      "label": "U2 snRNA Sm site",
      "name": "ILS_disassembly_9L5R_U2_Sm_site",
      "section": "Named selections for resolved snRNA functional regions."
    },
    {
      "atomspec": "#425.1/5:37-41",
      "category": "snRNA feature",
      "color": "#1B3CD0",
      "comment": "U5 snRNA loop I: residues 37-41, sequence-motif, medium confidence",
      "family": "RNA",
      "feature": "U5_loop_I",
      "group": "snRNA-pre-mRNA regions",
      "group_key": "snRNA_pre_mRNA_regions",
      "kind": "rna_feature",
      "label": "U5 snRNA loop I",
      "label_category_model_id": "425.2.2",
      "label_default_visible": "true",
      "label_group_model_id": "425.2",
      "label_model_id": "425.2.2.2",
      "name": "ILS_disassembly_9L5R_U5_loop_I",
      "section": "Named selections for resolved snRNA functional regions."
    },
    {
      "atomspec": "#425.1/6:28-53",
      "category": "snRNA feature",
      "color": "#D0183C",
      "comment": "U6 snRNA U2/U6 helix I partner: residues 28-53, motif-neighborhood, medium confidence",
      "family": "RNA",
      "feature": "U6_U2_helix_I_partner",
      "group": "snRNA-snRNA interacting regions",
      "group_key": "snRNA_snRNA_regions",
      "kind": "rna_feature",
      "label": "U6 snRNA U2/U6 helix I partner",
      "label_category_model_id": "425.2.1",
      "label_default_visible": "",
      "label_group_model_id": "425.2",
      "label_model_id": "425.2.1.2",
      "name": "ILS_disassembly_9L5R_U6_U2_helix_I_partner",
      "section": "Named selections for resolved snRNA functional regions."
    },
    {
      "atomspec": "#425.1/6:31-42",
      "category": "snRNA feature",
      "color": "#E01842",
      "comment": "U6 snRNA 5' splice-site upstream contact: residues 31-42, motif-neighborhood, medium confidence",
      "family": "RNA",
      "feature": "U6_5SS_upstream_contact",
      "group": "other snRNA regions",
      "group_key": "other_snRNA_regions",
      "kind": "rna_feature",
      "label": "U6 snRNA 5' splice-site upstream contact",
      "label_category_model_id": "425.2.2",
      "label_default_visible": "true",
      "label_group_model_id": "425.2",
      "label_model_id": "425.2.2.3",
      "name": "ILS_disassembly_9L5R_U6_5SS_upstream_contact",
      "section": "Named selections for resolved snRNA functional regions."
    },
    {
      "atomspec": "#425.1/6:33-60",
      "category": "snRNA feature",
      "color": "#D61A3D",
      "comment": "U6 snRNA internal stem-loop: residues 33-60, motif-neighborhood, low confidence",
      "family": "RNA",
      "feature": "U6_ISL",
      "group": "internal stem loops",
      "group_key": "internal_stem_loops",
      "kind": "rna_feature",
      "label": "U6 snRNA internal stem-loop",
      "label_category_model_id": "425.2.3",
      "label_default_visible": "",
      "label_group_model_id": "425.2",
      "label_model_id": "425.2.3.2",
      "name": "ILS_disassembly_9L5R_U6_ISL",
      "section": "Named selections for resolved snRNA functional regions."
    },
    {
      "atomspec": "#425.1/6:34-40",
      "category": "snRNA feature",
      "color": "#DC143C",
      "comment": "U6 snRNA ACAGAGA box: residues 34-40, sequence-motif, high confidence",
      "family": "RNA",
      "feature": "U6_ACAGAGA_box",
      "group": "other snRNA regions",
      "group_key": "other_snRNA_regions",
      "kind": "rna_feature",
      "label": "U6 snRNA ACAGAGA box",
      "label_category_model_id": "425.2.4",
      "label_default_visible": "",
      "label_group_model_id": "425.2",
      "label_model_id": "425.2.4.1",
      "name": "ILS_disassembly_9L5R_U6_ACAGAGA_box",
      "section": "Named selections for resolved snRNA functional regions."
    },
    {
      "atomspec": "#425.1/6:46-48",
      "category": "snRNA feature",
      "color": "#C91236",
      "comment": "U6 snRNA AGC catalytic triad: residues 46-48, sequence-motif, medium confidence",
      "family": "RNA",
      "feature": "U6_AGC_catalytic_triad",
      "group": "catalytic core regions",
      "group_key": "catalytic_core_regions",
      "kind": "rna_feature",
      "label": "U6 snRNA AGC catalytic triad",
      "label_category_model_id": "425.2.5",
      "label_default_visible": "",
      "label_group_model_id": "425.2",
      "label_model_id": "425.2.5.1",
      "name": "ILS_disassembly_9L5R_U6_AGC_catalytic_triad",
      "section": "Named selections for resolved snRNA functional regions."
    },
    {
      "atomspec": "#425.1/6:92-98",
      "category": "snRNA feature",
      "color": "#E33A55",
      "comment": "U6 snRNA LSm site: residues 92-98, terminal-region, low confidence",
      "family": "RNA",
      "feature": "U6_LSm_site",
      "group": "other snRNA regions",
      "group_key": "other_snRNA_regions",
      "kind": "rna_feature",
      "label": "U6 snRNA LSm site",
      "name": "ILS_disassembly_9L5R_U6_LSm_site",
      "section": "Named selections for resolved snRNA functional regions."
    }
  ],
  "structure_group_id": "425",
  "structure_model_id": "425.1"
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
