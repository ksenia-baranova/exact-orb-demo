// TASK-T-02: independent requirement oracles; shared leaf fixtures only.
import assert from 'node:assert/strict';
import { mountBirthForm } from '../../src/exact_orb/http_api/ui/main.mjs';
import { documentPort } from '../ui/fixtures/dom.mjs';
import { harness, views, ready, response, committed, failure, deferred, currentPath, buildPath } from '../ui/fixtures/session.mjs';

const scenario = process.argv[2];
let examples = 0;
const badOracle = process.env.TERMS_BAD_ORACLE === '1';
async function mount(saved = true) {
  const h = harness(), document = documentPort();
  if (saved) {
    const initial = ready(); initial.birth.birth_date = '1990-09-02'; initial.birth.place.display_name = 'Москва';
    h.queue(currentPath, response(initial));
  }
  const ui = mountBirthForm(document, { apiClient: h.apiClient, clock: h.clock });
  await ui.ready;
  return { h, ui, document, get: id => document.getElementById(id) };
}
function edit(m, id, value) {
  const node = m.get(id), check = typeof value === 'boolean';
  node[check ? 'checked' : 'value'] = value;
  node.emit(check ? 'change' : 'input');
}
function values(m) {
  const s = m.ui.form.snapshot();
  return { date: s.date, text: s.query, place: s.place, time: s.time,
    unknown: s.timeUnknown, raw: ['birth-date','birth-place','birth-time'].map(id => m.get(id).value) };
}
function open(m) {
  m.get('terms-link').click();
  assert.equal(m.get('terms-page').hidden, false);
  assert.equal(m.get('birth-page').hidden, true);
}
function back(m, action, expected) {
  m.get('terms-' + action).click();
  assert.equal(m.get('terms-page').hidden, true);
  assert.equal(m.get('birth-form').hidden, false);
  assert.equal(m.get('birth-editor').hidden, false);
  assert.equal(m.get('terms-acknowledged').checked, badOracle ? !expected : expected);
  assert.equal(m.document.activeElement, m.get('terms-link'));
}
const submit = m => m.get('birth-form').emit('submit');
function agree(m, method) {
  if (method === 'manual') edit(m, 'terms-acknowledged', true);
  else { open(m); back(m, 'agree', true); }
}
async function run() {
  if (scenario === 'roundtrips') {
    // Given подготовлен D1/D2/D3 из примера и записан полный пользовательский ввод
    const cases = [
      ...['00:00','12:00','23:59'].map(time => ['D1-'+time, true, m => edit(m,'birth-time',time), time]),
      ...['','12:00'].map(time => ['D2-'+time, true, m => { edit(m,'birth-time',time); edit(m,'time-unknown',true); }, null]),
      ['D3-empty', false, () => {}, undefined],
      ['D3-partial', true, m => edit(m,'birth-time','12:6'), undefined],
      ['D3-no-id', false, m => edit(m,'birth-place','Моск'), undefined],
      ['D3-edited-A', true, m => { edit(m,'birth-date','2000-02-29'); edit(m,'birth-time','23:59'); }, '23:59'],
      ['D3-cleared-id', true, m => edit(m,'birth-place','Моск'), undefined],
    ];
    for (const [name,saved,setup,birthTime] of cases) for (const action of ['agree','back']) for (const checked of [false,true]) {
      const m = await mount(saved); setup(m); edit(m,'terms-acknowledged',checked);
      const before = values(m), view = m.ui.session.snapshot().view;
      // When пользователь открывает условия и возвращается указанным способом
      open(m); assert.equal(m.get('terms-acknowledged').checked, checked);
      back(m,action,action === 'agree' || checked);
      // Then каждый компонент черновика совпадает с исходным
      assert.deepEqual(values(m),before,name);
      assert.deepEqual(m.ui.session.snapshot().view,view);
      m.get('terms-agree').click(); m.get('terms-back').click();
      assert.equal(m.h.builds().length,0);
      if (birthTime !== undefined) {
        edit(m,'terms-acknowledged',true);
        await submit(m);
        assert.equal(m.h.builds().length,1,'positive build control '+name);
        assert.equal(m.h.builds()[0].body.birth_time,birthTime);
        assert.equal(m.h.builds()[0].body.place_id,'524901');
      }
      examples++; m.ui.dispose();
    }
    const m = await mount(); agree(m,'page'); edit(m,'terms-acknowledged',false); edit(m,'birth-time','23:59');
    const before = values(m); open(m); back(m,'back',false); assert.deepEqual(values(m),before);
    open(m); back(m,'agree',true); assert.deepEqual(values(m),before); m.ui.dispose(); examples++;
  } else if (scenario === 'isolation') {
    for (const saved of [false,true]) for (const action of ['agree','back']) for (const checked of [false,true]) {
      // Given исходные чтения завершены и записаны N и исходное состояние карты
      const m = await mount(saved); edit(m,'terms-acknowledged',checked);
      const before=values(m), view=m.ui.session.snapshot().view;
      // When пользователь открывает условия и повторно активирует один возврат до завершения перехода
      open(m); back(m,action,action==='agree'||checked); m.get('terms-'+action).click();
      // Then нет нового построения и сохранено исходное состояние карты
      assert.deepEqual(values(m),before); assert.deepEqual(m.ui.session.snapshot().view,view);
      assert.equal(m.h.builds().length,0); m.ui.dispose(); examples++;
    }
  } else if (scenario === 'gates') {
    for (const method of ['manual','page']) for (const field of ['','-00:01','24:00','12:6','date','place']) {
      // Given POST не ожидается и checkbox выбран способом из примера
      const m = await mount(); agree(m,method);
      if (field === 'date') edit(m,'birth-date','2025-02-30');
      else if (field === 'place') edit(m,'birth-place','Москва');
      else edit(m,'birth-time',field);
      const before = values(m);
      // When пользователь явно пытается построить карту с невалидным полем
      await submit(m);
      // Then показана ошибка соответствующего поля без отправки запроса
      assert.equal(m.h.builds().length,0);
      assert.ok(m.get((field === 'date' ? 'date' : field === 'place' ? 'place' : 'time')+'-error').textContent);
      assert.deepEqual(values(m),before);
      m.ui.dispose(); examples++;
    }
    for (const valid of [false,true]) {
      const m = await mount(); if (!valid) edit(m,'birth-time','');
      const before = values(m); await submit(m);
      assert.equal(m.h.builds().length,0); assert.ok(m.get('acknowledged-error').textContent);
      assert.deepEqual(values(m),before); m.ui.dispose(); examples++;
    }
    for (const checked of [false,true]) for (const valid of [false,true]) {
      const m = await mount(), pending = deferred(), entered = m.h.entered(buildPath);
      agree(m,'manual'); m.h.queue(buildPath,pending.promise);
      const first = submit(m); await entered;
      edit(m,'terms-acknowledged',checked); if (!valid) edit(m,'birth-time','');
      await submit(m); assert.equal(m.h.builds().length,badOracle ? 2 : 1);
      assert.equal(m.get('birth-form').getAttribute('aria-busy'),'true');
      pending.resolve(response(committed())); await first; m.ui.dispose(); examples++;
    }
  } else if (scenario === 'payload') {
    for (const method of ['manual','page']) for (const time of ['00:00','14:30','23:59',null]) {
      // Given подготовлены валидные поля, нет ожидающего POST и HTTP/recovery допускает build
      const m = await mount(), pending = deferred(), entered = m.h.entered(buildPath);
      edit(m,'birth-date','1990-09-02'); edit(m,'birth-time',time ?? '12:00');
      if (time === null) edit(m,'time-unknown',true);
      agree(m,method); const before = values(m); m.h.queue(buildPath,pending.promise);
      // When пользователь с выбранным checkbox явно строит карту
      const sending = submit(m); await entered;
      // Then отправлен единственный запрос с нормативным payload и показано ожидание
      assert.equal(m.h.builds().length,1);
      assert.deepEqual(m.h.builds()[0].body,{birth_date:'1990-09-02',birth_time:badOracle ? 'WRONG' : time,place_id:'524901'});
      assert.deepEqual(values(m),before); assert.equal(m.get('birth-form').getAttribute('aria-busy'),'true');
      pending.resolve(response(committed())); await sending; m.ui.dispose(); examples++;
    }
  } else if (scenario === 'current') {
    for (const action of ['agree','back']) for (const checked of [false,true]) for (const changed of [false,true]) {
      // Given принята A, открыт изменённый D и разрешённое безопасное чтение удержано барьером
      const m = await mount(), pending = deferred();
      const b = ready(); b.birth.birth_date = '2001-01-01'; if (changed) b.chart.chart_identity += '-B';
      edit(m,'birth-date','1990-09-02'); edit(m,'birth-time','23:59'); edit(m,'terms-acknowledged',checked);
      const before = values(m), entered = m.h.entered(currentPath);
      m.h.queue(currentPath,pending.promise); const reading = m.ui.session.foreground(); await entered;
      // When после перехода условий и возврата завершается automatic current с картой B
      open(m); back(m,action,action === 'agree' || checked); pending.resolve(response(b)); await reading;
      // Then принят ответ current, а пользовательский черновик и состояние отметки от возврата сохранены
      assert.deepEqual(values(m),before); assert.deepEqual(m.ui.session.snapshot().view,b);
      assert.equal(m.get('birth-editor').hidden,false); assert.equal(m.get('terms-acknowledged').checked,action === 'agree' || checked);
      assert.equal(m.h.builds().length,badOracle ? 1 : 0); m.ui.dispose(); examples++;
    }
    for (const method of ['manual','page']) for (const view of [ready(),views.empty,views.known_unavailable]) {
      const m = await mount(), pending = deferred(), entered = m.h.entered(currentPath);
      agree(m,method); edit(m,'birth-date','1990-09-02'); const before = values(m);
      m.h.queue(buildPath,response({status:'already_applied',state_version:3})); m.h.queue(currentPath,pending.promise);
      const building = submit(m); await entered; assert.equal(m.ui.session.snapshot().view.chart?.chart_identity,ready().chart.chart_identity);
      pending.resolve(response(view)); await building;
      assert.equal(m.ui.session.snapshot().view.status,view.status); assert.deepEqual(values(m),before);
      assert.equal(m.h.builds().length,1); m.ui.dispose(); examples++;
    }
  } else if (scenario === 'recovery') {
    for (const method of ['manual','page']) {
      const m=await mount(); agree(m,method); const before=values(m), pending=deferred(), entered=m.h.entered(currentPath);
      m.h.queue(buildPath,new Error('controlled lost response'));m.h.queue(currentPath,pending.promise);
      const sending=submit(m);await entered;
      assert.ok(m.get('session-status').textContent.includes('Не удалось получить ответ о построении карты. Проверяем текущую карту'));
      pending.resolve(response(failure('STATE_READ_FAILED'),503));await sending;
      assert.equal(m.ui.session.snapshot().requiresReconciliation,true);assert.deepEqual(values(m),before);
      await submit(m);assert.equal(m.h.builds().length,1);
      m.h.queue(currentPath,response(views.empty));await m.ui.session.recheck();
      assert.equal(m.h.builds().length,1);assert.equal(m.get('birth-form').querySelector('button[type="submit"]').textContent,'Построить ещё раз');
      assert.ok(m.get('session-status').textContent.includes('Введённые данные сохранены'));
      m.ui.dispose();examples++;
    }
    for (const method of ['manual','page']) for (const code of ['SESSION_REQUIRED','SESSION_EXPIRED','SESSION_NOT_FOUND','RESULT_SUPERSEDED','BUILD_SESSION_RATE_LIMITED','BUILD_CAPACITY_EXHAUSTED','STATE_COMMIT_FAILED','BUILD_TIMEOUT','lost']) {
      // Given выполнен G4, записан D и наличие прежней карты
      const m = await mount(); agree(m,method); edit(m,'birth-date','1990-09-02'); const before = values(m);
      const status = code.startsWith('SESSION_') || code === 'RESULT_SUPERSEDED' ? 409 : code === 'BUILD_SESSION_RATE_LIMITED' ? 429 : code === 'BUILD_TIMEOUT' ? 504 : 503;
      m.h.queue(buildPath,code === 'lost' ? new Error('controlled response loss') : response(failure(code),status,{'Retry-After':'2'}));
      const baseline = m.h.calls.length;
      // When запрос завершается исходом из примера
      await submit(m);
      // Then сохраняются ввод и разрешённое представление и выполняется только предусмотренное recovery
      assert.deepEqual(values(m),before); assert.equal(m.h.builds().length,badOracle ? 2 : 1);
      const after = m.h.calls.slice(baseline).map(c => c.path);
      if (code.startsWith('SESSION_')) assert.deepEqual(after,[buildPath,'/session/bootstrap',currentPath]);
      if (code === 'RESULT_SUPERSEDED') assert.deepEqual(after,[buildPath,currentPath]);
      if (['BUILD_SESSION_RATE_LIMITED','BUILD_CAPACITY_EXHAUSTED'].includes(code)) {
        assert.equal(m.ui.session.snapshot().canSubmit,false); await m.h.clock.advance(1999); assert.equal(m.ui.session.snapshot().canSubmit,false);
        await m.h.clock.advance(1); assert.equal(m.ui.session.snapshot().canSubmit,true); assert.equal(m.h.builds().length,1);
        await submit(m); assert.equal(m.h.builds().length,2);
      }
      if (['STATE_COMMIT_FAILED','BUILD_TIMEOUT'].includes(code)) {
        assert.equal(m.ui.session.snapshot().requiresReconciliation,true); assert.deepEqual(after,[buildPath]);
        await m.h.clock.advance(2000); await m.ui.session.recheck({restartConfirmed:true});
        assert.equal(m.h.builds().length,1);
        assert.ok(m.h.calls.some((c,i) => i >= baseline && c.path === currentPath));
      }
      m.ui.dispose(); examples++;
    }
  } else if (scenario === 'issues') {
    for (const field of ['birth.date','birth.time','birth.place','request.body','request.name','request.future']) for (const code of ['MISSING','INVALID','UNSUPPORTED','AMBIGUOUS']) {
      // Given локальный gate пройден
      const m = await mount(); agree(m,'page'); const before = values(m);
      m.h.queue(buildPath,response(failure('INPUT_REQUIRED',[{field,code}]),422));
      // When сервер отвергает ввод по публичному контракту
      await submit(m);
      // Then UI использует нормативные issues и сохраняет введённые данные
      assert.deepEqual(values(m),before); assert.equal(m.h.builds().length,1);
      const name = {'birth.date':'date','birth.time':'time','birth.place':'place'}[field];
      assert.ok(m.get(name ? name+'-error' : 'form-error').textContent); m.ui.dispose(); examples++;
    }
  } else throw new Error('unknown scenario '+scenario);
}
await run();
console.log(JSON.stringify({scenario,examples,status:'PASS'}));
