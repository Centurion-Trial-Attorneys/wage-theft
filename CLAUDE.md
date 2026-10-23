# Notes for Claude working on wagetheft.law

This site is a top-of-funnel intake site for California wage and hour clients of Centurion Trial Attorneys, APC (Attorney Ryan Stygar), including class action and PAGA cases. Its one job is to get California workers who were shorted on pay to click through to the intake link in `src/site.json` (Lawbrokr).

## Rules

- Never publish without Ryan's approval. New drafts go to Ryan's Command Center (https://claude.ai/artifact/Sf2QQGWZXyWDQkdeVF3RX7) as `pending` items with site `wagetheft-law`. When he approves one there, the Command Center publisher task writes it to `src/articles/`, builds, and pushes to main.
- This is attorney advertising under the California Rules of Professional Conduct (rules 7.1-7.5). No guarantees, no unverifiable superlatives ("best," "top-rated"), no case results without the "prior results" disclaimer, no fee claims beyond what `src/faq.json` already says.
- Verify every statute, regulation, and case citation against a primary source before using it. If leginfo is blocked, follow the Style Guide backup rule: compare Justia and FindLaw, quote only when they match, and flag anything amended this year. If it can't be verified, leave it out. Ryan checks every cite.
- Fees (only state them the way `src/faq.json` does, approved by Ryan Oct 22, 2026): case evaluations are free; if we take the case, our fee comes out of what we recover from the employer, including costs; if there's no recovery, the client pays nothing; fees and costs are explained in a written agreement before we start. Buttons say "Free case review."
- Case results live in `src/site.json` (`results`) and only Ryan adds or changes them. Every page that shows results must carry the prior-results disclaimer, and class action amounts must say they're totals for all workers in the case.
- California workers only. Federal law is fine to explain where it applies in California.
- Keep the site accessible (the Accessibility statement promises WCAG 2.1 AA): alt text on every image, real headings in order, text contrast of at least 4.5:1, nothing that only works with a mouse. Don't remove the accessibility options panel.
- General information, not advice. Every article already ends with a disclaimer and an intake callout added by `build.py`; don't add another.
- The look is comic in the frame (Bangers headings, halftone dots, thick borders, the Attorney Ryan illustration) and plain in the body. Article text stays in Work Sans; never set body copy in Bangers.

## Voice

Direct second person, plain English, short punchy sentences without stacking one-line fragments. Pro-worker, a little fired up, never sloppy. No profanity on this site. Avoid "very" as an intensifier, repeated "own," overused em dashes (commas or parentheses instead), "here's the kicker," manufactured suspense, "not X, it's Y" constructions, and stock AI vocabulary.

## Article format (built for search engines and AI answer engines)

- File: `src/articles/<slug>.md`, front matter `title`, `description` (under 160 characters), `date`, optional `updated`, `status`.
- The six launch guides in `src/topics.md` have fixed slugs: the homepage cards link to `/articles/<slug>/` once a guide with that slug is published. Use those slugs exactly.
- Title: the plain question or phrase a worker would search ("Do I get overtime after 8 hours in California?").
- Open with the `<div class="tldr" markdown="1">` short-version block that answers the question in 2-3 sentences.
- Question-style `##` headings, specific numbers and deadlines, citations in parentheses.
- Where it fits, say whether the problem tends to affect coworkers too and link to `/class-actions/`.
- Link to at least one existing guide and end with a short practical takeaway.
- 700-1,200 words. Check `src/articles/` first so topics don't overlap.
- Pick topics from `src/topics.md` (first unchecked one) and check it off in the same pull request.

## Publishing steps

1. Weekly task: write the article, confirm `python3 build.py` builds, and create the `pending` item in the Command Center. Don't commit.
2. Publisher task (runs when Ryan clicks Approve, plus a daily backup): write the approved item to `src/articles/<slug>.md` exactly as Ryan left it, check off its topic in `src/topics.md`, build, commit `src/` and `public/`, and push to main.
