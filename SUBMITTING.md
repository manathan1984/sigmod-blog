# Submitting a new blog post

Posts on the ACM SIGMOD Blog are commissioned and edited by the blog editors
(see the [Editors page](https://manathan1984.github.io/sigmod-blog/editors/)).
This guide covers the whole path: from pitch to publication.

- **Authors** only need [step 1](#1-pitch-and-write-authors) — no GitHub knowledge required.
- **Editors** (or authors comfortable with GitHub) do [steps 2–6](#2-create-the-post-file) to publish.

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

Each post is one file in `_posts/`, named

```
_posts/YYYY-MM-DD-short-title.md
```

The date is the publication date and, together with `short-title`, forms the URL:
`_posts/2026-11-15-learned-indexes-revisited.md` is published at
`/2026/11/15/learned-indexes-revisited/`. Use lowercase letters, digits and hyphens.

Start the file from this template:

```markdown
---
title: "Learned Indexes, Revisited"
author: jane-doe
categories: [Databases, Machine Learning]
excerpt: "One or two sentences shown on the home page and in link previews."
image: /assets/posts/2026-11-15-learned-indexes-revisited/figure1.png
---

Opening paragraph…

## First section

Text with **bold**, *italics*, [links](https://sigmod.org) and `inline code`.

![Figure 1: What the figure shows.]({{ '/assets/posts/2026-11-15-learned-indexes-revisited/figure1.png' | relative_url }})

More text, with a footnote.[^1]

## References

[1] A. Author, B. Author. "Paper Title." SIGMOD 2026.

[^1]: The footnote text.
```

| Field | Required | Notes |
| --- | --- | --- |
| `title` | yes | In quotes. |
| `author` | yes | An author **key** from `_data/authors.yml` (step 3), not the display name. |
| `categories` | recommended | Existing names are listed in the *Categories* dropdown on the site. A new name needs a category page (step 4). |
| `excerpt` | recommended | Shown on the home page. Without it, the first paragraph is used. |
| `image` | optional | Thumbnail on the home page. Without it, the post is listed without a picture. |

The body is [Markdown](https://www.markdownguide.org/basic-syntax/) (GitHub-flavoured:
tables and footnotes work). Plain HTML is allowed too, which is handy for figures
with captions:

```html
<figure>
  <img src="{{ '/assets/posts/2026-11-15-learned-indexes-revisited/figure2.png' | relative_url }}" alt="Throughput vs. data size">
  <figcaption>Figure 2: Throughput as the data grows.</figcaption>
</figure>
```

Tip: to convert a Google Doc or Word file, *File → Download → Markdown* (Google
Docs) or [pandoc](https://pandoc.org/) (`pandoc post.docx -t gfm -o post.md`) gives
a good starting point; then tidy up headings, figures and references by hand.

---

## 3. Add the author

Authors are listed in `_data/authors.yml`, keyed by a short lowercase id. If the
author has written for the blog before, reuse their key (search the file for
their name). Otherwise add an entry at the end:

```yaml
"jane-doe":
  name: "Jane Doe"
  url: "https://janedoe.example.org"
  avatar: "/assets/authors/jane-doe.jpg"
```

- Put the headshot at `assets/authors/jane-doe.jpg` (about 300×300 px is plenty).
  `avatar` and `url` are optional.
- Create the author's page, `author/jane-doe.html`, with exactly:

  ```yaml
  ---
  layout: author
  title: "Jane Doe"
  author: "jane-doe"
  permalink: /author/jane-doe/
  ---
  ```

For posts with several authors, use one entry whose `name` lists everyone
(e.g. `name: "Jane Doe and John Roe"`), as the imported posts do.

The author bio goes at the end of the post body itself, e.g.

```markdown
*Author bio: Jane Doe is a professor at … Her research focuses on …*
```

---

## 4. New category? Add its page

If every category in the post already exists, skip this step. For a new one,
create `category/<slug>.html`, where `<slug>` is the name in lowercase with
hyphens instead of spaces:

```yaml
---
layout: category
title: "Machine Learning"
category: "Machine Learning"
permalink: /category/machine-learning/
---
```

The `category:` value must match the name used in posts exactly (including capitals).

---

## 5. Add images

Put the post's images in a folder named after the post file:

```
assets/posts/2026-11-15-learned-indexes-revisited/figure1.png
assets/posts/2026-11-15-learned-indexes-revisited/figure2.png
```

Always reference them with the `relative_url` filter, as in the template above,
so they work both on the GitHub Pages address and on a custom domain. Keep each
image under ~1 MB (resize to ~1600 px wide; prefer PNG for plots, JPG for photos).

---

## 6. Preview, review and publish

**Preview locally** (optional, needs Ruby — see [README](README.md#local-preview)):

```bash
bundle exec jekyll serve      # then open http://localhost:4000/sigmod-blog/
```

**Review on GitHub** — no local setup needed:

1. Create a branch, e.g. `post/learned-indexes-revisited`, and add the files there
   (on github.com: *Add file → Upload files*, then choose *Create a new branch*).
2. Open a pull request. Ask the author and the other editor to review it.
3. Check the post against the list below.
4. **Merge the pull request.** The site rebuilds and the post is live within a
   couple of minutes (watch the *Actions* tab; a red ✗ means the build failed —
   usually a typo in the front matter).

### Checklist before merging

- [ ] File name is `_posts/YYYY-MM-DD-short-title.md` with the publication date.
- [ ] `author` key exists in `_data/authors.yml` and `author/<key>.html` exists.
- [ ] Every category exists (dropdown on the site) or has a new `category/<slug>.html`.
- [ ] All images load, use `relative_url`, and are under ~1 MB.
- [ ] Links work; references are complete.
- [ ] Author bio is at the end of the post.
- [ ] The author has approved the final version.

### Scheduling and corrections

- A post dated in the future is **not** published until the site is rebuilt on or
  after that date — merge on the day, or re-run the *Deploy to GitHub Pages*
  workflow from the *Actions* tab on the day.
- To fix a typo after publication, edit the file and merge again; the URL stays the same.
- Do not rename a published post file: that changes its URL and breaks existing links.
