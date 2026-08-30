(() => {
  const openButton = document.querySelector('[data-open-seal]');
  const sealedScroll = document.querySelector('[data-sealed-scroll]');
  const openedScroll = document.querySelector('[data-opened-scroll]');
  const title = document.querySelector('[data-message-title]');

  if (!openButton || !sealedScroll || !openedScroll) {
    return;
  }

  openButton.addEventListener('click', () => {
    sealedScroll.hidden = true;
    openedScroll.hidden = false;

    if (title) {
      title.textContent = 'Opened Letter';
    }
  });
})();
