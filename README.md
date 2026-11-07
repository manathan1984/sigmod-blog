# ACM SIGMOD Blog

Source of the [ACM SIGMOD Blog](https://blog.sigmod.org/), a
Jekyll site with a layout modelled on the [SIGPLAN blog](https://blog.sigplan.org/).
Pushes to `main` are built and deployed to GitHub Pages by
`.github/workflows/pages.yml`.

**Writing or publishing a new post?** See [SUBMITTING.md](SUBMITTING.md).

## Major TODOs

- [ ] **Discussion on new posts.** Add a comment option, e.g.
  [Giscus](https://giscus.app/) (backed by GitHub Discussions on this repository;
  commenters sign in with GitHub, editors moderate there). Comments from the old
  blog are already archived read-only under each post (see below).

## View counts

Page views are counted by [GoatCounter](https://sigmod-blog.goatcounter.com)
(code `goatcounter: sigmod-blog` in `_config.yml`). It sets no cookies, and the
script is only added when `JEKYLL_ENV=production`, so local previews are not counted.

Each post's byline shows "N reads": the post's views on the old WordPress blog,
frozen in `_data/legacy_views.yml` (keyed by `wp_id`), plus its new views, which
`assets/js/reads.js` reads from GoatCounter's public counter
(`https://sigmod-blog.goatcounter.com/counter/<path>.json`; this needs
*Allow adding visitor counts on your website* switched on in GoatCounter's settings).
Without JavaScript, only the old count shows; new posts show nothing until their first view.

The old counts were read with `tools/wp_import.py --views` from
[sigmod-org/wp.sigmod.org](https://github.com/sigmod-org/wp.sigmod.org). **Run it once
more just before the old WordPress site (wp-old.sigmod.org) goes offline.**

## Authors

Each person has one entry in `_data/authors.yml` and a page at `/author/<key>/`.
A post names its author with `author: <key>`, or several with
`authors: [<key>, <key>]`. `_plugins/authors.rb` works out each post's list of
people (`author_keys`), makes the author pages that have no file in `author/`,
and builds the list used by the Authors page and the sidebar.

Posts imported from the old blog keep their old combined bylines (e.g.
`author: azzaandpaolo`); that entry's `members` lists the people behind it, so the
post is shown under each of them. The combined pages (`/author/azzaandpaolo/`)
stay, because old `?author=` links redirect there; they link to each person.
Headshots split from the old group photos are in `assets/authors/`.

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
