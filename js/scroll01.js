/* Scroll01：滚动时文字与图片联动（对应 React 组件 Scroll01），尊重系统减弱动态设置 */
(function () {
  var section = document.getElementById("scroll01");
  if (!section) return;

  var reduced =
    window.matchMedia &&
    window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  var desktop =
    window.matchMedia && window.matchMedia("(min-width: 768px)").matches;

  var items = Array.prototype.slice.call(
    section.querySelectorAll(".zz-scroll01-copy .zz-scroll01-item")
  );
  var imgs = Array.prototype.slice.call(
    section.querySelectorAll(".zz-scroll01-stage .zz-scroll01-img")
  );

  if (reduced || !desktop || items.length === 0 || imgs.length === 0) return;

  var activeIndex = 0;

  function setActive(index) {
    if (index === activeIndex) return;
    activeIndex = index;
    items.forEach(function (el, i) {
      el.classList.toggle("is-active", i === index);
    });
    imgs.forEach(function (el, i) {
      el.classList.toggle("is-active", i === index);
    });
  }

  function update() {
    var vh = window.innerHeight || document.documentElement.clientHeight;
    var target = vh * 0.5;
    var best = 0;
    var bestDist = Infinity;

    for (var i = 0; i < items.length; i++) {
      var r = items[i].getBoundingClientRect();
      var center = r.top + r.height / 2;
      var dist = Math.abs(center - target);

      if (dist < bestDist) {
        bestDist = dist;
        best = i;
      }

      var fade = Math.min(1, dist / (vh * 0.3));
      var offset = Math.max(-20, Math.min(20, (center - target) * 0.02));
      items[i].style.opacity = String(1 - fade);
      items[i].style.transform =
        "translate3d(0, " + offset.toFixed(2) + "px, 0)";
    }

    setActive(best);
  }

  var ticking = false;
  function requestTick() {
    if (ticking) return;
    ticking = true;
    window.requestAnimationFrame(function () {
      ticking = false;
      update();
    });
  }

  window.addEventListener("scroll", requestTick, { passive: true });
  window.addEventListener("resize", requestTick);
  update();
})();
