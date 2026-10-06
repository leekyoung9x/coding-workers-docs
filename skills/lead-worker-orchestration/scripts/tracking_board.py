#!/usr/bin/env python3
"""Update an owner-facing tracking board (Google Sheet) WITHOUT destroying what the owner built.

Three modes:

  check  --sheet-id <ID>
      Report what the owner has on the sheet: tab name, dimensions, tables (Ctrl+Alt+T),
      data validations, conditional-format rules. Run this BEFORE and AFTER any write.

  set    --sheet-id <ID> --tab "<Tab>" --cell B2=THƯỜNG --cell C2=XONG [--apply]
      Write individual cells. Dry-run unless --apply.

  sync   --sheet-id <ID> --csv status.csv [--apply]
      CSV must carry the board's own header names (ID / Mức / Trạng thái / ...).
      Rows are matched on the ID column and only the named columns are touched.
      Dry-run unless --apply.

Why the preservation report exists: replacing a spreadsheet's contents wholesale erases the
owner's tables, colours, dropdowns and formulas. Every write is followed by a re-read so you
can prove those objects survived instead of asserting it.

Path selection, in order of preference:
  1. Sheets API (`values().update`) - touches cells only, nothing else can be lost.
  2. If the API is not enabled for the project, this script REFUSES by default and prints the
     one-click enablement URL (parsed from the 403 body). Pass --unsafe-file-replace to use the
     export -> edit -> re-upload-same-file-id fallback, which is verified to keep tables and data
     validations but is NOT verified to keep the owner's conditional formatting or manual colours.

Deps (install into a venv, not the system interpreter):
    python3 -m venv ~/.venv-sheet && ~/.venv-sheet/bin/pip install \
        openpyxl google-api-python-client google-auth-oauthlib
"""

import argparse
import csv
import io
import json
import os
import re
import sys

TOKEN = os.environ.get("GOOGLE_TOKEN", os.path.expanduser("~/.hermes/google_token.json"))
XLSX = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
SHEET = "application/vnd.google-apps.spreadsheet"


def _creds():
    from google.oauth2.credentials import Credentials
    return Credentials.from_authorized_user_file(TOKEN)


def _drive():
    from googleapiclient.discovery import build
    return build("drive", "v3", credentials=_creds(), cache_discovery=False)


def _sheets():
    from googleapiclient.discovery import build
    return build("sheets", "v4", credentials=_creds(), cache_discovery=False)


def sheets_enablement_url(err):
    m = re.search(r"project(?:s/)?\s*[:=]?\s*(\d{6,})", str(err))
    if not m:
        m = re.search(r"containerInfo['\"]?\s*:\s*['\"]?(\d{6,})", str(err))
    proj = m.group(1) if m else "<PROJECT_ID>"
    return f"https://console.developers.google.com/apis/api/sheets.googleapis.com/overview?project={proj}"


def api_available(sheet_id):
    """True when the Sheets API is enabled and we can write cells safely."""
    try:
        _sheets().spreadsheets().get(spreadsheetId=sheet_id, fields="properties").execute()
        return True, None
    except Exception as e:  # noqa: BLE001 - any failure means: do not use the API path
        return False, e


def export_workbook(drive, sheet_id):
    raw = drive.files().export(fileId=sheet_id, mimeType=XLSX).execute()
    from openpyxl import load_workbook
    return load_workbook(io.BytesIO(raw)), raw


def structure(wb):
    ws = wb.active
    return {
        "tab": ws.title,
        "dims": ws.dimensions,
        "tables": sorted(ws.tables.keys()) if hasattr(ws, "tables") else [],
        "data_validations": [str(dv.sqref) for dv in ws.data_validations.dataValidation],
        "conditional_formats": len(list(ws.conditional_formatting)),
        "header": [c.value for c in ws[1]],
    }


def report(label, wb):
    s = structure(wb)
    print(f"{label}: tab={s['tab']!r} dims={s['dims']} "
          f"tables={s['tables']} validations={s['data_validations']} "
          f"cond_formats={s['conditional_formats']}")
    return s


def col_of(ws):
    """Header name -> column index, first row."""
    out = {}
    for c in ws[1]:
        if c.value is not None and str(c.value).strip():
            out[str(c.value).strip()] = c.column
    return out


def do_set(wb, tab, cells):
    ws = wb[tab] if tab in wb.sheetnames else wb.active
    n = 0
    for addr, val in cells.items():
        if ws[addr].value != val:
            ws[addr].value = val
            n += 1
    return n


def do_sync(wb, csv_path):
    ws = wb.active
    cmap = col_of(ws)
    cid, cmuc, ctt = cmap.get("ID"), cmap.get("Mức"), cmap.get("Trạng thái")
    if not (cid and cmuc and ctt):
        sys.exit(f"CSV/sheet header mismatch. Sheet has {sorted(cmap)}; need ID + Mức + Trạng thái")

    with open(csv_path, encoding="utf-8") as f:
        rows = list(csv.DictReader(f))

    wanted = {r["ID"].strip(): (r.get("Mức", "").strip(), r.get("Trạng thái", "").strip())
              for r in rows if (r.get("ID") or "").strip()}

    n, missed = 0, set(wanted)
    for r in range(2, ws.max_row + 1):
        rid = str(ws.cell(r, cid).value or "").strip()
        if rid not in wanted:
            continue
        missed.discard(rid)
        muc, tt = wanted[rid]
        if muc and ws.cell(r, cmuc).value != muc:
            ws.cell(r, cmuc).value = muc
            n += 1
        if tt and ws.cell(r, ctt).value != tt:
            ws.cell(r, ctt).value = tt
            n += 1
    if missed:
        print(f"  ! IDs in CSV but not on the sheet: {sorted(missed)}", file=sys.stderr)
    return n


def counts(wb):
    ws = wb.active
    cmap = col_of(ws)
    from collections import Counter
    out = {}
    for name in ("Mức", "Trạng thái"):
        ci = cmap.get(name)
        if ci:
            vals = [ws.cell(r, ci).value for r in range(2, ws.max_row + 1)]
            out[name] = dict(Counter(v for v in vals if v))
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("mode", choices=["check", "set", "sync"])
    ap.add_argument("--sheet-id", required=True)
    ap.add_argument("--tab")
    ap.add_argument("--cell", action="append", default=[], help="ADDR=VALUE, repeatable")
    ap.add_argument("--csv")
    ap.add_argument("--apply", action="store_true", help="actually write (default: dry run)")
    ap.add_argument("--unsafe-file-replace", action="store_true",
                    help="allow export->edit->re-upload when the Sheets API is unavailable")
    a = ap.parse_args()

    drive = _drive()
    wb, _ = export_workbook(drive, a.sheet_id)
    before = report("BEFORE", wb)

    if a.mode == "check":
        print(json.dumps(counts(wb), ensure_ascii=False))
        return

    checks_ok, err = api_available(a.sheet_id)
    if not checks_ok:
        print(f"\n! Sheets API unavailable: {type(err).__name__}")
        print(f"  Enable it (one click): {sheets_enablement_url(err)}")
        if not a.unsafe_file_replace:
            sys.exit("\nRefusing to write. Re-run with --unsafe-file-replace to accept the risk "
                     "that conditional formatting / manual colours may be lost.\n"
                     "(--unsafe-file-replace is verified to keep tables and data validations only.)")
        print("  Proceeding with file-replace fallback (tables + validations verified to survive;\n"
              "  conditional formatting and manual colours are NOT verified).")

    if a.mode == "set":
        cells = {}
        for item in a.cell:
            if "=" not in item:
                sys.exit(f"--cell needs ADDR=VALUE, got {item!r}")
            k, v = item.split("=", 1)
            cells[k.strip()] = v
        if not cells:
            sys.exit("set mode needs at least one --cell")
        n = do_set(wb, a.tab or before["tab"], cells)
    else:
        if not a.csv:
            sys.exit("sync mode needs --csv")
        n = do_sync(wb, a.csv)

    print(f"\ncells to change: {n}")
    if not a.apply:
        print("DRY RUN - nothing written. Re-run with --apply.")
        return

    if checks_ok:
        ws = wb[a.tab] if a.tab and a.tab in wb.sheetnames else wb.active
        data = []
        for item in a.cell if a.mode == "set" else []:
            pass
        # API path: push only the touched cells
        if a.mode == "set":
            for addr, val in cells.items():
                rng = f"{ws.title}!{addr}"
                _sheets().spreadsheets().values().update(
                    spreadsheetId=a.sheet_id, range=rng,
                    valueInputOption="USER_ENTERED", body={"values": [[val]]}).execute()
        else:
            cmap = col_of(wb.active)
            with open(a.csv, encoding="utf-8") as f:
                rows = list(csv.DictReader(f))
            for r in rows:
                rid = (r.get("ID") or "").strip()
                if not rid:
                    continue
                for name, col_letter_name in (("Mức", "Mức"), ("Trạng thái", "Trạng thái")):
                    if name in cmap and r.get(name):
                        col = cmap[name]
                        from openpyxl.utils import get_column_letter
                        # locate the row by ID
                        for rr in range(2, wb.active.max_row + 1):
                            if str(wb.active.cell(rr, cmap["ID"]).value or "").strip() == rid:
                                rng = f"{wb.active.title}!{get_column_letter(col)}{rr}"
                                _sheets().spreadsheets().values().update(
                                    spreadsheetId=a.sheet_id, range=rng,
                                    valueInputOption="USER_ENTERED",
                                    body={"values": [[r[name]]]}).execute()
                                break
    else:
        from googleapiclient.http import MediaFileUpload
        buf = io.BytesIO()
        wb.save(buf)
        buf.seek(0)
        drive.files().update(fileId=a.sheet_id, media_body=MediaFileUpload(
            buf, mimetype=XLSX, resumable=False), body={"mimeType": SHEET}, fields="id").execute()

    # Re-read and prove the owner's objects survived.
    wb2, _ = export_workbook(drive, a.sheet_id)
    after = report("AFTER", wb2)
    print(json.dumps(counts(wb2), ensure_ascii=False))
    lost = []
    for k in ("tables", "data_validations"):
        if before[k] != after[k]:
            lost.append(f"{k}: {before[k]} -> {after[k]}")
    if before["conditional_formats"] and not after["conditional_formats"]:
        lost.append("conditional_formats: all gone")
    print("PRESERVATION: OK" if not lost else "PRESERVATION: DAMAGE -> " + "; ".join(lost))


if __name__ == "__main__":
    main()
