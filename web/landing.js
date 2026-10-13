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
  const tabs = Array.from(document.querySelectorAll(".mobile-bottom-nav [data-mobile-tab]"));
  const tabIds = new Set(tabs.map(tab => tab.dataset.mobileTab));
  function updateActiveTab(id) {
    if (!tabIds.has(id)) return;
    for (const tab of tabs) {
      if (tab.dataset.mobileTab === id) tab.setAttribute("aria-current","page");
      else tab.removeAttribute("aria-current");
    }
  }
  for (const tab of tabs) tab.addEventListener("click", () => updateActiveTab(tab.dataset.mobileTab));
  if (tabs.length && typeof IntersectionObserver === "function") {
    const visible = new Map();
    const observer = new IntersectionObserver(entries => {
      for (const entry of entries) {
        if (entry.isIntersecting) visible.set(entry.target.id, entry.boundingClientRect.top);
        else visible.delete(entry.target.id);
      }
      if (visible.size) updateActiveTab([...visible].sort((a,b)=>Math.abs(a[1])-Math.abs(b[1]))[0][0]);
    }, {rootMargin:"-15% 0px -55% 0px",threshold:0});
    for(const id of tabIds) {
      const element=document.getElementById(id);
      if(element) observer.observe(element);
    }
  }
  window.addEventListener("hashchange", () => {
    const id=location.hash.slice(1);
    if (tabIds.has(id)) updateActiveTab(id);
  });
  const year=document.getElementById("year");
  if(year) year.textContent=String(new Date().getFullYear());
})();