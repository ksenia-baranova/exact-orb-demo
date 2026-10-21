# docs: зарегистрировать принятые долги ui-chart-wheel

Тип передачи: готовый документальный пакет для отдельного PR в main; публикация
и merge ещё не выполнялись. Base — актуальный `origin/main`; проверенный
MainBaseline `bba8d6cfb22f586f86c3035423f2535ede158b9f`.

Изменяется только `docs/project_management/technical_debt.md`:

- DEBT-UI-002: UX ввода года, Owner отложил исправление; P3, Developer UI,
  возврат при следующем изменении ввода/валидации даты.
- DEBT-UI-003: увеличение символов, Owner отложил; P3, Developer UI,
  возврат при следующем изменении читаемости/размера SVG и перед публичным выпуском.
- DEBT-UI-004: независимый oracle плотности/точности, P2; связан с UI-003,
  возвращается при изменении SVG-раскладки или подготовке публичного выпуска.

Все три остаются OPEN. TEST-FIND-WHEEL-002 не исправлен; precision INDETERMINATE,
TEST-FIND-WHEEL-004 CLOSED. Новые entries относятся к source change до поставки,
а не объявляются дефектами текущей main-реализации.

Патч [registry-publication.patch](registry-publication.patch) получен из текущего
единого реестра относительно проверенного main. Источники новых entries ведут
на опубликованный Git snapshot: они читаются до merge реализации. Ранее
существовавшие записи main сохраняются байт-в-байт. Перед применением обновить
main, повторно проверить IDs и использовать `git apply --check --unidiff-zero`; затем
`git apply --unidiff-zero` (патч без context-строк, база закреплена SHA). При движении
main заново собрать патч из единого реестра без перезаписи чужих entries.

Проверки и SHA-256 кандидата — [session checks](session_closure_checks.json).
Runtime suites/browser не требуются для изменения реестра. После разрешённого
merge этого PR записать URL и точный registry SHA в Manager §2.30 и связанные
handoffs, синхронизировать реестр в change до итоговой интеграции.
