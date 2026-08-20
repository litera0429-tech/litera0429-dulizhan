/* Hero07：滚动显现（subtle）+ 大图视差，尊重系统减弱动态设置 */
(function () {
  var section = document.getElementById("editorial");
  if (!section) return;

  var reduced =
    window.matchMedia &&
    window.matchMedia("(prefers-reduced-motion: reduce)").matches;

  var img = section.querySelector(".zz-hero07-img");
  var revealItems = section.querySelectorAll(".zz-rv");

  /* 入场显现：进入视口后给区块加 .is-in */
  if (!reduced && "IntersectionObserver" in window && revealItems.length > 0) {
    section.setAttribute("data-anim", "on");
    var io = new IntersectionObserver(
      function (entries) {
        entries.forEach(function (entry) {
          if (entry.isIntersecting) {
            section.classList.add("is-in");
          } else {
            section.classList.remove("is-in");
          }
        });
      },
      { threshold: 0.12, rootMargin: "0px 0px -40px 0px" }
    );
    io.observe(section);
  }

  /* 大图视差：滚动时图片在框内缓慢上下移动 */
  if (!reduced && img) {
    var ticking = false;

    function updateParallax() {
      ticking = false;
      var r = section.getBoundingClientRect();
      var vh = window.innerHeight || document.documentElement.clientHeight;
      if (r.bottom < -240 || r.top > vh + 240) return;
      var total = vh + r.height;
      var p = Math.min(1, Math.max(0, (vh - r.top) / total));
      var shift = (0.08 - 0.16 * p) * r.height;
      img.style.transform = "translate3d(0, " + shift.toFixed(2) + "px, 0)";
    }

    function requestTick() {
      if (!ticking) {
        ticking = true;
        window.requestAnimationFrame(updateParallax);
      }
    }

    window.addEventListener("scroll", requestTick, { passive: true });
    window.addEventListener("resize", requestTick);
    updateParallax();
  }
})();
