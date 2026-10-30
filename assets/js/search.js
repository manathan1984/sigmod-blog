(function () {
  var script = document.currentScript;
  var input = document.getElementById("search-input");
  var out = document.getElementById("search-results");
  var q = new URLSearchParams(location.search).get("q") || "";
  input.value = q;
  if (!q.trim()) return;

  function esc(s) {
    return String(s).replace(/[&<>"]/g, function (c) {
      return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c];
    });
  }

  fetch(script.dataset.index)
    .then(function (r) { return r.json(); })
    .then(function (posts) {
      var terms = q.toLowerCase().split(/\s+/).filter(Boolean);
      var hits = posts.filter(function (p) {
        var hay = (p.title + " " + p.author + " " + p.categories.join(" ")).toLowerCase() + " " + p.text;
        return terms.every(function (t) { return hay.indexOf(t) !== -1; });
      });
      out.innerHTML = "<p class=\"small\">" + hits.length + " result" + (hits.length === 1 ? "" : "s") +
        " for &ldquo;" + esc(q) + "&rdquo;</p>" +
        hits.map(function (p) {
          return "<article class=\"post-card\"><h2 class=\"entry-title\"><a href=\"" + esc(p.url) + "\">" +
            esc(p.title) + "</a></h2><p class=\"post-meta\">by " + esc(p.author) + " on " + esc(p.date) +
            "</p><p class=\"post-excerpt\">" + esc(p.excerpt) + "</p></article>";
        }).join("");
    })
    .catch(function () { out.textContent = "Search is unavailable right now."; });
})();
