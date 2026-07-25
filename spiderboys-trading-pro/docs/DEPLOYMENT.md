# Streamlit Deployment

1. Keep the GitHub repository's default branch as `main`.
2. In Streamlit Community Cloud, connect the repository.
3. Set the entry point to `app.py`.
4. Add private values under **App settings → Secrets**.
5. Every merge to `main` becomes the next deployed version.

Do not upload replacement ZIP files after the repository is established. Edit files in GitHub, use branches, or sync the repository locally with Git.

## Journal persistence warning

Files written by an app host can be temporary and may be replaced during redeployment. Demo CSV storage is suitable for training. Before live use, move the journal to a persistent database and add user authentication and backups.
