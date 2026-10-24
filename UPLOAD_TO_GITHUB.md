# Upload this site to GitHub Pages

This folder is the repository root. It includes the site files, `archive.json`, `.nojekyll`, and the GitHub Pages workflow at `.github/workflows/pages.yml`.

## Browser upload

1. Create a new **public** GitHub repository named `ethiopian-bible-library` (or choose another name). A public repository works with GitHub Pages on GitHub Free.
2. Extract `EthiopianBibleLibrary_GitHub_Upload.zip` on your computer.
3. In the empty repository choose **Add file → Upload files**. Upload the extracted folder's contents, including the hidden `.github` directory and its workflow file.
4. Commit the upload to the `main` branch.
5. Open **Settings → Pages** and set the publishing source to **GitHub Actions**.
6. Open the **Actions** tab and wait for “Deploy site to GitHub Pages” to finish. The workflow provides the published URL.

Do not upload the ZIP itself as the only repository file: GitHub Pages needs the extracted `index.html`, `archive.json`, assets, and workflow at the repository root.

## Git command line

If GitHub CLI is authenticated, extract the ZIP, open a terminal in the extracted folder, create an empty GitHub repository, then push this folder to its `main` branch. If needed, authenticate first with `gh auth login -h github.com`.

## Current content boundary

The site is a preliminary catalogue and source register, not a complete scripture text library. The related-text section identifies comparative sources separately. No scan from the provided Baal Cycle page is included; its translation reuse rights remain unresolved.
