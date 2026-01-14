# ITT+Tolerability Normalizer для пресс-релизов по obesity trials

## Суть (1-2 предложения)
Веб‑сервис для buy-side/biotech BD/IR, который превращает «as treated» readouts по снижению веса в консервативные ITT/импутационные сценарии и добавляет структурированное сравнение discontinuations и GI‑переносимости. Выход — 1‑страничный memo и сопоставимые флаги качества раскрытия данных по активам.

## Проблема
Ранние obesity readouts часто публикуются как «as treated» и без нормального блока safety/tolerability, из‑за чего эффект завышен, а сравнение активов — некорректно. Сейчас это критично, потому что рынок резко прайсит «сырые цифры» и инвесторы вынуждены вручную пересчитывать, как discontinuations/импутация меняют картину.

## Решение
Парсер пресс‑релизов/слайдов извлекает ключевые endpoint’ы и формат анализа (ITT vs as treated), затем строит 3–5 консервативных сценариев (ITT/импутация) при разных уровнях discontinuations и формирует «tolerability checklist» (что раскрыто/не раскрыто по GI AEs, выбываниям, дозо‑эскалации). Результат — нормализованное сравнение 2–3 активов и предупреждения о рисках интерпретации.

## MVP (3-6 месяцев)
- Вставка текста/загрузка PDF → извлечение: % weight loss, недели, дозы/эскалация, популяция анализа, упоминания discontinuations/GI AEs.  
- Детектор «as treated vs ITT» + флаги неполноты раскрытия.  
- Генератор 3–5 ITT/импутационных сценариев (пользователь задаёт диапазон discontinuations или «unknown» → sensitivity).  
- Шаблон отчёта (HTML/PDF) + сравнение 2–3 активов side‑by‑side.  
- Мини‑база кейсов (ручной ввод) для калибровки и примеров.

## Почему сейчас
- Next‑gen obesity гонка смещается от «макс. % снижения веса» к переносимости (GI) и выбываниям — это нужно быстро сравнивать.  
- Инвесторы сильно реагируют на ранние readouts, а формат «as treated» и отсутствие safety‑комментариев создают систематическую ошибку.  
- LLM+правила позволяют дешево извлекать структуру из неструктурных пресс‑релизов и стандартизировать вывод.

## Голубой океан
Это не «новостной дайджест», а слой нормализации сопоставимости: явное разделение фактов vs сценариев, фокус на ITT‑консерватизме и disclosure‑качества (discontinuations + GI tolerability). Конкурентам сложно быстро повторить без: (а) корпуса размеченных readouts, (б) доверия к методологии сценариев, (в) community‑стандарта disclosure checklist.

## Путь к traction
- Бесплатный wedge: «Press‑release parser» с авто‑таблицей «что заявлено / чего не хватает» и красными флагами (as treated, нет tolerability).  
- Публичный мини‑каталог readouts с метками disclosure‑качества + open‑source checklist.  
- Дистрибуция: biotech Twitter/LinkedIn, рассылка для инвесторов, партнерства с IR‑агентствами/бутик‑ресёрчем, разборы громких readouts в день выхода.

## Монетизация
Подписка для команд: экспорт в PPT, workspace, алерты на новые readouts, кастомные шаблоны memo, сравнение портфеля активов. Платный «rapid readout review» как консалтинг‑аддон.

## Exit thesis
Покупатели через 2–3 года: провайдеры biotech intelligence/данных, ресёрч‑платформы, инструменты competitive intelligence для pharma/biotech — как модуль «readout normalization + disclosure scoring» для obesity и далее других TA.

## Риски и митигация
1) Недостаток данных в публичных материалах → сценарный анализ с явной маркировкой допущений, disclosure‑скоринг вместо «ложной точности».  
2) Риск «псевдоточности» → жёсткое разделение: extracted facts vs modeled scenarios; прозрачные формулы/диапазоны.  
3) Узкий фокус obesity → после product‑market fit расширение на другие TA с похожей проблемой (NASH, oncology safety, etc.).

## Доказательства
- Ограничение интерпретации «as treated» и отсутствие tolerability: “this is really as an as treated result…”, “there really wasn't any meaningful tolerability data presented.”  
- Discontinuations искажают efficacy/tolerability; ITT снизит эффект: “the discontinuations aren't counted…”, “If you were to do a true ITT analysis… that 22% weight loss is very likely to be overstated.”  
- Невозможность comparative analysis без safety данных: “we didn't get any safety and tolerability comments.”, “the comparative analysis… is not possible…”  
- Сдвиг ценности к переносимости: “chasing raw weight loss…”, “without the nausea… gi tolerability issues”  
- Сильная рыночная реакция на ранние данные: “up about 7.5%… Almost 10% at the Open.”