// Progressive enhancement only — the page is fully readable and usable without this file.
document.querySelectorAll("[data-copy-target]").forEach(function (btn) {
  btn.addEventListener("click", function () {
    var target = document.getElementById(btn.getAttribute("data-copy-target"));
    if (!target || !navigator.clipboard) return;
    navigator.clipboard.writeText(target.textContent.trim()).then(function () {
      var original = btn.textContent;
      btn.textContent = "Copied";
      setTimeout(function () {
        btn.textContent = original;
      }, 1500);
    });
  });
});
