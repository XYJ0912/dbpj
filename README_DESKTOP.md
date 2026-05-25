# Portfolio Library Desktop Packaging

This desktop build wraps the existing React + Flask + MySQL app in Electron for Windows x64.

## What is included

- Electron desktop shell.
- Built React frontend from `frontend/dist`.
- PyInstaller Flask backend executable.
- Portable MySQL Community Server runtime.
- Database schema from `db/creator_workspace_minimal.sql`.

Runtime data is stored under Electron's user data directory, not in the source tree:

- `mysql-data/`
- `uploads/`
- `exports/`
- `logs/`

## Prepare MySQL runtime

Download MySQL Community Server for Windows x64 as a ZIP archive, then copy the extracted
server contents into:

```text
desktop/runtime/mysql/
```

These files must exist before packaging:

```text
desktop/runtime/mysql/bin/mysqld.exe
desktop/runtime/mysql/bin/mysql.exe
```

Keep the MySQL license files from the downloaded ZIP in that runtime directory before distribution.

## Install desktop build dependencies

```powershell
cd desktop
npm install
```

PyInstaller must also be available in the Python environment used for packaging:

```powershell
python -m pip install pyinstaller
```

## Build

```powershell
cd desktop
npm run dist
```

Expected outputs:

```text
dist-desktop/
  Portfolio-Library-Setup-0.1.0.exe
  Portfolio-Library-0.1.0-win-x64.zip
```

## Development run

Build the frontend first:

```powershell
npm --prefix frontend run build
```

Then run Electron from the desktop folder:

```powershell
cd desktop
npm start
```

In development mode, Electron uses:

- `frontend/dist` for the UI.
- `backend/app.py` if `backend/dist/portfolio-backend.exe` is not present.
- `desktop/runtime/mysql` for MySQL.

## Notes

- First launch initializes a private MySQL data directory and imports `creator_workspace_minimal.sql`.
- Browser development mode still works with Vite on `localhost:5173` and Flask on `localhost:5000`.
- Desktop mode injects the API base URL at runtime through `window.__APP_CONFIG__.apiBase`.
