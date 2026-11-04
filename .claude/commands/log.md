---
description: Записать в журнал выполненную работу, фактические затраты, ошибку или замечание
argument-hint: "<что произошло>"
---
Запись: $ARGUMENTS

1. Добавь запись в `smart-renovation/project/log/journal.md` (дата, этап, что сделано/обнаружено, ссылки на фото в `inputs/photos/`).
2. Если упомянуты траты — передай `financial-controller` для записи `actual` в budget.json / purchases.json.
3. Если упомянут дефект или отклонение — вызови `quality-controller`: критично ли, нужно ли остановить работы, как исправить; создай задачу на исправление в tasks.json.
4. Если завершена задача — обнови её статус в tasks.json; если это hold point — предложи `/quality`.
5. `python3 smart-renovation/tools/reno.py validate`.
