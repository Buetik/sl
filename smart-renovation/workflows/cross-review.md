# Протокол взаимодействия агентов и перекрёстной проверки

Субагенты Claude Code не вызывают друг друга. Цепочку исполняет **главная сессия**:
передаёт результат агента A следующему агенту B (текстом или путём к файлу-черновику),
собирает заключения и выносит разногласия на согласование пользователю.

## Порядок
1. **Автор** (агент-владелец решения) готовит черновик → файл в `project/specifications/`,
   `knowledge/*.md` (статус ПРЕДЛОЖЕНО) или текст отчёта.
2. **Проверяющие** из матрицы ниже вызываются **параллельно**, если их проверки независимы, и
   **последовательно**, если следующему нужен результат предыдущего (например, финансист считает
   после выбора материалов). Каждый получает: черновик, конкретный вопрос, пути к файлам.
3. Каждый проверяющий пишет заключение по `templates/agent-review.md` в
   `project/reviews/<YYYY-MM-DD>-<тема>-<агент>.md`: СОГЛАСЕН / СОГЛАСЕН С УСЛОВИЯМИ / НЕ СОГЛАСЕН.
4. Есть «НЕ СОГЛАСЕН» → главная сессия формирует таблицу разногласий (`templates/conflict-table.md`),
   при необходимости даёт автору один раунд доработки, затем выносит на решение пользователя.
5. Решения К1 не принимаются без явной фиксации пользователем (`/decision`).
6. Последний в цепочке — `quality-controller`: критерии приёмки и испытания для принятого варианта.

## Матрица (тип решения → цепочка)

| Тип решения | Автор | Проверяют (порядок) | Класс |
|---|---|---|---|
| Перенос/снос стен, новые проёмы | interior-designer | construction-engineer (несущие, нормы) → hvac-engineer (вентиляция, перетоки) → electrical-engineer (трассы) → financial-controller → quality-controller | К1 |
| Скрытый плинтус / теневой шов / скрытые двери | interior-designer | construction-engineer (геометрия, технология) → materials-expert (системы профилей) → hvac-engineer (перетоки для скрытых дверей) → financial-controller → quality-controller | К2 |
| Душ без поддона / трап / лоток | interior-designer | plumbing-engineer (канализация, уклоны, высота сифона) ∥ construction-engineer (пирог пола, гидроизоляция) → electrical-engineer (зоны ванной, уравнивание потенциалов) → materials-expert (трап, гидроизоляция, клей) → financial-controller → quality-controller (залив, пролив) | К1 |
| Расположение света, сценарии, умный дом | electrical-engineer | interior-designer (сценарии, эстетика) ∥ innovation-researcher (автоматизация) → financial-controller → quality-controller | К2 |
| Электрощит, группы, защита | electrical-engineer | hvac-engineer (мощности климата) ∥ plumbing-engineer (мокрые зоны, краны протечек) → financial-controller → quality-controller | К1 |
| Тёплый пол (любой) | hvac-engineer | electrical-engineer (питание, защита) ∥ construction-engineer (пирог, толщина, совместимость с покрытием) → materials-expert (покрытие под тёплый пол) → financial-controller → quality-controller | К1 |
| Вентиляция, кондиционеры | hvac-engineer | construction-engineer (трассы, короба) ∥ electrical-engineer (питание) ∥ interior-designer (размещение) → financial-controller | К1 (вентканалы) / К2 |
| Разводка воды и канализации, инсталляции | plumbing-engineer | construction-engineer (основание, штробы, короба) ∥ interior-designer (габариты) → materials-expert → financial-controller → quality-controller (опрессовка) | К1 |
| Выбор материала | materials-expert | construction-engineer или профильный инженер (совместимость, техкарта) → financial-controller | К2/К3 |
| Технология выравнивания, стяжки, штукатурки | construction-engineer | innovation-researcher (альтернативы) ∥ materials-expert → project-manager (сроки высыхания, последовательность) → financial-controller → quality-controller | К2 |
| Шумоизоляция | construction-engineer | hvac-engineer (инженерный шум) ∥ electrical-engineer (подрозетники в звукоизоляции) → materials-expert → financial-controller | К2 |
| Мебель и хранение, встроенная техника | interior-designer | electrical-engineer (розетки, выводы) ∥ plumbing-engineer (выводы) ∥ hvac-engineer (вентиляция техники) → construction-engineer (крепление) → financial-controller | К2 |
| Изменение последовательности этапов | project-manager | construction-engineer (технология) → quality-controller | К2 |
| Любой пересмотр принятого решения | владелец решения | все, чьи решения затронуты (по `change-decision.md`) | как у исходного |

`∥` — параллельно, `→` — после.

## Как передавать контекст агенту
В prompt агенту всегда: (1) цель проверки, (2) путь к черновику, (3) конкретные вопросы,
(4) напоминание вернуть отчёт в формате раздела 9 `smart-renovation/CLAUDE.md` и сохранить заключение.
