---
description: Проверить качество выполненных работ по фото и замерам, сформировать/применить чек-лист приёмки этапа
argument-hint: "<этап или работа> [описание замеров/фото]"
---
Проверка: $ARGUMENTS

Выполни `smart-renovation/workflows/quality-control.md`:
1. Найди чек-лист этапа в `smart-renovation/project/quality-checklists/`. Если нет — вызови `quality-controller` для его создания по `templates/quality-checklist.md` и выдай пользователю инструкцию, что и как замерить/сфотографировать.
2. Если пользователь прислал фото (в `inputs/photos/` или в сообщении) и замеры — вызови `quality-controller` для оценки по каждому пункту. Для спорных инженерных пунктов — профильный инженер параллельно.
3. Вердикт: ПРИНЯТЬ / ПРИНЯТЬ С ЗАМЕЧАНИЯМИ / НЕ ПРИНИМАТЬ. Дефекты → журнал `project/log/journal.md` и задачи на исправление в `tasks.json`.
4. Только при вердикте ПРИНЯТЬ (с замечаниями, не влияющими на следующие этапы) **и** явном подтверждении пользователя: `python3 smart-renovation/tools/reno.py set-stage N accepted --confirmed-by-user --checklist <путь>`.
