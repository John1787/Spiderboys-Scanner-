# One-Time GitHub Setup

## Easiest method

1. Create a new empty GitHub repository named `spiderboys-trading-pro`.
2. Do not add a README or `.gitignore` during repository creation.
3. Unpack the bootstrap package on your Mac.
4. Open Terminal in the unpacked folder.
5. Run:

```bash
git init
git add .
git commit -m "Initialize Spiderboys Trading Pro v6.1.0"
git branch -M main
git remote add origin YOUR_GITHUB_REPOSITORY_URL
git push -u origin main
```

6. Connect that repository to Streamlit Community Cloud with `app.py` as the entry point.

## Future updates

After setup, do not replace the repository with a new ZIP. Pull the latest `main`, create a feature branch, edit only the changed files, run tests, and merge through a pull request.
