// JLPT exam timer + answer sheet interactions
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
      const h = Math.floor(s / 3600);
      const m = Math.floor((s % 3600) / 60);
      const sec = s % 60;
      const pad = (n) => n.toString().padStart(2, '0');
      if (h > 0) return `${pad(h)}:${pad(m)}:${pad(sec)}`;
      return `${pad(m)}:${pad(sec)}`;
    },
  };
}

async function saveExamAnswer(form, extra = {}) {
  const fd = new FormData(form);
  fd.set('action', extra.action || 'save');
  if (extra.answer !== undefined) fd.set('answer', String(extra.answer));
  if (extra.q_idx !== undefined) fd.set('q_idx', String(extra.q_idx));
  if (extra.question_id) fd.set('question_id', extra.question_id);
  const res = await fetch(form.action, { method: 'POST', body: fd, credentials: 'same-origin' });
  return res;
}

function updateSheetRow(qid, answerIdx) {
  document.querySelectorAll('[data-pick-answer]').forEach((btn) => {
    if (btn.dataset.qid !== qid) return;
    const picked = parseInt(btn.dataset.answer, 10) === answerIdx;
    btn.classList.toggle('is-picked', picked);
  });
}

document.addEventListener('DOMContentLoaded', () => {
  const form = document.getElementById('exam-form');
  if (!form) return;

  form.querySelectorAll('input[type=radio][name=answer]').forEach((radio) => {
    radio.addEventListener('change', async function () {
      const qid = form.querySelector('input[name=question_id]')?.value;
      const answer = parseInt(this.value, 10);
      await saveExamAnswer(form, { action: 'save', answer });
      if (qid) updateSheetRow(qid, answer);
      form.querySelectorAll('.exam-option-card').forEach((card) => {
        card.classList.remove('is-selected');
      });
      this.closest('.exam-option-card')?.classList.add('is-selected');
    });
  });

  document.querySelectorAll('[data-pick-answer]').forEach((btn) => {
    btn.addEventListener('click', async () => {
      const qIdx = btn.dataset.qIdx;
      const qid = btn.dataset.qid;
      const answer = parseInt(btn.dataset.answer, 10);
      const currentIdx = form.querySelector('input[name=q_idx]')?.value;

      await saveExamAnswer(form, {
        action: 'save',
        answer,
        q_idx: qIdx,
        question_id: qid,
      });

      updateSheetRow(qid, answer);

      if (String(qIdx) !== String(currentIdx)) {
        const base = window.location.pathname;
        window.location.href = `${base}?q=${qIdx}`;
      } else {
        const radio = form.querySelector(`input[name=answer][value="${answer}"]`);
        if (radio) {
          radio.checked = true;
          form.querySelectorAll('.exam-option-card').forEach((c) => c.classList.remove('is-selected'));
          radio.closest('.exam-option-card')?.classList.add('is-selected');
        }
      }
    });
  });
});
