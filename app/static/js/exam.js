// Exam timer — per JLPT section (official) or full exam
function examTimer(initialSeconds, hasNextPhase) {
  return {
    time: initialSeconds,
    hasNextPhase: !!hasNextPhase,
    init() {
      setInterval(() => {
        if (this.time > 0) this.time--;
        if (this.time === 0) {
          const form = document.getElementById('exam-form');
          if (!form) return;
          if (this.hasNextPhase) {
            const btn = form.querySelector('[name=action][value=next_phase]');
            if (btn) {
              btn.click();
              return;
            }
          }
          const submit = form.querySelector('[name=action][value=submit]');
          if (submit) submit.click();
        }
      }, 1000);
    },
    formatTime(s) {
      const m = Math.floor(s / 60);
      const sec = s % 60;
      return `${m.toString().padStart(2, '0')}:${sec.toString().padStart(2, '0')}`;
    },
  };
}

document.addEventListener('DOMContentLoaded', () => {
  document.querySelectorAll('input[type=radio][name=answer]').forEach((radio) => {
    radio.addEventListener('change', function () {
      const form = this.closest('form');
      if (!form) return;
      const hidden = form.querySelector('input[name=action]');
      if (hidden) hidden.value = 'save';
      const fd = new FormData(form);
      fd.set('action', 'save');
      fetch(form.action, { method: 'POST', body: fd, credentials: 'same-origin' });
    });
  });
});
