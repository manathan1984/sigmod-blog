# ACM SIGMOD Blog

Source of the [ACM SIGMOD Blog](https://sigmod-org.github.io/blog.sigmod.org/), a
Jekyll site with a layout modelled on the [SIGPLAN blog](https://blog.sigplan.org/).
Pushes to `main` are built and deployed to GitHub Pages by
`.github/workflows/pages.yml`.

**Writing or publishing a new post?** See [SUBMITTING.md](SUBMITTING.md).

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
bundle exec jekyll serve      # http://localhost:4000/blog.sigmod.org/
```
