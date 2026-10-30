# ACM SIGMOD Blog

Static (Jekyll) version of the [ACM SIGMOD Blog](https://wp.sigmod.org/), with a
layout modelled on the [SIGPLAN blog](https://blog.sigplan.org/). Pushes to
`main` are built and deployed to GitHub Pages by `.github/workflows/pages.yml`.

**Writing or publishing a new post?** See [SUBMITTING.md](SUBMITTING.md).

## Importing from the old WordPress site

`tools/wp_import.py` pulls posts and pages through the public WordPress REST API
(stdlib Python only, no credentials):

```bash
python3 tools/wp_import.py --latest 1        # newest post
python3 tools/wp_import.py --post 3855       # specific post IDs
python3 tools/wp_import.py --page 2 3873     # specific page IDs (About, Editors)
python3 tools/wp_import.py --all             # every published post
```

It is idempotent (files are keyed by WordPress ID) and:

- writes posts to `_posts/` as raw WordPress HTML, pages to `_pages/`;
- mirrors images to `wp-content/uploads/...` at their **original paths**;
- records authors in `_data/authors.yml` and all WordPress categories in
  `_data/categories.yml`, and creates `category/<slug>` and `author/<slug>` pages;
- rewrites links between imported posts to their new URLs (re-run `--all` at the
  end so every cross-link is resolved), and resolves `?attachment_id=` / `?cat=`
  links and Google Docs redirect links;
- keeps local copies of images pasted from Google Docs (`wp-content/uploads/external/`);
- cleans up old-WordPress markup: one-column layout tables, unclosed `<div>`s,
  `http://` embeds.

Files with `keep_local_edits: true` in their front matter (e.g. the About page) are
never overwritten by a re-import unless `--force` is given.

Comments are not migrated yet; each post links back to its original page.

### Checking an import

```bash
python3 tools/audit_posts.py   # writes IMPORT_REVIEW.md
```

flags posts whose content may not have survived the move (embeds, math, external
or missing images, broken layout, unresolved old links) and lists, separately,
the ones still needing a human decision. See [IMPORT_REVIEW.md](IMPORT_REVIEW.md).

## URLs

New posts live at `/YYYY/MM/DD/slug/` (same scheme as the SIGPLAN blog).

The old blog used WordPress "plain" permalinks, all on the site root, so they are
resolved client-side by `_includes/legacy-redirect.html` on the home and 404 pages:

| Old URL                     | Goes to                              |
| --------------------------- | ------------------------------------ |
| `/?p=3855`, `/?page_id=2`   | the imported post / page             |
| `/?cat=16`                  | `/category/databases/`               |
| `/?author_name=x`, `/?author=120` | `/author/x/`                   |
| `/?m=202609`                | `/archives/#2026-09`                 |
| `/?feed=rss2`               | `/feed.xml`                          |
| `/?s=query`                 | `/search/?q=query`                   |
| `/wp-content/uploads/...`   | same path (images are mirrored)      |

A post that has not been imported yet is sent to the same URL on wp.sigmod.org
(skipped once this site is itself served from wp.sigmod.org).

For old links to keep working verbatim, serve this site from the old domain:
set `url: "https://wp.sigmod.org"` and `baseurl: ""` in `_config.yml`, add a
`CNAME` file and point DNS at GitHub Pages — after `--all` has been run.

## Local preview

```bash
bundle install
bundle exec jekyll serve      # http://localhost:4000/sigmod-blog/
```
