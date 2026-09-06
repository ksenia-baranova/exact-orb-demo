# Research Corpus

Диаграммы описывают нормативный поток ADR-0023. P5a (contracts,
whitelist-проекция и InMemory adapter) реализован; P5b (SQLite) и producer
path ещё не реализованы. Application wiring появится отдельной задачей после
P5b.

- `001-record-and-quality.puml` — caller-owned identity/time, whitelist-
  проекция базовой natal/cosmogram-записи и поздние append-only quality events.

Research v1 не записывает `topic=transit`, query/response text и полный
artifact. Отсутствие общего стабильного ID с будущим consented-корпусом не
объявляется невозможностью корреляции по полному вектору и времени.
