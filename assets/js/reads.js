// Adds the new GoatCounter views to the old WordPress count shown under a post
// (see _includes/post-meta.html). Without JavaScript the old count stays.
(function () {
  var el = document.querySelector(".reads[data-path]");
  if (!el || !window.fetch) return;
  var legacy = parseInt(el.getAttribute("data-legacy"), 10) || 0;
  fetch(el.getAttribute("data-counter") + encodeURIComponent(el.getAttribute("data-path")) + ".json")
    .then(function (r) { return r.ok ? r.json() : { count: "0" }; })  // 404: no views yet
    .then(function (d) {
      var n = legacy + (parseInt(String(d.count).replace(/\D/g, ""), 10) || 0);
      if (!n) return;
      el.querySelector(".reads-n").textContent = n.toLocaleString("en-US");
      el.hidden = false;
    })
    .catch(function () {});
})();
