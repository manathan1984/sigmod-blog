# Submitting a new blog post

Posts on the ACM SIGMOD Blog are commissioned and edited by the blog editors
(see the [Editors page](https://manathan1984.github.io/sigmod-blog/editors/)).
This guide covers the whole path: from pitch to publication.

- **Authors** only need [step 1](#1-pitch-and-write-authors) — no GitHub knowledge required.
- **Editors** publish with [steps 2–6](#2-create-the-post-file), by hand or
  [with Claude or another AI agent](#using-claude-or-another-ai-agent).

---

## 1. Pitch and write (authors)

1. **Pitch first.** Email the editors a short pitch: two or three sentences on the
   idea and why it matters now.
2. **Write.** Posts usually run between 1,000 and 3,000 words; 2,000 is a good
   target. Write for the broad data management community, not only specialists.
3. **Send the editors:**
   - the text (Google Doc, Word, or Markdown are all fine);
   - figures as separate image files (PNG or JPG, at least 1200 px wide), with captions;
   - a short author bio (2–4 sentences) and a square-ish headshot;
   - your name as it should appear, your homepage URL, and 1–3 suggested categories.

The editors take it from there.

---

## 2. Create the post file

Create `_posts/YYYY-MM-DD-short-title.md` (publication date + lowercase,
hyphenated title). It is published at `/YYYY/MM/DD/short-title/`.

```markdown
---
title: "Learned Indexes, Revisited"
author: jane-doe                          # key from _data/authors.yml (step 3)
categories: [Databases, Machine Learning] # existing names, or add one (step 4)
excerpt: "One or two sentences for the home page."      # optional
image: /assets/posts/2026-11-15-learned-indexes-revisited/figure1.png  # optional thumbnail
---

Opening paragraph, in Markdown: **bold**, *italics*, [links](https://sigmod.org), tables, footnotes.[^1]

![Figure 1: Caption.]({{ '/assets/posts/2026-11-15-learned-indexes-revisited/figure1.png' | relative_url }})

*Author bio: Jane Doe is …*

[^1]: Footnote text.
```

HTML works too (e.g. `<figure>` with `<figcaption>`). To convert a Google Doc or
Word file: *File → Download → Markdown* in Google Docs, or
`pandoc post.docx -t gfm -o post.md`, then tidy up.

## 3. Add the author (if new)

Append to `_data/authors.yml` (put the headshot, ~300 px, in `assets/authors/`):

```yaml
"jane-doe":
  name: "Jane Doe"                         # for several authors: "Jane Doe and John Roe"
  url: "https://janedoe.example.org"       # optional
  avatar: "/assets/authors/jane-doe.jpg"   # optional
```

and create `author/jane-doe.html`:

```yaml
---
layout: author
title: "Jane Doe"
author: "jane-doe"
permalink: /author/jane-doe/
---
```

## 4. Add the category (if new)

Create `category/machine-learning.html`; `category:` must match the name used in posts exactly:

```yaml
---
layout: category
title: "Machine Learning"
category: "Machine Learning"
permalink: /category/machine-learning/
---
```

## 5. Add images

Put them in `assets/posts/<post-file-name>/`, keep each under ~1 MB (~1600 px wide),
and always link them with `relative_url` as in the template.

## 6. Review and publish

1. Add the files on a new branch and open a pull request (on github.com:
   *Add file → Upload files → Create a new branch*). Optionally preview locally
   with `bundle exec jekyll serve` (see [README](README.md#local-preview)).
2. Have the author and the other editor review it, using the checklist below.
3. **Merge.** The post is live within a few minutes (a red ✗ in the *Actions* tab
   means the build failed, usually a front-matter typo).

**Checklist:** file name and date are right · author key and `author/` page exist ·
categories exist · images load and are under 1 MB · links work · bio at the end ·
**the author approved the final version**.

**Good to know:** a post dated in the future only appears after a rebuild on or after
that date (merge on the day, or re-run the workflow from *Actions*). Fix typos by
editing and merging again. Never rename a published post's file: that changes its URL.

---

## Using Claude or another AI agent

Steps 2–6 are mechanical, so an AI coding agent such as
[Claude Code](https://www.anthropic.com/claude-code) (or Claude on claude.ai with the
files attached) can do them: convert the author's document, create the post,
author and category files, resize and place images, preview the site, and open
the pull request. Give it the author's files and point it at this guide, e.g.:

> Following SUBMITTING.md, publish the attached post by Jane Doe
> (draft.docx, figure1.png, figure2.png, headshot.jpg) with categories
> "Databases" and "Machine Learning", dated 2026-11-15. Convert it to Markdown
> without changing the wording, add the author and any new category, resize
> the images, preview the site, check the post renders correctly, and open a
> pull request — do not merge it.

Some advice from setting this blog up this way:

- **Formatting only, not editing.** Ask the agent explicitly not to change the
  author's wording, and check the pull request diff for unintended edits.
  Copy-editing, if any, is an editorial decision agreed with the author.
- **A human merges.** Let the agent open the pull request, but have an editor
  review it and merge. The checklist above applies unchanged, including the
  author's approval.
- **Ask it to check its own work.** Agents that can run a browser can preview the
  site and confirm that figures, tables, footnotes and links render; ask for that
  explicitly, and for a short list of anything it was unsure about.
- **Watch the details agents get wrong:** dates (publication date vs. today),
  reusing an existing author key instead of creating a duplicate, category names
  that almost match an existing one, and image paths missing `relative_url`.
- **Keep the author's content private until it is public.** Only use tools your
  institution allows for unpublished manuscripts, and do not paste drafts into
  services that may train on them without the author's consent.
- **Agents can also help authors** (step 1): converting a draft to Markdown or
  checking references, as long as the text remains their own.
