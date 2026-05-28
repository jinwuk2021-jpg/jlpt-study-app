// Exam timer Alpine component
function examTimer(initialSeconds) {
  return {
    time: initialSeconds,
    init() {
      setInterval(() => {
        if (this.time > 0) this.time--;
        if (this.time === 0) {
          document.getElementById('exam-form')?.querySelector('[name=action][value=submit]')?.click();
        }
      }, 1000);
    },
    formatTime(s) {
      const m = Math.floor(s / 60);
      const sec = s % 60;
      return `${m.toString().padStart(2, '0')}:${sec.toString().padStart(2, '0')}`;
    }
  };
}

document.addEventListener('DOMContentLoaded', () => {
  document.querySelectorAll('input[type=radio][name=answer]').forEach(radio => {
    radio.addEventListener('change', function () {
      const form = this.closest('form');
      if (form) {
        const action = form.querySelector('[name=action]');
        if (action) action.value = 'save';
        form.submit();
      }
    });
  });
});
