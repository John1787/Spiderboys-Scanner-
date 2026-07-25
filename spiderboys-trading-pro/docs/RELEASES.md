# Release Process

1. Create `release/x.y.z` from `main`.
2. Update `VERSION.json`, `pyproject.toml`, the sidebar version, and `CHANGELOG.md`.
3. Run project checks and manually test Streamlit.
4. Open a pull request and merge after CI passes.
5. Create a GitHub Release tag such as `v6.1.0`.
6. Verify the Streamlit deployment after the merge.

Patch releases fix defects. Minor releases add backwards-compatible features. Major releases may change storage, deployment, or trading workflows.
