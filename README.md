# Quality3Ds Daily 3D Printing News

## Purpose
This project runs a daily task that produces a Facebook-ready roundup of the latest 3D printing news, with extra focus on major product announcements from Bambu Lab (e.g., H2D/H2C), Creality, Sovol, and Elegoo.

## Daily Output Requirements
- Provide 4 to 8 stories.
- Try to include at least 1 story each from: Medical, Rockets/Aerospace, Construction (houses/bridges).
  - If a category has no credible updates today, skip it and add a different high-value story, but explicitly avoid filler.
- Each item must link to a working, verified source URL from reputable outlets or primary sources.
- For each story: start with an eye-catching emoji headline; then 1 sentence hook; then 1 sentence with a concrete detail (spec, milestone, funding amount, project scale, location, date).
- Finish each item with: "Read more ? <source link>".
- Separate stories with one blank line.
- Avoid repeating the same stories across days.
- For ghost guns: only cover high-level news/regulatory developments; do not include any how-to or technical build details.

## Daily Topic Focus
1) Medical applications (implants, surgical models, bioprinting, devices)
2) Aerospace/Rockets (engines, propulsion, launch hardware)
3) Construction (3D-printed houses/bridges/infrastructure)
4) FDM printers
5) 3D scanners
6) Slicer/software breakthroughs

## Output Location
- Daily output is saved inside the project folder as a date-stamped folder containing a README.
- Path pattern: D:\Software\AI_Projects\Quality3Ds\YYYY-MM-DD\README.md

## Scheduler
- Use Windows Task Scheduler to run the daily job.
- Script entrypoint: D:\Software\AI_Projects\Quality3Ds\run_daily.ps1

## Publishing (Optional)
If configured, publish the daily roundup to:
- Facebook Page: https://www.facebook.com/Quality3Ds
- Website: GoDaddy Website Builder (editor link provided by user)

## Publishing Requirements (To Configure)
See D:\Software\AI_Projects\Quality3Ds\PUBLISHING_SETUP.md
