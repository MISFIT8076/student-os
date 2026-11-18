"""Build the blind second-annotator grading sheet from the eval dataset.

    python study_kit/build_annotator_sheet.py

Produces study_kit/annotator_sheet.xlsx: every item from all 40 scenarios, with
a fillable 0-3 "Your grade" column. It deliberately does NOT show the original
(gold) grades, so the second rater judges independently. Feed the filled sheet
to backend/eval/annotator_agreement.py to compute Cohen's kappa.
"""
from __future__ import annotations

import json
from pathlib import Path

from openpyxl import Workbook
from openpyxl.styles import Alignment, Font, PatternFill
from openpyxl.worksheet.datavalidation import DataValidation

REPO = Path(__file__).resolve().parents[1]
DATASET = REPO / "backend" / "eval" / "dataset.json"
OUT = REPO / "study_kit" / "annotator_sheet.xlsx"

ARIAL = "Arial"
HEAD_FILL = PatternFill("solid", fgColor="2F6BFF")
YELLOW = PatternFill("solid", fgColor="FFF3B0")
HEAD_FONT = Font(name=ARIAL, bold=True, color="FFFFFF")
BODY = Font(name=ARIAL)


def _due_hint(offset):
    if offset is None:
        return ""
    if offset <= 0:
        return "due today"
    if offset == 1:
        return "due tomorrow"
    return f"in {offset} days"


def main() -> None:
    data = json.loads(DATASET.read_text())
    wb = Workbook()

    # ── Instructions sheet ────────────────────────────────────────────────
    ins = wb.active
    ins.title = "Instructions"
    lines = [
        ("Student OS — Second-Annotator Grading Sheet", True),
        ("", False),
        ("You are grading how important each item is to do TODAY, from your own judgment.", False),
        ("Do NOT look at anyone else's grades — judge independently.", False),
        ("", False),
        ("Relevance scale (enter one number in the yellow 'Your grade' column):", True),
        ("  3 = must do today", False),
        ("  2 = important, do soon", False),
        ("  1 = optional / nice to do", False),
        ("  0 = noise (e.g. an OTP, a promo, an old notification)", False),
        ("", False),
        ("Use the 'Scenario context' to picture the situation for each block of items.", False),
        ("Grade every row on the 'Grading' sheet. Then send the file back.", False),
        ("", False),
        ("Example:", True),
    ]
    for i, (text, bold) in enumerate(lines, start=1):
        c = ins.cell(row=i, column=1, value=text)
        c.font = Font(name=ARIAL, bold=bold, size=14 if (bold and i == 1) else 11)
    # Example mini-table
    ex_row = len(lines) + 1
    ex_headers = ["Source", "Kind", "Item", "Due", "Your grade (0-3)"]
    ex_values = ["gmail", "email", "Internship application closes", "due tomorrow", 3]
    for j, (hh, vv) in enumerate(zip(ex_headers, ex_values), start=1):
        hcell = ins.cell(row=ex_row, column=j, value=hh); hcell.font = HEAD_FONT; hcell.fill = HEAD_FILL
        vcell = ins.cell(row=ex_row + 1, column=j, value=vv); vcell.font = BODY
        if j == 5:
            vcell.fill = YELLOW
    ins.column_dimensions["A"].width = 40
    for col in "BCDE":
        ins.column_dimensions[col].width = 16
    ins.column_dimensions["C"].width = 34

    # ── Grading sheet ─────────────────────────────────────────────────────
    gs = wb.create_sheet("Grading")
    headers = ["No.", "Scenario", "Scenario context", "Source", "Kind",
               "Item", "Due", "Your grade (0-3)", "Notes"]
    for j, hname in enumerate(headers, start=1):
        c = gs.cell(row=1, column=j, value=hname)
        c.font = HEAD_FONT; c.fill = HEAD_FILL
        c.alignment = Alignment(vertical="center", wrap_text=True)
    gs.freeze_panes = "A2"

    dv = DataValidation(type="list", formula1='"0,1,2,3"', allow_blank=True)
    gs.add_data_validation(dv)

    r = 2
    n = 0
    for sc in data["scenarios"]:
        for idx, it in enumerate(sc["items"]):
            n += 1
            row = [n, sc["id"], sc["context"], it["source"], it["kind"],
                   it["title"], _due_hint(it.get("due_offset_days")), None, None]
            for j, val in enumerate(row, start=1):
                cell = gs.cell(row=r, column=j, value=val)
                cell.font = BODY
                cell.alignment = Alignment(vertical="top", wrap_text=(j in (3, 6)))
            grade_cell = gs.cell(row=r, column=8)
            grade_cell.fill = YELLOW
            dv.add(grade_cell)
            r += 1

    widths = {"A": 5, "B": 22, "C": 34, "D": 11, "E": 12, "F": 40, "G": 12, "H": 15, "I": 24}
    for col, w in widths.items():
        gs.column_dimensions[col].width = w

    OUT.parent.mkdir(parents=True, exist_ok=True)
    wb.save(OUT)
    print(f"Wrote {OUT} — {n} items across {len(data['scenarios'])} scenarios.")


if __name__ == "__main__":
    main()
