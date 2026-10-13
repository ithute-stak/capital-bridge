"use strict";
(() => {
  const toggle = document.getElementById("menu-toggle");
  const nav = document.getElementById("site-nav");
  if (toggle && nav) {
    const close = () => {nav.classList.remove("open");toggle.setAttribute("aria-expanded","false");toggle.setAttribute("aria-label","Open navigation");};
    toggle.addEventListener("click", () => {
      const isOpen = nav.classList.toggle("open");
      toggle.setAttribute("aria-expanded",String(isOpen));
      toggle.setAttribute("aria-label",isOpen?"Close navigation":"Open navigation");
    });
    for(const anchor of nav.querySelectorAll("a")) anchor.addEventListener("click",close);
    document.addEventListener("keydown", (event) => {if(event.key==="Escape") close();});
  }
  const year=document.getElementById("year");
  if(year) year.textContent=String(new Date().getFullYear());
})();