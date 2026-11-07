# Authors of co-written posts, each shown as a separate person.
#
# A post names its authors in one of three ways:
#   authors: [jane-doe, john-roe]   # new posts with several authors
#   author: jane-doe                # one author
#   author: azzaandpaolo            # combined byline imported from the old blog;
#                                   # its _data/authors.yml entry lists `members`
#
# This plugin sets `author_keys` on every post (the people, in byline order),
# creates /author/<key>/ for every person who has no hand-made page in author/,
# gives each author page its `author_posts`, and builds `site.data.author_index`
# (one row per person, for the Authors page and the sidebar).

module SigmodAuthors
  def self.keys_for(doc, authors)
    list = Array(doc.data["authors"]).map(&:to_s).reject(&:empty?)
    return list unless list.empty?

    key = doc.data["author"].to_s
    return [] if key.empty?

    members = (authors[key] || {})["members"]
    members && !members.empty? ? members.map(&:to_s) : [key]
  end
end

Jekyll::Hooks.register :site, :post_read do |site|
  authors = site.data["authors"] || {}
  site.posts.docs.each { |doc| doc.data["author_keys"] = SigmodAuthors.keys_for(doc, authors) }
end

class SigmodAuthorPages < Jekyll::Generator
  safe true
  priority :low

  def generate(site)
    authors = site.data["authors"] || {}
    newest_first = site.posts.docs.sort_by(&:date).reverse
    by_person = Hash.new { |h, k| h[k] = [] }
    newest_first.each { |doc| doc.data["author_keys"].each { |k| by_person[k] << doc } }

    by_person.each_key do |k|
      Jekyll.logger.warn "Authors:", "no _data/authors.yml entry for \"#{k}\"" unless authors[k]
    end

    # A page for every person (and combined byline) that has posts but no file in author/.
    have = site.pages.map(&:url)
    authors.each do |key, info|
      url = "/author/#{key}/"
      next if have.include?(url) || (by_person[key].empty? && !info["members"])

      page = Jekyll::PageWithoutAFile.new(site, site.source, "author/#{key}", "index.html")
      page.data.merge!("layout" => "author", "title" => info["name"] || key, "author" => key)
      site.pages << page
    end

    # Posts for each author page: a person's own and co-written posts; for a
    # combined byline, the posts published under it.
    site.pages.each do |page|
      next unless page.data["layout"] == "author"

      key = page.data["author"].to_s
      page.data["author_posts"] =
        if (authors[key] || {})["members"]
          newest_first.select { |doc| doc.data["author"].to_s == key }
        else
          by_person[key]
        end
    end

    site.data["author_index"] = by_person.filter_map do |key, docs|
      info = authors[key] || {}
      next if info["members"]

      { "key" => key, "name" => info["name"] || key, "avatar" => info["avatar"],
        "count" => docs.size, "latest" => docs.first.date }
    end.sort_by { |row| row["name"].downcase }
  end
end
