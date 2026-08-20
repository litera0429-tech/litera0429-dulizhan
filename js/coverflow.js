(function () {
  "use strict";

  /* Coverflow 封面轮播 — 由 React CoverflowCarousel 原样移植为原生 JS。
     图片与文案对应原演示组件；数据来源：content/site.json 的 carousel 数组。 */

  var R2 = "https://pub-940ccf6255b54fa799a9b01050e6c227.r2.dev/stock-images";
  var UNSPLASH = function (id) {
    return (
      "https://images.unsplash.com/photo-" + id +
      "?w=640&h=640&fit=crop&q=70&auto=format"
    );
  };

  var DEFAULT_CAROUSEL = [
    {
      src: R2 + "/767d99bb371a54d0d36751e8cecae43c.jpg",
      alt: "夕阳海景中潜水者的剪影，形似一幅侧脸人像",
      title: "潮汐",
      subtitle: "全长专辑",
      meta: [
        { label: "年份", value: "2019" },
        { label: "制作人", value: "Ada Ferrow" },
        { label: "时长", value: "3:42" }
      ]
    },
    {
      src: R2 + "/821d815affa6496c39cbdeeec7a84603.jpg",
      alt: "黄昏城市天际线与人物肖像的双重曝光",
      title: "夜巡",
      subtitle: "全长专辑",
      meta: [
        { label: "年份", value: "2021" },
        { label: "制作人", value: "Kell Mora" },
        { label: "时长", value: "4:08" }
      ]
    },
    {
      src: R2 + "/937438c560ada1c83317f2c11b3454b0.jpg",
      alt: "深橙色背景下侧脸人像的动感模糊",
      title: "过曝",
      subtitle: "单曲",
      meta: [
        { label: "年份", value: "2018" },
        { label: "制作人", value: "Juno Vale" },
        { label: "时长", value: "2:57" }
      ]
    },
    {
      src: R2 + "/98f89cb9994f5c382ab964062c4039db.jpg",
      alt: "黄昏中手持球拍的身影，球拍化作旋涡云层",
      title: "慢绽",
      subtitle: "EP",
      meta: [
        { label: "年份", value: "2022" },
        { label: "制作人", value: "Rue Alcott" },
        { label: "时长", value: "3:15" }
      ]
    },
    {
      src: R2 + "/ddcbee38be8b7274e19e132d7ab35b53.jpg",
      alt: "手指间的剪影，一只飞鸟穿过指缝",
      title: "摊掌",
      subtitle: "单曲",
      meta: [
        { label: "年份", value: "2020" },
        { label: "制作人", value: "Ada Ferrow" },
        { label: "时长", value: "3:01" }
      ]
    },
    {
      src: UNSPLASH("1470071459604-3b5ec3a7fe05"),
      alt: "晨光中雾气漫过森林山谷",
      title: "低地",
      subtitle: "全长专辑",
      meta: [
        { label: "年份", value: "2017" },
        { label: "制作人", value: "Sim Oyo" },
        { label: "时长", value: "5:20" }
      ]
    },
    {
      src: UNSPLASH("1500534314209-a25ddb2bd429"),
      alt: "湛蓝天空下阳光照耀的沙丘山脊",
      title: "旱季",
      subtitle: "EP",
      meta: [
        { label: "年份", value: "2016" },
        { label: "制作人", value: "Juno Vale" },
        { label: "时长", value: "2:44" }
      ]
    },
    {
      src: UNSPLASH("1441974231531-c6227db76b6e"),
      alt: "阳光穿过茂密树林",
      title: "林下",
      subtitle: "单曲",
      meta: [
        { label: "年份", value: "2023" },
        { label: "制作人", value: "Kell Mora" },
        { label: "时长", value: "3:38" }
      ]
    },
    {
      src: UNSPLASH("1493246507139-91e8fad9978e"),
      alt: "浅色背景上彩色烟雾的粉彩抽象",
      title: "纸灯笼",
      subtitle: "单曲",
      meta: [
        { label: "年份", value: "2021" },
        { label: "制作人", value: "Rue Alcott" },
        { label: "时长", value: "2:19" }
      ]
    },
    {
      src: UNSPLASH("1501785888041-af3ef285b470"),
      alt: "暮色中山脊倒映在湖面",
      title: "静水",
      subtitle: "全长专辑",
      meta: [
        { label: "年份", value: "2015" },
        { label: "制作人", value: "Ada Ferrow" },
        { label: "时长", value: "4:51" }
      ]
    },
    {
      src: UNSPLASH("1465101162946-4377e57745c3"),
      alt: "暗色风景上长曝光留下的光轨",
      title: "第三轨",
      subtitle: "EP",
      meta: [
        { label: "年份", value: "2024" },
        { label: "制作人", value: "Sim Oyo" },
        { label: "时长", value: "3:07" }
      ]
    },
    {
      src: UNSPLASH("1519681393784-d120267933ba"),
      alt: "清冷晨光下白雪覆盖的山峰",
      title: "暗流",
      subtitle: "单曲",
      meta: [
        { label: "年份", value: "2020" },
        { label: "制作人", value: "Juno Vale" },
        { label: "时长", value: "3:29" }
      ]
    }
  ];

  var section = document.getElementById("coverflow");
  var frame = document.getElementById("cfFrame");
  var track = document.getElementById("cfTrack");
  var caption = document.getElementById("cfCaption");
  if (!section || !frame || !track || !caption) return;

  /* 进入视口时柔滑显现：RECOMMEND 标题与轮播依次淡入上移 */
  if ("IntersectionObserver" in window) {
    var cfReduced =
      window.matchMedia &&
      window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    if (!cfReduced) {
      var cfStage = section.querySelector(".cf-stage");
      if (cfStage) {
        var cfIo = new IntersectionObserver(
          function (entries) {
            entries.forEach(function (entry) {
              if (entry.isIntersecting) {
                section.classList.add("cf-in");
                cfIo.disconnect();
              }
            });
          },
          { threshold: 0.9 }
        );
        cfIo.observe(cfStage);
      }
    }
  }

  var CF = {
    rotate: 44,
    depth: 0.6,
    perspective: 3,
    falloff: 0.56,
    fade: 0.1,
    cardWidth: "clamp(148px, 22vw, 260px)",
    gap: 0.05,
    loop: true
  };

  var slides = [];
  var cardEls = [];
  var count = 0;
  var selected = 0;
  var pos = 0; // 小数卡位：当前“正中”位置
  var target = 0; // 本次归位要去的地方
  var width = 0;
  var raf = null;
  var drag = null;
  var justDragged = false; // 拖拽后松开，避免误触发生跳转

  section.style.setProperty("--cf-card", CF.cardWidth);
  frame.style.perspective = "calc(var(--cf-card) * " + CF.perspective + ")";

  function indexAt(p) {
    return ((Math.round(p) % count) + count) % count;
  }

  /* 直接写样式，跟原组件一致：倾斜/后退都随距离衰减，环状折返 */
  function paint() {
    if (!width) return;
    var pitch = width * (1 + CF.gap);
    for (var i = 0; i < count; i++) {
      var card = cardEls[i];
      if (!card) continue;

      var offset = i - pos;
      if (CF.loop) {
        offset = ((offset % count) + count) % count;
        if (offset > count / 2) offset -= count;
      }

      var distance = Math.abs(offset);
      var ramp = Math.pow(distance, CF.falloff);
      var tilt = Math.min(CF.rotate * ramp, 82) * Math.sign(offset);

      card.style.transform =
        "translateX(calc(-50% + " + offset * pitch + "px)) " +
        "translateZ(" + -CF.depth * width * ramp + "px) rotateY(" + -tilt + "deg)";

      var edge = CF.loop ? Math.min(1, Math.max(0, count / 2 - distance)) : 1;
      card.style.opacity = String(Math.max(0, 1 - CF.fade * distance) * edge);
      card.style.zIndex = String(100 - Math.round(distance));
    }
  }

  function settle(t) {
    if (raf !== null) cancelAnimationFrame(raf);
    target = t;
    selected = indexAt(t);
    updateCaption();

    var step = function () {
      var remaining = target - pos;
      if (Math.abs(remaining) < 0.0004) {
        pos = target;
        paint();
        raf = null;
        return;
      }
      pos += remaining * 0.16;
      paint();
      raf = requestAnimationFrame(step);
    };
    raf = requestAnimationFrame(step);
  }

  function clamp(p) {
    return CF.loop ? p : Math.max(0, Math.min(count - 1, p));
  }

  function nudge(by) {
    settle(clamp(Math.round(target) + by));
  }

  /* ---------- 拖拽：横向拖动归我们管，页面保留竖向滚动 ---------- */
  frame.addEventListener("pointerdown", function (event) {
    if (raf !== null) {
      cancelAnimationFrame(raf);
      raf = null;
    }
    event.currentTarget.setPointerCapture(event.pointerId);
    frame.classList.add("grabbing");
    target = pos;
    drag = {
      id: event.pointerId,
      x: event.clientX,
      pos: pos,
      v: 0,
      t: performance.now(),
      moved: false
    };
  });

  frame.addEventListener("pointermove", function (event) {
    if (!drag || drag.id !== event.pointerId) return;
    var pitch = width * (1 + CF.gap);
    if (!pitch) return;

    var now = performance.now();
    var previous = pos;
    if (Math.abs(event.clientX - drag.x) > 6) drag.moved = true;
    pos = clamp(drag.pos - (event.clientX - drag.x) / pitch);
    drag.v = ((pos - previous) / Math.max(now - drag.t, 1)) * 1000;
    drag.t = now;

    var idx = indexAt(pos);
    if (idx !== selected) {
      selected = idx;
      updateCaption();
    }
    paint();
  });

  function endDrag(event) {
    if (!drag || drag.id !== event.pointerId) return;
    // 甩动惯性：最多再带两张
    var carried = Math.max(-2, Math.min(2, drag.v * 0.18));
    if (drag.moved) {
      justDragged = true;
      setTimeout(function () { justDragged = false; }, 350);
    }
    drag = null;
    frame.classList.remove("grabbing");
    settle(clamp(Math.round(pos + carried)));
  }

  frame.addEventListener("pointerup", endDrag);
  frame.addEventListener("pointercancel", endDrag);

  /* ---------- 键盘 ---------- */
  frame.addEventListener("keydown", function (event) {
    if (event.key === "ArrowLeft") {
      event.preventDefault();
      nudge(-1);
    } else if (event.key === "ArrowRight") {
      event.preventDefault();
      nudge(1);
    }
  });

  /* ---------- 宽度测量（响应式变化时重画） ---------- */
  if (typeof ResizeObserver !== "undefined") {
    var ro = new ResizeObserver(function () {
      var first = cardEls[0];
      if (!first) return;
      width = first.offsetWidth;
      paint();
    });
    ro.observe(frame);
  }

  /* ---------- 说明区：标题 + 副标题 + 元信息，对应原组件 caption ---------- */
  function updateCaption() {
    var s = slides[selected];
    if (!s) return;
    caption.innerHTML = "";

    if (s.title) {
      var t = document.createElement("p");
      t.className = "cf-title";
      t.textContent = s.title;
      caption.appendChild(t);
    }
    if (s.subtitle) {
      var st = document.createElement("p");
      st.className = "cf-subtitle";
      st.textContent = s.subtitle;
      caption.appendChild(st);
    }
    if (s.meta && s.meta.length) {
      var dl = document.createElement("dl");
      dl.className = "cf-meta";
      s.meta.forEach(function (row) {
        var rowEl = document.createElement("div");
        rowEl.className = "cf-meta-row";
        var dt = document.createElement("dt");
        dt.textContent = row.label;
        var dd = document.createElement("dd");
        dd.textContent = row.value;
        rowEl.appendChild(dt);
        rowEl.appendChild(dd);
        dl.appendChild(rowEl);
      });
      caption.appendChild(dl);
    }

    caption.classList.remove("cf-fade");
    void caption.offsetWidth; // 重新触发淡入
    caption.classList.add("cf-fade");
  }

  function render(data) {
    slides = data;
    count = slides.length;
    selected = 0;
    pos = 0;
    target = 0;
    track.innerHTML = "";
    cardEls = [];

    slides.forEach(function (s, i) {
      var d = document.createElement("div");
      d.className = "cf-card";
      d.setAttribute("role", "group");
      d.setAttribute("aria-roledescription", "slide");
      d.setAttribute("aria-label", "第 " + (i + 1) + " 张，共 " + count + " 张");
      var img = document.createElement("img");
      img.src = s.src;
      img.alt = s.alt || "";
      img.draggable = false;
      d.appendChild(img);
      d.addEventListener("click", function () {
        if (justDragged) return;
        window.location.href = "footprint.html";
      });
      track.appendChild(d);
      cardEls.push(d);
    });

    updateCaption();
    requestAnimationFrame(function () {
      var first = cardEls[0];
      if (first) width = first.offsetWidth;
      paint();
    });
  }

  fetch("content/site.json")
    .then(function (r) { return r.json(); })
    .then(function (data) {
      if (data && Array.isArray(data.carousel) && data.carousel.length) {
        render(data.carousel);
      } else {
        render(DEFAULT_CAROUSEL);
      }
    })
    .catch(function () {
      render(DEFAULT_CAROUSEL);
    });
})();
