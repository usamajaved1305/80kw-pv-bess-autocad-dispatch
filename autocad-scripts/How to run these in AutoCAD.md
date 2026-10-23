# Running these in AutoCAD

There are three scripts, one per sheet (`PV-01`, `PV-03` and `PV-04`). Each one makes AutoCAD draw that sheet
itself, using AutoCAD's own LINE, TEXT and CIRCLE commands. Nothing is imported.

PV-01, PV-03 and PV-04 were drawn this way in AutoCAD 2027 on 8 October 2026.
The DWG files and the A1 PDFs plotted from them are in the `drawings` folder.

## Steps

1. Open AutoCAD and start a new drawing. Use the **acadiso** template so the
   units are millimetres.
2. Type **SCRIPT** and press Enter.
3. Pick the `.scr` file for the sheet you want.
4. AutoCAD draws it in a few seconds. PV-01 has the most objects, 778.
5. Type **ZOOM** then **E** if you need to see the whole sheet.
6. **SAVEAS** and choose DWG. From that point it is an ordinary AutoCAD drawing
   and you can edit, dimension and plot it like any other.

## What each script does first

- Sets OSMODE to 0, so object snap does not pull points off their coordinates
- Sets DTEXTED to 1, so each TEXT command places one line and ends
- Sets the drawing limits to the A1 sheet, 84100 by 59400 units
- Creates the twelve layers with their colours
- Then draws, switching layer as it goes, and at the end zooms to the whole
  sheet and sets DTEXTED back to 2, AutoCAD's default

## Why DTEXTED matters

With AutoCAD 2027's default (DTEXTED 2) the TEXT command stays open on screen
after each label, waiting for the next click, and a script stops after the first
label. With DTEXTED at 1 the command ends after one line, so the scripts give no
blank line after each label. An older version of these scripts did, and that
blank line restarted TEXT and stopped the script.

## Plotting

Everything is drawn full size in millimetres and the sheet border is scaled by
100. The PDFs were plotted with these settings:

- Printer: DWG To PDF.pc3
- Paper: ISO full bleed A1 (841 x 594 mm)
- What to plot: Limits, centred
- Scale: 1:100, so every dimension read off the drawing is true
- Plot style: monochrome.ctb, so the sheet prints black on white

## If a line of text looks wrong

A space at the start of a line acts as Enter inside an AutoCAD script, so the
indented note lines are indented by moving the start point rather than by typing
spaces. That is why the scripts have no lines beginning with a space.
