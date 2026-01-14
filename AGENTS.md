# Repository Guidelines

## Project Structure & Module Organization
This repository is a small automation project focused on producing a daily news roundup.
- `README.md`: project requirements and publishing notes.
- `run_daily.ps1`: local entrypoint that creates the dated output folder and `README.md`.
- `PUBLISHING_SETUP.md`: setup checklist for Facebook and website publishing.
- `YYYY-MM-DD/README.md`: daily outputs (one folder per date).

## Build, Test, and Development Commands
There is no build system yet. Use the PowerShell entrypoint to generate the daily stub:
- `powershell.exe -ExecutionPolicy Bypass -File "D:\Software\AI_Projects\Quality3Ds\run_daily.ps1"`
This creates `D:\Software\AI_Projects\Quality3Ds\YYYY-MM-DD\README.md` if it does not exist.

## Coding Style & Naming Conventions
- Use PowerShell with 2-space indentation and double-quoted strings for paths.
- Name daily folders with the `YYYY-MM-DD` pattern.
- Keep documentation concise and update `README.md` if requirements change.

## Testing Guidelines
No automated tests are defined. If you add tests, document the framework and commands here and in `README.md`.

## Commit & Pull Request Guidelines
No Git history exists in this folder, so commit conventions are not yet established. If you initialize Git, prefer clear, imperative commit messages (e.g., "Add daily output script") and include a short PR description if using pull requests.

## Security & Configuration Tips
- Do not commit access tokens or secrets. Store them in a local `.env` or OS secret store.
- Verify all news links before publishing and avoid repeated stories across days.
