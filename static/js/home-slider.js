(() => {
  const slider = document.querySelector('[data-home-slider]');
  if (!slider) return;
  const track = slider.querySelector('.home-slider__track');
  const slides = Array.from(track.children);
  const dotsBox = slider.querySelector('.home-slider__dots');
  const prev = slider.querySelector('[data-slider-prev]');
  const next = slider.querySelector('[data-slider-next]');
  if (slides.length < 2) return;
  let index = 0;
  let timer;
  const dots = slides.map((_, i) => {
    const dot = document.createElement('button');
    dot.type = 'button';
    dot.className = 'home-slider__dot';
    dot.setAttribute('aria-label', `Slayd ${i + 1}`);
    dot.addEventListener('click', () => show(i));
    dotsBox.appendChild(dot);
    return dot;
  });
  function show(nextIndex) {
    index = (nextIndex + slides.length) % slides.length;
    track.style.transform = `translateX(-${index * 100}%)`;
    dots.forEach((dot, i) => {
      dot.classList.toggle('is-active', i === index);
      dot.setAttribute('aria-current', i === index ? 'true' : 'false');
    });
  }
  function start() { stop(); timer = window.setInterval(() => show(index + 1), 5000); }
  function stop() { if (timer) window.clearInterval(timer); }
  prev.addEventListener('click', () => { show(index - 1); start(); });
  next.addEventListener('click', () => { show(index + 1); start(); });
  slider.addEventListener('mouseenter', stop);
  slider.addEventListener('mouseleave', start);
  slider.addEventListener('focusin', stop);
  slider.addEventListener('focusout', start);
  show(0);
  start();
})();
