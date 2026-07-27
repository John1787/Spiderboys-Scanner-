# Spiderboys Trading Pro v11.1 — Scanner Hotfix

## Fixed

Version 11 used pandas `background_gradient()` for Spider Score colors. That feature imports Matplotlib internally, but Matplotlib was not part of the deployment package. Streamlit therefore raised an ImportError while rendering the scanner.

Version 11.1:

- Replaces the gradient with dependency-free score color bands
- Preserves green/yellow/orange/red scanner coloring
- Adds a plain-table fallback so styling cannot blank the app
- Protects both the Command Center scanner and full Live Scanner page

Upload the contents directly to the GitHub repository root. Main file: `app.py`.
