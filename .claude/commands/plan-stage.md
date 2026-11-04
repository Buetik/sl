---
description: Сформировать подробный план этапа (задачи, зависимости, материалы, инструменты, бюджет, контрольные точки). Аналог /plan — встроенная команда /plan в Claude Code занята.
argument-hint: "[номер этапа; если пусто — ближайший доступный]"
---
Этап: $ARGUMENTS

Выполни `smart-renovation/workflows/plan-stage.md`:
1. `python3 smart-renovation/tools/reno.py next` и, для выбранного этапа, `reno.py gate <N>`. Если ворота закрыты — объясни, какие этапы не приняты и почему нельзя начинать; предложи план для доступного этапа. План можно готовить заранее, но статус in_progress — нет.
2. Вызови `project-manager` (план по шаблону `templates/stage-plan.md`), параллельно `innovation-researcher` (технологии под этап) и `tools-expert` (инструменты под этап).
3. Затем профильных инженеров этапа (см. `knowledge/stage-catalog.md`, поле «Ответственный»), `materials-expert` — для невыбранных материалов, `financial-controller` — бюджет этапа, `quality-controller` — чек-лист приёмки в `project/quality-checklists/`.
4. Сохрани план в `smart-renovation/project/stages/stage-XX-<slug>.md`, задачи — в `project/tasks/tasks.json`, статус этапа `planned` (`reno.py set-stage N planned`). Прогони `reno.py validate`.
5. Покажи пользователю краткий план, решения, требующие его подтверждения, и что купить заранее (длинные сроки поставки).
