# Start MathMate AI from this ZIP (Windows)

1. Extract the ZIP into a NEW folder. Keep your existing project and database as a backup.
2. Install Node.js 22.13 or newer and Python 3.13/3.14 if needed. Initial dependency installation needs internet access.
3. Open PowerShell inside the extracted mathmate-ai folder and run:

   powershell -ExecutionPolicy Bypass -File scripts/setup-local.ps1

4. In the first terminal:

   cd backend
   .venv/Scripts/python -m uvicorn app.main:app --host 127.0.0.1 --port 8000

5. In a SECOND terminal, from the extracted project folder:

   cd frontend
   npm.cmd run dev

6. Open http://localhost:3000 and register a new account. No preset username/password is included.
7. Learning studio: submit 2x + 6 = 14, then Play. Use Pause, Stop, Replay, Previous and Next below the board.

This is a source-code ZIP, not a standalone installer. The setup installs dependencies and creates a fresh local SQLite database. Docker is NOT required. Secrets, existing accounts/database, dependencies and generated caches are intentionally excluded. The Mia model and its license files are included.

Meta inference is not activated by this ZIP. The default setup uses labelled development-mode responses. OCR quality depends on input and recognizer configuration. Mia's motions are procedural pointing, not motion-captured handwriting or precise phoneme lip synchronization.

See README.md for more details and docs/classroom-gesture-controls.md for the latest classroom changes.

Latest classroom update: all verified solution steps appear immediately after Solve; Play explains and highlights them in order. The full working stays visible during Replay and Previous. Long solutions can be scrolled. See docs/cumulative-whiteboard.md.
