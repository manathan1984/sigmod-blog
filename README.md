# ACM SIGMOD Blog

Source of the [ACM SIGMOD Blog](https://blog.sigmod.org/), a
Jekyll site with a layout modelled on the [SIGPLAN blog](https://blog.sigplan.org/).
Pushes to `main` are built and deployed to GitHub Pages by
`.github/workflows/pages.yml`.

**Writing or publishing a new post?** See [SUBMITTING.md](SUBMITTING.md).

## Major TODOs

- [ ] **Page view counters.** Show a view count on each post (e.g. with
  [GoatCounter](https://www.goatcounter.com/), which is free for non-commercial
  sites and needs no cookies). Possibly start from the old blog's counts: wp.sigmod.org
  uses the *Post Views Counter* plugin, which publishes each post's total at
  `https://wp.sigmod.org/index.php?rest_route=/post-views-counter/get-post-views/<wp_id>`.
  Save them (e.g. as `_data/legacy_views.yml`, keyed by `wp_id`) **before the
  WordPress site goes offline**, and show old + new.
- [ ] **Discussion on new posts.** Add a comment option, e.g.
  [Giscus](https://giscus.app/) (backed by GitHub Discussions on this repository;
  commenters sign in with GitHub, editors moderate there). Comments from the old
  blog are already archived read-only under each post (see below).

## Archived comments

The comment threads of the old WordPress blog (158 comments on 23 posts) are kept
in `_data/comments/<wp_id>.json` and shown, read-only, at the end of each post
by `_includes/archived-comments.html`. They were imported with
`tools/wp_import.py --comments` from [sigmod-org/wp.sigmod.org](https://github.com/sigmod-org/wp.sigmod.org).

## URLs

Posts live at `/YYYY/MM/DD/slug/`. Images of posts imported from the old
WordPress blog are kept at their original `wp-content/uploads/...` paths.

## The old WordPress blog

Everything about the old blog (wp.sigmod.org) lives in
[sigmod-org/wp.sigmod.org](https://github.com/sigmod-org/wp.sigmod.org): the
importer and import audit, and the "blog has moved" site that redirects old
links (`/?p=3855`, `/?cat=16`, ...) to their pages here. It reads the `wp_id`
fields kept in imported posts and pages, `_data/authors.yml` and
`_data/categories.yml`, so leave those in place.

## Local preview

```bash
bundle install
bundle exec jekyll serve      # http://localhost:4000/
```
