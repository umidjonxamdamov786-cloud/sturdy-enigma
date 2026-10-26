(function () {
  document.querySelectorAll('[data-slider]').forEach(function (slider) {
    var track = slider.querySelector('[data-track]');
    var slides = track ? Array.from(track.children) : [];
    var dots = slider.querySelector('[data-dots]');
    var prev = slider.querySelector('[data-prev]');
    var next = slider.querySelector('[data-next]');
    var controls = slider.querySelector('[data-controls]');
    var index = 0;

    if (!slides.length) {
      slider.innerHTML = '<p class="empty-note">Mahsulot rasmi mavjud emas.</p>';
      return;
    }
    if (slides.length < 2) {
      if (controls) controls.style.display = 'none';
      return;
    }

    function show(n) {
      index = (n + slides.length) % slides.length;
      track.style.transform = 'translateX(-' + index * 100 + '%)';
      Array.from(dots.children).forEach(function (d, i) {
        d.classList.toggle('active', i === index);
      });
    }

    slides.forEach(function (_, i) {
      var b = document.createElement('button');
      b.type = 'button';
      b.className = 'gallery-dot';
      b.setAttribute('aria-label', 'Rasm ' + (i + 1));
      b.addEventListener('click', function () { show(i); });
      dots.appendChild(b);
    });
    prev.addEventListener('click', function () { show(index - 1); });
    next.addEventListener('click', function () { show(index + 1); });
    show(0);
  });
})();
