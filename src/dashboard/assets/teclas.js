// Na ficha do edital, j avança e k volta na fila atual.
document.addEventListener("keydown", function (ev) {
  if (ev.ctrlKey || ev.metaKey || ev.altKey) return;
  var alvo = ev.target;
  if (alvo && (alvo.tagName === "INPUT" || alvo.tagName === "TEXTAREA" || alvo.isContentEditable)) return;
  var tecla = ev.key.toLowerCase();
  if (tecla !== "j" && tecla !== "k") return;
  var link = document.getElementById("tecla-" + tecla);
  if (link) {
    ev.preventDefault();
    link.click();
    window.scrollTo(0, 0);
  }
});
