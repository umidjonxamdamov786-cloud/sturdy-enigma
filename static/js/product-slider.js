document.addEventListener("DOMContentLoaded", function () {
  document.querySelectorAll("[data-product-slider]").forEach(function (slider) {
    const track = slider.querySelector("[data-product-track]");
    const dotsBox = slider.querySelector("[data-product-dots]");
    const slides = track ? Array.from(track.children) : [];
    if (!track || slides.length < 1) return;

    let current = 0;
    slides.forEach(function (_, i) {
      const dot = document.createElement("button");
      dot.type = "button";
      dot.className = "product-detail-dot";
      dot.setAttribute("aria-label", "Rasm " + (i + 1));
      dot.addEventListener("click", function () { show(i); });
      dotsBox.appendChild(dot);
    });

    function show(i) {
      current = (i + slides.length) % slides.length;
      track.style.transform = "translateX(-" + (current * 100) + "%)";
      Array.from(dotsBox.children).forEach(function (dot, n) {
        dot.classList.toggle("active", n === current);
      });
    }

    const prev = slider.querySelector("[data-product-prev]");
    const next = slider.querySelector("[data-product-next]");
    prev.addEventListener("click", function () { show(current - 1); });
    next.addEventListener("click", function () { show(current + 1); });
    if (slides.length <= 1) {
      prev.hidden = true;
      next.hidden = true;
      dotsBox.hidden = true;
    }
    show(0);
  });
});
