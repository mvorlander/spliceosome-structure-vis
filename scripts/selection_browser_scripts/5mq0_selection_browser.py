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
  "pdb_id": "5mq0",
  "selectors": [
    {
      "atomspec": "#314.1/H",
      "category": "subcomplex",
      "color": "#EAA439",
      "comment": "EJC/mRNP",
      "family": "Protein/RNP groups",
      "feature": "",
      "group": "EJC/mRNP groups",
      "group_key": "",
      "kind": "subcomplex",
      "label": "EJC/mRNP",
      "name": "pdb_5MQ0_EJC_mRNP",
      "section": "Named selections for subcomplexes using original deposited chain IDs."
    },
    {
      "atomspec": "#314.1/K,L,M,N,S,T,y",
      "category": "subcomplex",
      "color": "#F4BF67",
      "comment": "NTC/NTR related",
      "family": "Protein/RNP groups",
      "feature": "",
      "group": "NTC/NTR groups",
      "group_key": "",
      "kind": "subcomplex",
      "label": "NTC/NTR related",
      "name": "pdb_5MQ0_NTC_NTR_related",
      "section": "Named selections for subcomplexes using original deposited chain IDs."
    },
    {
      "atomspec": "#314.1/J,O,P,t,u,v,w",
      "category": "subcomplex",
      "color": "#F4BF67",
      "comment": "NTC/PRP19",
      "family": "Protein/RNP groups",
      "feature": "",
      "group": "NTC/NTR groups",
      "group_key": "",
      "kind": "subcomplex",
      "label": "NTC/PRP19",
      "name": "pdb_5MQ0_NTC_PRP19",
      "section": "Named selections for subcomplexes using original deposited chain IDs."
    },
    {
      "atomspec": "#314.1/2,3,5,6,E,I",
      "category": "subcomplex",
      "color": "#303030",
      "comment": "RNA/substrate",
      "family": "RNA",
      "feature": "",
      "group": "pre-mRNA features",
      "group_key": "",
      "kind": "subcomplex",
      "label": "RNA/substrate",
      "name": "pdb_5MQ0_RNA_substrate",
      "section": "Named selections for subcomplexes using original deposited chain IDs."
    },
    {
      "atomspec": "#314.1/V,c,o",
      "category": "subcomplex",
      "color": "#9CA3AF",
      "comment": "Second step factors",
      "family": "Protein/RNP groups",
      "feature": "",
      "group": "other protein/RNP groups",
      "group_key": "",
      "kind": "subcomplex",
      "label": "Second step factors",
      "name": "pdb_5MQ0_Second_step_factors",
      "section": "Named selections for subcomplexes using original deposited chain IDs."
    },
    {
      "atomspec": "#314.1/b,d,e,f,g,h,j,k,l,m,n,p,q,r",
      "category": "subcomplex",
      "color": "#9CA3AF",
      "comment": "Sm ring",
      "family": "Protein/RNP groups",
      "feature": "",
      "group": "other protein/RNP groups",
      "group_key": "",
      "kind": "subcomplex",
      "label": "Sm ring",
      "name": "pdb_5MQ0_Sm_ring",
      "section": "Named selections for subcomplexes using original deposited chain IDs."
    },
    {
      "atomspec": "#314.1/W,Y",
      "category": "subcomplex",
      "color": "#2F8B4D",
      "comment": "U2 snRNP",
      "family": "Protein/RNP groups",
      "feature": "",
      "group": "U2/SF3B groups",
      "group_key": "",
      "kind": "subcomplex",
      "label": "U2 snRNP",
      "name": "pdb_5MQ0_U2_snRNP",
      "section": "Named selections for subcomplexes using original deposited chain IDs."
    },
    {
      "atomspec": "#314.1/A,C",
      "category": "subcomplex",
      "color": "#0000CD",
      "comment": "U5 snRNP",
      "family": "Protein/RNP groups",
      "feature": "",
      "group": "U5 snRNP groups",
      "group_key": "",
      "kind": "subcomplex",
      "label": "U5 snRNP",
      "name": "pdb_5MQ0_U5_snRNP",
      "section": "Named selections for subcomplexes using original deposited chain IDs."
    },
    {
      "atomspec": "#314.1/R,X,a,s",
      "category": "subcomplex",
      "color": "#9CA3AF",
      "comment": "other",
      "family": "Protein/RNP groups",
      "feature": "",
      "group": "other protein/RNP groups",
      "group_key": "",
      "kind": "subcomplex",
      "label": "other",
      "name": "pdb_5MQ0_other",
      "section": "Named selections for subcomplexes using original deposited chain IDs."
    },
    {
      "atomspec": "#314.1/2:1-49,55-73,78-84,98-104,139-150|#314.1/E:-16--1",
      "category": "substrate RNA feature",
      "color": "#FF8C00",
      "comment": "5' exon: residues -16--1; 1-49;55-73;78-84;98-104;139-150, component-name/splice-site-inference, high/medium confidence, validation not_applicable",
      "family": "RNA",
      "feature": "exon_5",
      "group": "pre-mRNA features",
      "group_key": "pre_mRNA_features",
      "kind": "rna_feature",
      "label": "5' exon",
      "label_category_model_id": "314.2.1",
      "label_default_visible": "true",
      "label_group_model_id": "314.2",
      "label_model_id": "314.2.1.1",
      "name": "Cstar_5MQ0_5exon",
      "section": "Named selections for resolved substrate RNA features."
    },
    {
      "atomspec": "#314.1/2:1-49,55-73,78-84,98-104,139-150,1089-1108,1117-1129,1138-1154,1159-1169|#314.1/3:1-3|#314.1/5:4-53,62-145,167-173|#314.1/6:1-10,16-104|#314.1/E:-16--1|#314.1/I:1-16,56-73",
      "category": "substrate RNA feature",
      "color": "#303030",
      "comment": "substrate RNA: residues -16--1; 1-10;16-104; 1-16;56-73; 1-3; 1-49;55-73;78-84;98-104;139-150;1089-1108;1117-1129;1138-1154;1159-1169; 4-53;62-145;167-173, component, medium confidence, validation not_applicable",
      "family": "RNA",
      "feature": "substrate",
      "group": "pre-mRNA features",
      "group_key": "pre_mRNA_features",
      "kind": "rna_feature",
      "label": "substrate RNA",
      "name": "Cstar_5MQ0_substrate",
      "section": "Named selections for resolved substrate RNA features."
    },
    {
      "atomspec": "#314.1/2:1089|#314.1/E:-16--1",
      "category": "substrate RNA feature",
      "color": "#303030",
      "comment": "intron: residues -16--1; 1089, five-ss-inference/splice-site-inference, low/medium confidence, validation not_applicable",
      "family": "RNA",
      "feature": "intron",
      "group": "pre-mRNA features",
      "group_key": "pre_mRNA_features",
      "kind": "rna_feature",
      "label": "intron",
      "label_category_model_id": "314.2.1",
      "label_default_visible": "true",
      "label_group_model_id": "314.2",
      "label_model_id": "314.2.1.2",
      "name": "Cstar_5MQ0_intron",
      "section": "Named selections for resolved substrate RNA features."
    },
    {
      "atomspec": "#314.1/2:1089|#314.1/5:133-135",
      "category": "substrate RNA feature",
      "color": "#303030",
      "comment": "3' splice site: residues 1089; 133-135, sequence-motif, medium confidence, validation validated",
      "family": "RNA",
      "feature": "three_prime_splice_site",
      "group": "pre-mRNA features",
      "group_key": "pre_mRNA_features",
      "kind": "rna_feature",
      "label": "3' splice site",
      "label_category_model_id": "314.2.1",
      "label_default_visible": "true",
      "label_group_model_id": "314.2",
      "label_model_id": "314.2.1.3",
      "name": "Cstar_5MQ0_3SS",
      "section": "Named selections for resolved substrate RNA features."
    },
    {
      "atomspec": "#314.1/2:1090-1108,1117-1129,1138-1154,1159-1169|#314.1/3:1-3",
      "category": "substrate RNA feature",
      "color": "#D97706",
      "comment": "3' exon: residues 1-3; 1090-1108;1117-1129;1138-1154;1159-1169, component-name/splice-site-inference, high/medium confidence, validation not_applicable",
      "family": "RNA",
      "feature": "exon_3",
      "group": "pre-mRNA features",
      "group_key": "pre_mRNA_features",
      "kind": "rna_feature",
      "label": "3' exon",
      "label_category_model_id": "314.2.1",
      "label_default_visible": "true",
      "label_group_model_id": "314.2",
      "label_model_id": "314.2.1.4",
      "name": "Cstar_5MQ0_3exon",
      "section": "Named selections for resolved substrate RNA features."
    },
    {
      "atomspec": "#314.1/5:72-76|#314.1/I:65-71",
      "category": "substrate RNA feature",
      "color": "#303030",
      "comment": "branch point region: residues 65-71; 72-76, network-scored-motif, medium/review confidence, validation uncertain uncertain validation",
      "family": "RNA",
      "feature": "branch_point_region",
      "group": "pre-mRNA features",
      "group_key": "pre_mRNA_features",
      "kind": "rna_feature",
      "label": "branch point region",
      "label_category_model_id": "314.2.1",
      "label_default_visible": "true",
      "label_group_model_id": "314.2",
      "label_model_id": "314.2.1.5",
      "name": "Cstar_5MQ0_branch_region",
      "section": "Named selections for resolved substrate RNA features."
    },
    {
      "atomspec": "#314.1/5:94-99",
      "category": "substrate RNA feature",
      "color": "#303030",
      "comment": "polypyrimidine tract: residues 94-99, sequence-motif, medium confidence, validation uncertain uncertain validation",
      "family": "RNA",
      "feature": "polypyrimidine_tract",
      "group": "pre-mRNA features",
      "group_key": "pre_mRNA_features",
      "kind": "rna_feature",
      "label": "polypyrimidine tract",
      "label_category_model_id": "314.2.1",
      "label_default_visible": "true",
      "label_group_model_id": "314.2",
      "label_model_id": "314.2.1.6",
      "name": "Cstar_5MQ0_PPT",
      "section": "Named selections for resolved substrate RNA features."
    },
    {
      "atomspec": "#314.1/E:-16--12",
      "category": "substrate RNA feature",
      "color": "#303030",
      "comment": "5' splice site: residues -16--12, sequence-motif, medium confidence, validation uncertain uncertain validation",
      "family": "RNA",
      "feature": "five_prime_splice_site",
      "group": "pre-mRNA features",
      "group_key": "pre_mRNA_features",
      "kind": "rna_feature",
      "label": "5' splice site",
      "label_category_model_id": "314.2.1",
      "label_default_visible": "true",
      "label_group_model_id": "314.2",
      "label_model_id": "314.2.1.7",
      "name": "Cstar_5MQ0_5SS",
      "section": "Named selections for resolved substrate RNA features."
    }
  ],
  "structure_group_id": "314",
  "structure_model_id": "314.1"
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
