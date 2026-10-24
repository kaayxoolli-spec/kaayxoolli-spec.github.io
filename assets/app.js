// Recherche et filtres sur les annonces déjà présentes dans la page.
(function () {
  const $ = id => document.getElementById(id);
  const norm = s => String(s || "").toLowerCase().normalize("NFD").replace(/[̀-ͯ]/g, "");
  const fdate = s => { if (!s) return ""; const [y, m, d] = s.split("-"); return `${d}/${m}/${y}`; };

  async function copy(text, btn) {
    const label = btn.textContent;
    try { await navigator.clipboard.writeText(text); btn.textContent = "Copié"; }
    catch { btn.textContent = "Copie impossible"; }
    setTimeout(() => { btn.textContent = label; }, 2000);
  }

  document.addEventListener("click", e => {
    const c = e.target.closest("[data-copy]");
    if (c) copy(c.dataset.copy, c);
  });

  const list = $("list");
  if (list) {
    const cards = [...list.querySelectorAll(".card")];
    let type = "", cat = "";
    const params = new URLSearchParams(location.search);
    if (params.get("q")) $("q").value = params.get("q");

    function apply() {
      const terms = norm($("q").value.trim()).split(/\s+/).filter(Boolean);
      let shown = 0;
      for (const c of cards) {
        const ok = (!type || c.dataset.type === type) && (!cat || c.dataset.cat === cat) &&
          terms.every(t => c.dataset.text.includes(t));
        c.hidden = !ok;
        if (ok) shown++;
      }
      if (cards.length) $("count").textContent = `${shown} annonce${shown > 1 ? "s" : ""}`;
      $("none").hidden = !cards.length || shown > 0;
    }
    for (const c of cards) c.dataset.text = norm(c.textContent);

    $("types").addEventListener("click", e => {
      const b = e.target.closest("[data-t]"); if (!b) return;
      type = b.dataset.t;
      $("types").querySelectorAll(".chip").forEach(x => x.setAttribute("aria-pressed", x === b));
      apply();
    });
    $("cats").addEventListener("click", e => {
      const b = e.target.closest("[data-c]"); if (!b) return;
      cat = b.dataset.c;
      $("cats").querySelectorAll(".chip").forEach(x => x.setAttribute("aria-pressed", x === b));
      apply();
    });
    $("q").addEventListener("input", apply);
    $("search-form").addEventListener("submit", e => { e.preventDefault(); apply(); $("t-annonces").scrollIntoView({ block: "start" }); });
    $("quick").addEventListener("click", e => { const b = e.target.closest("[data-q]"); if (!b) return; $("q").value = b.dataset.q; apply(); });
    $("reset")?.addEventListener("click", () => { $("q").value = ""; $("types").querySelector("[data-t='']").click(); $("cats").querySelector("[data-c='']").click(); });
    apply();
  }

  const form = $("form");
  if (form) {
    form.addEventListener("submit", e => {
      e.preventDefault();
      const v = id => $(id).value.trim();
      if (!v("f-quoi") || !v("f-ou")) { $("err").textContent = "Indiquez au moins ce que c'est et où."; $("err").hidden = false; return; }
      $("err").hidden = true;
      const lines = ["Bonjour Kaay Xool, je souhaite publier une annonce.", "",
        `Type : ${v("f-type")}`, `Catégorie : ${v("f-cat")}`, `Quoi : ${v("f-quoi")}`, `Où : ${v("f-ou")}, ${v("f-ville")}`];
      if (v("f-quand")) lines.push(`Quand : ${fdate(v("f-quand"))}`);
      if (v("f-signe")) lines.push(`Signe distinctif : ${v("f-signe")}`);
      if (v("f-nom")) lines.push(`Prénom : ${v("f-nom")}`);
      $("out").textContent = lines.join("\n");
      $("copy").dataset.copy = lines.join("\n");
      $("mail").href = "mailto:kaayxoolli@gmail.com?subject=" + encodeURIComponent(`Annonce Kaay Xool : ${v("f-type")} - ${v("f-quoi")}`) + "&body=" + encodeURIComponent(lines.join("\n"));
      $("result").hidden = false;
      $("result").scrollIntoView({ behavior: matchMedia("(prefers-reduced-motion: reduce)").matches ? "auto" : "smooth", block: "nearest" });
    });
    $("f-type").addEventListener("change", () => { if ($("f-type").value === "Personne recherchée") $("f-cat").value = "Personnes"; });
  }
})();
