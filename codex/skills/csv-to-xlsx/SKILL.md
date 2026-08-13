---
name: csv-to-xlsx
description: Convert CSV files into polished, compatibility-first Excel `.xlsx` workbooks with encoding and delimiter detection, typed values, readable formatting, filters, frozen headers, and verification. Use when the user asks to turn a CSV into Excel, make CSV data easier to review, format a CSV as a workbook, or fix an XLSX that Excel opens with an unreadable-content or repair warning.
---

# CSV To XLSX

Convert one local CSV file with the bundled script. Keep the workflow deterministic and preserve the source CSV.

## Workflow

1. Resolve the input path and confirm it is one `.csv` file.
2. Confirm the selected `python3` can import `openpyxl`. If not, stop and report:
   `python3 -m pip install openpyxl`.
3. Run `scripts/csv_to_xlsx.py` with the input path and any requested output, title, sheet name, encoding, or delimiter.
4. Read the script summary and confirm its row and column counts match the source.
5. Render the output with Quick Look when `qlmanage` is available and inspect the image for clipped headers, unreadable values, or broken layout.
6. When Microsoft Excel is installed on macOS, open the generated file once and confirm Excel does not show a repair warning and the target window title does not contain `Repaired`. Do not close unrelated workbooks.
7. Report the exact output path.

## Execution

Default conversion:

```bash
python3 scripts/csv_to_xlsx.py "/path/to/input.csv"
```

Explicit output and title:

```bash
python3 scripts/csv_to_xlsx.py \
  "/path/to/input.csv" \
  --output "/path/to/output.xlsx" \
  --title "Review Title" \
  --sheet-name "Data"
```

Use `--encoding` or `--delimiter` only when automatic detection is wrong. Pass `--delimiter '\t'` for tabs. Use `--overwrite` only when replacing the exact output is clearly intended.

## Output Behavior

- Save next to the CSV with the same basename by default.
- Add a timestamp suffix instead of overwriting an existing workbook unless `--overwrite` is supplied.
- Detect UTF-8, UTF-8 with BOM, CP949, EUC-KR, and UTF-16.
- Detect comma, tab, semicolon, and pipe delimiters.
- Preserve identifiers with leading zeroes as text.
- Store numbers, percentages, dates, datetimes, and booleans as typed Excel values.
- Add a title, source summary, hidden gridlines, alternating row shading, one worksheet filter, frozen headers, semantic number formats, capped column widths, and print settings.

## Compatibility Rules

- Use ordinary cell styles and exactly one worksheet-level auto-filter.
- Do not add Excel Tables or conditional-formatting XML in the default conversion. Some Excel versions may repair workbooks containing overlapping or unsupported advanced elements even when other readers accept them.
- Treat any Excel unreadable-content or repair dialog as a failed conversion. Regenerate with the compatibility-first defaults and verify again.
- Never modify or delete the source CSV.

## Verification

The script reopens the workbook with `openpyxl`, compares every converted cell to the generated data, and tests the XLSX ZIP container. This structural verification is required but does not replace the visual pass or actual Excel-open check when Excel is available.
