# wagetheft.law

Client-intake website for California wage and hour cases (unpaid overtime, meal and rest breaks, off-the-clock work, final pay, misclassification, class actions and PAGA), operated by Centurion Trial Attorneys, APC.

## How it works

- Source content lives in `src/`. The finished site lives in `public/`.
- `python3 build.py` turns `src/` into `public/` (needs `pip install markdown`).
- Netlify publishes `public/` automatically whenever `main` changes (see `netlify.toml`).

## Common edits

| To change | Edit |
| --- | --- |
| Intake link, phone, offices, homepage claim cards, Google Analytics ID | `src/site.json` |
| FAQ questions | `src/faq.json` |
| Homepage and other pages | `src/pages/*.html` |
| Articles | `src/articles/*.md` (`status: published` or `status: draft`) |
| Colors and layout | `src/static/style.css` |

After any edit, run `python3 build.py` and commit both `src/` and `public/`.

Fonts: Bangers and Work Sans, self-hosted under the SIL Open Font License 1.1 (see `LICENSE-fonts.txt`). The Attorney Ryan illustration belongs to Ryan Stygar.
