# ReNexa complete app-folder UI replacement

This archive contains a replacement `app/` folder with the new ReNexa green/white design, sidebar, Light/Dark/System selector, login screen, opening animation and page shells matching the page names visible in your VS Code screenshot.

## Very important
This replaces the **app folder only**, not the entire project. It intentionally does not overwrite `ai/`, `services/`, `database/`, `data/`, `models/`, `training/`, `tests/`, `.streamlit/`, or `requirements.txt`.

Because I only had a screenshot of your project tree, not the contents of your existing page/service source files, this is a **UI scaffold**. The scan page accepts an image, but does not call the detector; results/recommendations/tutorial/history pages show honest empty states until connected to your existing services. This prevents fabricated model predictions or broken assumptions about unseen APIs.

## Replace safely
1. Close Streamlit.
2. Rename `E:\ReNexa\app` to `app_backup_20261011`.
3. Extract the archive.
4. Copy the included `app` folder into `E:\ReNexa`.
5. Confirm your `E:\ReNexa\app\main.py` and `app\pages` exist.
6. Run:
   `.\venv\Scripts\python.exe -m streamlit run app\main.py`

If startup fails, restore the backup folder. Do not delete the backup until the UI and services have been reconnected and tested.

## Login
Demo login accepts any non-empty username and password. This is for UI preview only and is not secure authentication. To require configured credentials, set environment variables `RENEXA_DEMO_LOGIN=0`, `RENEXA_LOGIN_USER`, and `RENEXA_LOGIN_PASSWORD`. Do not deploy plaintext-password authentication; use a proper authentication provider for production.

## Navigation note
Streamlit's built-in multipage navigation discovers scripts in `app/pages`. Sidebar entries in this scaffold are visual labels; Streamlit's native page navigation may also be shown depending on configuration. Connect them to `st.navigation` if you want a fully custom clickable sidebar.

## Theme note
System currently falls back to Light. Dark and Light are selectable. Opening animation is CSS fade/slide and does not block interaction.
