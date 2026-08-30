(() => {
  const form = document.querySelector('[data-letter-form]');
  if (!form) {
    return;
  }

  form.addEventListener('submit', () => {
    form.querySelectorAll('[data-field]').forEach((editor) => {
      const input = form.querySelector(`[name="${editor.dataset.field}"]`);
      input.value = editor.innerText.trim();
    });
  });
})();
