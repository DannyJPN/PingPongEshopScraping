"""
Generuje importní soubor pro opravu kódů variant v PincesObchodu.
Formát sleduje Report-All.xlsx (vstupní importní formát PincesObchodu).

Identifikace varianty při importu:
  product_id         = id rodiče z JSON (PincesObchod internal ID)
  varianta_produkt   = catalogNumber rodiče
  varianta1/2/3_nazev/hodnota = options[position=1/2/3] z JSON

Sloupec "kod" obsahuje NOVÝ správný kód (ten se přepíše).
"""
import csv
import os
import re
import subprocess
import sys
import io
import tempfile
from datetime import datetime

from compare_utils import load_latest_json, get_name, is_active

DEFAULT_CS_DIR  = "F:/Dropbox/DesakaPrivate/PingPongEshopScraping/Desaka/Pincesobchod_CS"
DEFAULT_OUT_DIR = "F:/Dropbox/DesakaPrivate/PingPongEshopScraping/Desaka/Reports/Pincesobchod"

COLUMNS = [
    "typ",
    "nazev",
    "varianta_produkt",
    "varianta_stejne",
    "varianta1_nazev",
    "varianta1_hodnota",
    "varianta2_nazev",
    "varianta2_hodnota",
    "varianta3_nazev",
    "varianta3_hodnota",
    "product_id",
    "varianta_id",
    "kod",
]


def extract_suffix_num(old_code):
    """Extrahuje číslo sufixu z kódu varianty, např. 'JOO05070016-12' → 12."""
    m = re.search(r'[-_](\d+)$', old_code)
    return int(m.group(1)) if m else None


def get_options(variant):
    """Vrátí options varianty seřazené podle position."""
    opts = variant.get('options') or []
    return sorted(opts, key=lambda o: o.get('position', 999))


def build_mismatch_rows(cs_products):
    """Vrátí list dict se všemi neshodami kódů variant."""
    rows = []

    for p in cs_products:
        parent_code   = p.get('catalogNumber') or ''
        parent_id     = p.get('id')
        parent_name   = get_name(p)
        parent_active = is_active(p)
        variants      = p.get('variants') or []

        # Sufixová čísla již platně použitá pod tímto rodičem
        used_suffixes = set()
        for v in variants:
            vc = v.get('catalogNumber') or ''
            if vc.startswith(parent_code + '-'):
                m = re.search(r'-(\d+)$', vc)
                if m:
                    used_suffixes.add(int(m.group(1)))

        mismatched = [
            v for v in variants
            if not (v.get('catalogNumber') or '').startswith(parent_code)
            or not v.get('catalogNumber')
        ]

        next_seq = 1
        for v in mismatched:
            old_code   = v.get('catalogNumber') or ''
            suffix_num = extract_suffix_num(old_code) if old_code else None

            if suffix_num is not None:
                new_seq = suffix_num
            else:
                while next_seq in used_suffixes:
                    next_seq += 1
                new_seq = next_seq
                used_suffixes.add(new_seq)
                next_seq += 1

            opts = get_options(v)
            row = {
                'typ':              'varianta',
                'nazev':            parent_name,
                'varianta_produkt': parent_code,
                'varianta_stejne':  '1',
                'varianta1_nazev':  opts[0]['name']  if len(opts) > 0 else '',
                'varianta1_hodnota': opts[0]['value'] if len(opts) > 0 else '',
                'varianta2_nazev':  opts[1]['name']  if len(opts) > 1 else '',
                'varianta2_hodnota': opts[1]['value'] if len(opts) > 1 else '',
                'varianta3_nazev':  opts[2]['name']  if len(opts) > 2 else '',
                'varianta3_hodnota': opts[2]['value'] if len(opts) > 2 else '',
                'product_id':       parent_id,
                'varianta_id':      v.get('id'),
                'kod':              f"{parent_code}-{new_seq:02d}",
                '_stary_kod':       old_code or '(prázdný)',
                '_aktivni':         parent_active,
            }
            rows.append(row)

    rows.sort(key=lambda r: (not r['_aktivni'], r['varianta_produkt'], r['_stary_kod']))
    return rows


def write_csv(rows, path):
    with open(path, 'w', newline='', encoding='utf-8-sig') as f:
        writer = csv.DictWriter(
            f, fieldnames=COLUMNS, delimiter=';', extrasaction='ignore')
        writer.writeheader()
        writer.writerows(rows)


def csv_to_xlsx(csv_path, xlsx_path):
    """Konvertuje CSV na XLSX přes Excel COM (stejný mechanismus jako Unifier.ps1 CsvToXlsx)."""
    col_count = len(COLUMNS)
    last_col_letter = chr(ord('A') + col_count - 1)
    ps_script = rf"""
param($csv, $xlsx)
Add-Type -AssemblyName System.Drawing
$excel = New-Object -ComObject excel.application
$excel.Visible = $false
$excel.DisplayAlerts = $false
$workbook = $excel.Workbooks.Add(1)
$worksheet = $workbook.Worksheets.Item(1)
$worksheet.Name = 'Opravy kodů variant'

$TxtConnector = 'TEXT;' + $csv
$Connector = $worksheet.QueryTables.add($TxtConnector, $worksheet.Range('A1'))
$query = $worksheet.QueryTables.item($Connector.name)
$query.TextFileOtherDelimiter = ';'
$query.TextFileParseType = 1
$query.TextFilePlatform = 65001
$query.TextFileColumnDataTypes = ,2 * $worksheet.Cells.Columns.Count
$query.AdjustColumnWidth = 1
$query.Refresh()
$query.Delete()

$headerRange = $worksheet.Range('A1:{last_col_letter}1')
$headerRange.Font.Bold = $true
$headerRange.Font.ColorIndex = 2
$headerRange.Interior.Color = [System.Drawing.ColorTranslator]::ToOle([System.Drawing.Color]::FromArgb(46, 80, 144))
$worksheet.Rows.Item(1).RowHeight = 22

$excel.ActiveWindow.SplitRow = 1
$excel.ActiveWindow.FreezePanes = $true

$workbook.SaveAs($xlsx, 51)
$workbook.Close($false)
$excel.Quit()
[System.Runtime.Interopservices.Marshal]::ReleaseComObject($excel) | Out-Null
"""
    tmp = tempfile.NamedTemporaryFile(suffix='.ps1', delete=False,
                                     mode='w', encoding='utf-8')
    tmp.write(ps_script)
    tmp.close()

    try:
        ps_exe = r'C:\Windows\System32\WindowsPowerShell\v1.0\powershell.exe'
        result = subprocess.run(
            [ps_exe, '-NoProfile', '-File', tmp.name,
             csv_path.replace('/', '\\'), xlsx_path.replace('/', '\\')],
            capture_output=True, text=True, timeout=60
        )
        if result.returncode != 0:
            raise RuntimeError(result.stderr.strip())
    finally:
        os.unlink(tmp.name)


def main():
    import argparse
    p = argparse.ArgumentParser(description="Generátor importního souboru pro opravu kódů variant")
    p.add_argument('--cs-dir',     default=DEFAULT_CS_DIR)
    p.add_argument('--output-dir', default=DEFAULT_OUT_DIR)
    args = p.parse_args()

    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

    cs_products, _, cs_path = load_latest_json(args.cs_dir, "CS")
    print(f"CS: {cs_path}  ({len(cs_products)} produktů)")

    rows = build_mismatch_rows(cs_products)
    active_cnt   = sum(1 for r in rows if r['_aktivni'])
    inactive_cnt = len(rows) - active_cnt
    print(f"Oprav variant: {len(rows)}  (aktivních rodičů: {active_cnt}, neaktivních: {inactive_cnt})")

    os.makedirs(args.output_dir, exist_ok=True)
    ts        = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
    csv_path  = os.path.join(args.output_dir, f"variant_code_corrections_{ts}.csv")
    xlsx_path = csv_path.replace('.csv', '.xlsx')

    write_csv(rows, csv_path)
    print(f"CSV uložen: {csv_path}")

    try:
        csv_to_xlsx(csv_path, xlsx_path)
        print(f"XLSX uložen: {xlsx_path}")
    except Exception as e:
        print(f"XLSX konverze se nezdařila ({e}); CSV je k dispozici.")

    # Přehled po rodičích
    from collections import Counter
    parents = Counter(r['varianta_produkt'] for r in rows)
    print("\nRodiče s neshodami:")
    for pc, cnt in sorted(parents.items()):
        pname  = next((r['nazev'] for r in rows if r['varianta_produkt'] == pc), '')
        active = any(r['_aktivni'] for r in rows if r['varianta_produkt'] == pc)
        flag   = "" if active else " [neaktivní]"
        print(f"  {pc:<22s}  {cnt:>2} variant  {pname[:45]}{flag}")


if __name__ == '__main__':
    main()