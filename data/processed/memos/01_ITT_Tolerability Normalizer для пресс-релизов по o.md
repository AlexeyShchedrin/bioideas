# ITT+Tolerability Normalizer для пресс‑релизов по obesity trials

## Суть (1-2 предложения)
Веб‑сервис для buy-side, BD/CI и biotech‑команд, который нормализует ранние readout’ы по obesity: переводит «as treated» weight loss в консервативные ITT/импутационные сценарии и добавляет структурированное сравнение discontinuations и GI‑tolerability. Выход — 1‑страничный memo и сопоставимые флаги качества раскрытия.

## Проблема
Ранние данные часто публикуются как «as treated» и без внятной safety/tolerability, из‑за чего эффект завышается, а сравнение активов становится некорректным. Это критично сейчас из‑за высокой чувствительности рынка к ранним цифрам и смещения фокуса от «максимального % weight loss» к переносимости.

## Решение
Парсер пресс‑релизов/слайдов извлекает ключевые endpoint’ы и контекст анализа (ITT vs as treated), затем строит 3–5 консервативных сценариев (ITT/импутация с учётом диапазона discontinuations) и формирует «tolerability checklist» + таблицу сравнения активов: что раскрыто/не раскрыто по GI‑побочкам и выбываниям.

## MVP (3-6 месяцев)
- Upload/вставка текста → извлечение: % weight loss, недели, дозы/эскалация, популяция анализа, N, discontinuations (если есть).
- Авто‑детектор «as treated/ITT/не указано» и флаги качества раскрытия.
- Генератор 3–5 сценариев ITT/импутации: пользователь задаёт диапазон discontinuations или «unknown» → sensitivity band.
- Экспорт 1‑pager (HTML/PDF) + сравнение 2–3 активов side‑by‑side.
- Мини‑база кейсов (ручной ввод) для обучения/валидации и публичного каталога readouts.

## Почему сейчас
- В obesity «гонка за %» теряет ценность; важнее переносимость и discontinuations.
- Рынок резко реагирует на ранние readout’ы, создавая спрос на быстрый «честный» нормализованный разбор.
- LLM+правила позволяют извлекать структуру из неструктурных пресс‑релизов без доступа к полным CSR.

## Голубой океан
Это не «ещё один news summary», а слой сопоставимости и качества раскрытия: явное разделение фактов vs допущений + стандартизированный disclosure checklist. Конкурентам сложно быстро занять нишу без (а) библиотеки прецедентов по obesity readouts, (б) доверия к методологии сценариев и (в) комьюнити‑стандарта чеклиста.

## Путь к traction
- Бесплатный wedge: «Press‑release parser» с таблицей «что заявлено/чего не хватает» и предупреждениями про as‑treated и отсутствие tolerability.
- Публичный мини‑каталог readouts с метками ITT/as‑treated, наличия discontinuations и GI‑сводки.
- Распространение через obesity‑инфлюенсеров/аналитиков, Substack/LinkedIn, комьюнити‑чеклист (open-source) и алерты на новые readouts.

## Монетизация
Подписка для buy-side/IR/BD: командные workspace, экспорт в PPT, алерты, сравнение портфеля активов, кастомные шаблоны memo. Платный аддон: «rapid response» разбор readout’а в течение 24 часов.

## Exit thesis
Покупатели через 2–3 года: провайдеры biotech intelligence/данных, research‑платформы, инструменты competitive intelligence для pharma/biotech. Причина: добавляет уникальный слой «comparability + disclosure quality» к новостям/данным и повышает удержание пользователей.

## Риски и митигация
1) **Недостаток структурированных данных** → сценарный анализ по умолчанию, строгая маркировка «unknown», прозрачные допущения.  
2) **Риск “псевдоточности”** → жёсткое разделение: extracted facts vs modeled scenarios; методология/формулы публичны.  
3) **Узкий фокус obesity** → после PMF расширение чеклистов и нормализации на другие TA (NASH, CVOT, CNS) с похожими проблемами раскрытия.

## Доказательства
- Ограничение интерпретации: “**this is really as an as treated result— this is only considering results for people who followed the planned dosing schedule**”; “**there really wasn't any meaningful tolerability data presented**.”
- Искажение из‑за выбываний и важность ITT: “**the discontinuations aren't counted in these results…**”; “**If you were to do a true ITT analysis… that 22% weight loss is very likely to be overstated**.”
- Невозможность сравнения safety/tolerability: “**this was a safety and tolerability study. And we didn't get any safety and tolerability comments**”; “**the comparative analysis… is not possible… because we haven't got enough data**.”
- Сдвиг рынка к переносимости: “**i don't know that chasing raw weight loss improvements… is of huge value**”; “**people are interested… without the nausea and the vomiting and the gi tolerability issues**.”
- Высокая реактивность рынка: “**up about 7.5%… Almost 10% at the Open**.”