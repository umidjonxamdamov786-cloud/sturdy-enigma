(function () {
  // Sevimlilar tugmasi: sahifani yangilamasdan (AJAX) ishlaydi.
  // Xato bo'lsa — oddiy form yuborish (sahifa yangilanadi).
  document.addEventListener('submit', function (e) {
    var form = e.target.closest('form[data-wishlist-form]');
    if (!form) return;
    e.preventDefault();

    var token = form.querySelector('[name=csrfmiddlewaretoken]');
    fetch(form.action, {
      method: 'POST',
      headers: {
        'X-Requested-With': 'XMLHttpRequest',
        'X-CSRFToken': token ? token.value : ''
      },
      credentials: 'same-origin'
    })
      .then(function (r) {
        if (!r.ok) throw new Error('bad response');
        return r.json();
      })
      .then(function (data) {
        // Sevimlilar sahifasida "O'chirish" bosilsa — kartani olib tashlaymiz
        if (form.hasAttribute('data-remove')) {
          var card = form.closest('.card');
          if (card) card.remove();
        } else {
          var btn = form.querySelector('button');
          var label = data.added ? form.dataset.labelOn : form.dataset.labelOff;
          btn.textContent = label + ' (' + data.count + ')';
          btn.classList.toggle('liked', data.added);
          btn.setAttribute('aria-pressed', data.added ? 'true' : 'false');
        }
        document.querySelectorAll('[data-wishlist-count]').forEach(function (el) {
          el.textContent = data.total;
        });
      })
      .catch(function () { form.submit(); });
  });
})();
