(function () {
  var input = document.getElementById("filter");
  if (!input) return;
  var rows = Array.prototype.slice.call(
    document.querySelectorAll("#catalogue tbody tr")
  );
  var shown = document.getElementById("shown");

  function matches(data, query) {
    if (!query) return true;
    var words = data.split(/[^a-z0-9]+/);
    return query.split(/\s+/).every(function (token) {
      if (token.length <= 3) return words.indexOf(token) !== -1;
      return words.some(function (word) { return word.indexOf(token) === 0; });
    });
  }

  function update() {
    var query = input.value.trim().toLowerCase();
    var visible = 0;
    rows.forEach(function (row) {
      var hit = matches(row.getAttribute("data-search") || "", query);
      row.hidden = !hit;
      if (hit) visible += 1;
    });
    if (shown) shown.textContent = String(visible);
  }

  input.addEventListener("input", update);
  input.addEventListener("keydown", function (event) {
    if (event.key === "Escape") {
      input.value = "";
      update();
    }
  });
})();
