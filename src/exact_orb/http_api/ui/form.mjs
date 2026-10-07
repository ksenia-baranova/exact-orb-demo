// REQ-UI-02/03: черновик хранит ввод, а отправляемый intent содержит только три поля API.
function calendarDate(value) {
  if (!/^[0-9]{4}-[0-9]{2}-[0-9]{2}$/.test(value)) return false;
  const [year, month, day] = value.split("-").map(Number);
  if (year === 0 || month < 1 || month > 12 || day < 1) return false;
  const leap = year % 4 === 0 && (year % 100 !== 0 || year % 400 === 0);
  const days = [31, leap ? 29 : 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31];
  return day <= days[month - 1];
}

export function createBirthForm() {
  const draft = { date: "", time: "", timeUnknown: false, query: "", place: null, acknowledged: false };
  let errors = {};
  function snapshot() {
    return { ...draft, place: draft.place === null ? null : { ...draft.place }, errors: { ...errors } };
  }
  return Object.freeze({
    snapshot,
    setDate(value) { draft.date = value; delete errors.date; },
    setTime(value) { draft.time = value; delete errors.time; },
    setUnknownTime(value) { draft.timeUnknown = value === true; delete errors.time; },
    editPlace(value) { draft.query = value; draft.place = null; delete errors.place; },
    selectPlace(item) {
      draft.place = { place_id: item.place_id, display_name: item.display_name,
        admin1_name: item.admin1_name, country_code: item.country_code };
      draft.query = item.display_name;
      delete errors.place;
    },
    acknowledge(value) { draft.acknowledged = value === true; delete errors.acknowledged; },
    prepareSubmission() {
      errors = {};
      if (!calendarDate(draft.date)) errors.date = "Укажите корректную дату рождения.";
      if (draft.place === null || typeof draft.place.place_id !== "string" || draft.place.place_id === "") {
        errors.place = "Выберите место рождения из списка.";
      }
      if (!draft.timeUnknown && !/^(?:[01][0-9]|2[0-3]):[0-5][0-9]$/.test(draft.time)) {
        errors.time = "Укажите время в формате ЧЧ:ММ или отметьте, что точное время неизвестно.";
      }
      if (!draft.acknowledged) errors.acknowledged = "Поставьте отметку ознакомления с условиями сервиса.";
      if (Object.keys(errors).length) return { ok: false, errors: { ...errors } };
      return { ok: true, intent: Object.freeze({ birth_date: draft.date,
        birth_time: draft.timeUnknown ? null : draft.time, place_id: draft.place.place_id }) };
    },
  });
}
