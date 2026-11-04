#!/usr/bin/env python3
"""Smart Renovation AI — утилита состояния проекта и инженерных расчётов.

Только стандартная библиотека Python 3.8+. Запуск из корня репозитория:

    python3 smart-renovation/tools/reno.py status
    python3 smart-renovation/tools/reno.py gate 7
    python3 smart-renovation/tools/reno.py next
    python3 smart-renovation/tools/reno.py budget [--recalc]
    python3 smart-renovation/tools/reno.py validate
    python3 smart-renovation/tools/reno.py set-stage 4 in_progress
    python3 smart-renovation/tools/reno.py set-stage 4 accepted --confirmed-by-user \
        --checklist smart-renovation/project/quality-checklists/stage-04-demolition.md
    python3 smart-renovation/tools/reno.py calc mix --area 20 --thickness-mm 15 --consumption 0.9 --bag-kg 30
    python3 smart-renovation/tools/reno.py calc --help

Переменная окружения RENO_ROOT переопределяет корень данных (по умолчанию —
каталог smart-renovation рядом с этим скриптом). Используется в тестах и примерах.
"""
from __future__ import annotations

import argparse
import datetime as _dt
import json
import math
import os
import re
import sys
from pathlib import Path

STAGE_STATUSES = ("not_started", "planned", "in_progress", "blocked", "review", "accepted", "skipped")
TASK_STATUSES = ("todo", "doing", "blocked", "done", "cancelled")
BUDGET_CATEGORIES = ("materials", "equipment", "tools", "rent", "delivery", "services", "consumables", "contingency")
PURCHASE_STATUSES = ("planned", "ordered", "delivered", "returned", "cancelled")
DONE_STAGE = ("accepted", "skipped")

# Удельное сопротивление при ~20 °C, Ом·мм²/м (справочные значения).
RHO = {"cu": 0.0175, "al": 0.028}


def root() -> Path:
    env = os.environ.get("RENO_ROOT")
    return Path(env) if env else Path(__file__).resolve().parent.parent


def p(*parts: str) -> Path:
    return root().joinpath(*parts)


def load(rel: str) -> dict:
    path = p(rel)
    with path.open(encoding="utf-8") as fh:
        return json.load(fh)


def save(rel: str, data: dict) -> None:
    path = p(rel)
    tmp = path.with_suffix(".tmp")
    with tmp.open("w", encoding="utf-8") as fh:
        json.dump(data, fh, ensure_ascii=False, indent=2)
        fh.write("\n")
    tmp.replace(path)


def money(x) -> str:
    if x is None:
        return "—"
    return f"{x:,.0f}".replace(",", " ")


# --------------------------------------------------------------------------- stages

def stages_by_id(state: dict) -> dict:
    return {s["id"]: s for s in state["stages"]}


def gate_check(state: dict, stage_id: int):
    """Возвращает (ok, список блокирующих этапов)."""
    by_id = stages_by_id(state)
    if stage_id not in by_id:
        raise SystemExit(f"Этап {stage_id} не найден в state.json")
    blockers = [by_id[d] for d in by_id[stage_id].get("depends_on", []) if by_id[d]["status"] not in DONE_STAGE]
    return (not blockers, blockers)


def cmd_gate(args) -> int:
    state = load("project/state.json")
    ok, blockers = gate_check(state, args.stage)
    st = stages_by_id(state)[args.stage]
    if ok:
        print(f"ОТКРЫТО: этап {st['id']} «{st['title']}» можно начинать — все зависимости приняты.")
        return 0
    print(f"ЗАКРЫТО: этап {st['id']} «{st['title']}» нельзя начинать. Не приняты зависимости:")
    for b in blockers:
        print(f"  - {b['id']:>2}. {b['title']} — статус: {b['status']}")
    return 1


def cmd_set_stage(args) -> int:
    state = load("project/state.json")
    by_id = stages_by_id(state)
    if args.stage not in by_id:
        print(f"Этап {args.stage} не найден", file=sys.stderr)
        return 2
    st = by_id[args.stage]
    if args.status in ("in_progress", "review", "accepted"):
        ok, blockers = gate_check(state, args.stage)
        if not ok and not args.force_deviation:
            print("Отказ: зависимости не приняты: " + ", ".join(str(b["id"]) for b in blockers), file=sys.stderr)
            print("Осознанное отступление: --force-deviation \"причина\" (фиксируется в журнале).", file=sys.stderr)
            return 1
    if args.status == "accepted":
        if not args.confirmed_by_user:
            print("Отказ: accepted ставится только с --confirmed-by-user (явное подтверждение пользователя).", file=sys.stderr)
            return 1
        if not args.checklist or not Path(args.checklist).exists():
            print("Отказ: для accepted нужен существующий файл чек-листа приёмки (--checklist).", file=sys.stderr)
            return 1
        st["checklist"] = args.checklist
        st["accepted_at"] = _dt.date.today().isoformat()
    st["status"] = args.status
    if args.note:
        st["notes"] = (st.get("notes", "") + f"\n[{_dt.date.today().isoformat()}] {args.note}").strip()
    if args.force_deviation:
        st["notes"] = (st.get("notes", "") + f"\n[{_dt.date.today().isoformat()}] ОТСТУПЛЕНИЕ ОТ ПОСЛЕДОВАТЕЛЬНОСТИ: {args.force_deviation}").strip()
        _journal(f"ОТСТУПЛЕНИЕ от последовательности для этапа {st['id']}: {args.force_deviation}")
    if args.status in ("in_progress", "planned") and state.get("current_stage") in (None, 0):
        state["current_stage"] = st["id"]
    if args.status == "in_progress":
        state["current_stage"] = st["id"]
    save("project/state.json", state)
    print(f"Этап {st['id']} «{st['title']}» → {args.status}")
    return 0


def _journal(text: str) -> None:
    path = p("project/log/journal.md")
    with path.open("a", encoding="utf-8") as fh:
        fh.write(f"\n- {_dt.datetime.now().strftime('%Y-%m-%d %H:%M')} — {text}\n")


def decisions_summary() -> dict:
    path = p("knowledge/project-decisions.md")
    counts: dict = {}
    if not path.exists():
        return counts
    for m in re.finditer(r"\*\*Статус:\*\*\s*([А-ЯЁA-Z ]+?)\s*(?:\n|$|\|)", path.read_text(encoding="utf-8")):
        key = m.group(1).strip()
        counts[key] = counts.get(key, 0) + 1
    return counts


def cmd_status(args) -> int:
    state = load("project/state.json")
    proj = state.get("project", {})
    print(f"Проект: {proj.get('name', '—')} | Город: {proj.get('city') or '—'} | Обновлено: {_dt.date.today().isoformat()}")
    cur = state.get("current_stage")
    by_id = stages_by_id(state)
    print(f"Текущий этап: {cur}. {by_id[cur]['title']}" if cur in by_id else "Текущий этап: не начат")
    counts: dict = {}
    for s in state["stages"]:
        counts[s["status"]] = counts.get(s["status"], 0) + 1
    print("Этапы: " + ", ".join(f"{k}={v}" for k, v in sorted(counts.items())))
    print()
    for s in state["stages"]:
        mark = {"accepted": "✔", "skipped": "–", "in_progress": "▶", "review": "?", "blocked": "✖", "planned": "○"}.get(s["status"], " ")
        print(f"  [{mark}] {s['id']:>2}. {s['title']:<52} {s['status']}")
    tasks = load("project/tasks/tasks.json").get("tasks", [])
    tc: dict = {}
    for t in tasks:
        tc[t["status"]] = tc.get(t["status"], 0) + 1
    print("\nЗадачи: " + (", ".join(f"{k}={v}" for k, v in sorted(tc.items())) or "нет"))
    dc = decisions_summary()
    print("Решения: " + (", ".join(f"{k}={v}" for k, v in sorted(dc.items())) or "нет"))
    b = budget_summary(load("project/estimates/budget.json"))
    print(f"Бюджет: план {money(b['planned'])} | факт {money(b['actual'])} | прогноз {money(b['forecast'])} "
          f"| лимит пользователя {money(b['user_budget'])} {b['currency']}")
    if b["missing_prices"]:
        print(f"  Позиций без цены: {b['missing_prices']}")
    return 0


def cmd_next(args) -> int:
    state = load("project/state.json")
    ready = []
    for s in state["stages"]:
        if s["status"] in DONE_STAGE:
            continue
        ok, _ = gate_check(state, s["id"])
        if ok:
            ready.append(s)
    print("Этапы, доступные к работе (зависимости приняты):")
    for s in ready:
        print(f"  {s['id']:>2}. {s['title']} — {s['status']}")
    if not ready:
        print("  нет")
    tasks = load("project/tasks/tasks.json").get("tasks", [])
    done = {t["id"] for t in tasks if t["status"] == "done"}
    ready_ids = {s["id"] for s in ready}
    actionable = [t for t in tasks if t["status"] in ("todo", "doing")
                  and all(d in done for d in t.get("depends_on", []))
                  and t.get("stage") in ready_ids]
    print("\nЗадачи, которые можно выполнять сейчас:")
    for t in actionable:
        hp = " [HOLD POINT — приёмка]" if t.get("hold_point") else ""
        print(f"  {t['id']}: {t['title']} (этап {t.get('stage')}, {t.get('who', 'self')}, ~{t.get('est_hours', '?')} ч){hp}")
    if not actionable:
        print("  нет — сформируйте задачи через /plan-stage")
    blocked = [t for t in tasks if t["status"] == "blocked"]
    if blocked:
        print("\nЗаблокировано:")
        for t in blocked:
            print(f"  {t['id']}: {t['title']} — {t.get('blocked_reason', 'причина не указана')}")
    return 0


# --------------------------------------------------------------------------- budget

def budget_summary(budget: dict) -> dict:
    items = budget.get("items", [])
    by_cat: dict = {}
    by_stage: dict = {}
    planned = actual = forecast = 0.0
    missing = 0
    for it in items:
        pl = it.get("planned")
        if pl is None and it.get("qty") is not None and it.get("unit_price") is not None:
            pl = it["qty"] * it["unit_price"]
        ac = it.get("actual")
        if pl is None and ac is None:
            missing += 1
        pl = pl or 0.0
        planned += pl
        if ac is not None:
            actual += ac
        fc = ac if (ac is not None and it.get("status") in ("paid", "closed")) else max(pl, ac or 0.0)
        forecast += fc
        for key, bucket in ((it.get("category", "?"), by_cat), (it.get("stage", "—"), by_stage)):
            b = bucket.setdefault(key, {"planned": 0.0, "actual": 0.0})
            b["planned"] += pl
            b["actual"] += ac or 0.0
    pct = budget.get("contingency_pct") or 0
    has_explicit = any(it.get("category") == "contingency" for it in items)
    reserve = 0.0 if has_explicit else round((planned) * pct / 100.0, 2)
    return {
        "currency": budget.get("currency", "RUB"),
        "user_budget": budget.get("user_budget"),
        "planned": planned + reserve,
        "planned_without_reserve": planned,
        "reserve": reserve,
        "actual": actual,
        "forecast": forecast + reserve,
        "by_category": by_cat,
        "by_stage": by_stage,
        "missing_prices": missing,
    }


def cmd_budget(args) -> int:
    budget = load("project/estimates/budget.json")
    if args.recalc:
        n = 0
        for it in budget.get("items", []):
            if it.get("qty") is not None and it.get("unit_price") is not None:
                it["planned"] = round(it["qty"] * it["unit_price"], 2)
                n += 1
        save("project/estimates/budget.json", budget)
        print(f"Пересчитано позиций: {n}")
    s = budget_summary(budget)
    cur = s["currency"]
    print(f"Смета ({cur})")
    print(f"  План без резерва: {money(s['planned_without_reserve'])}")
    print(f"  Резерв ({budget.get('contingency_pct', 0)} %): {money(s['reserve'])}")
    print(f"  План итого: {money(s['planned'])}")
    print(f"  Факт: {money(s['actual'])}")
    print(f"  Прогноз: {money(s['forecast'])}")
    if s["user_budget"]:
        delta = s["user_budget"] - s["forecast"]
        print(f"  Лимит пользователя: {money(s['user_budget'])} → {'запас' if delta >= 0 else 'ПЕРЕРАСХОД'} {money(abs(delta))}")
    print("\nПо категориям:")
    for k, v in sorted(s["by_category"].items()):
        print(f"  {k:<12} план {money(v['planned']):>12} | факт {money(v['actual']):>12}")
    print("\nПо этапам:")
    for k, v in sorted(s["by_stage"].items(), key=lambda kv: (str(type(kv[0])), kv[0])):
        print(f"  {str(k):<4} план {money(v['planned']):>12} | факт {money(v['actual']):>12}")
    if s["missing_prices"]:
        print(f"\nВнимание: позиций без цены — {s['missing_prices']} (нужна цена с источником).")
    return 0


# --------------------------------------------------------------------------- validate

def validate() -> list:
    errors = []
    try:
        state = load("project/state.json")
    except Exception as e:  # noqa: BLE001
        return [f"state.json: {e}"]
    ids = [s.get("id") for s in state.get("stages", [])]
    if len(ids) != len(set(ids)):
        errors.append("state.json: повторяющиеся id этапов")
    idset = set(ids)
    for s in state.get("stages", []):
        for f in ("id", "slug", "title", "depends_on", "status"):
            if f not in s:
                errors.append(f"state.json: этап {s.get('id')} без поля {f}")
        if s.get("status") not in STAGE_STATUSES:
            errors.append(f"state.json: этап {s.get('id')} неизвестный статус {s.get('status')}")
        for d in s.get("depends_on", []):
            if d not in idset:
                errors.append(f"state.json: этап {s.get('id')} зависит от несуществующего {d}")
        if s.get("status") == "accepted" and not s.get("checklist"):
            errors.append(f"state.json: этап {s.get('id')} accepted без чек-листа")
    # циклы
    graph = {s["id"]: s.get("depends_on", []) for s in state.get("stages", []) if "id" in s}
    color: dict = {}

    def dfs(n):
        color[n] = 1
        for m in graph.get(n, []):
            if color.get(m) == 1:
                errors.append(f"state.json: цикл зависимостей через этап {m}")
            elif color.get(m) is None and m in graph:
                dfs(m)
        color[n] = 2

    for n in graph:
        if color.get(n) is None:
            dfs(n)
    try:
        tasks = load("project/tasks/tasks.json").get("tasks", [])
        tids = {t.get("id") for t in tasks}
        for t in tasks:
            if t.get("status") not in TASK_STATUSES:
                errors.append(f"tasks.json: {t.get('id')} неизвестный статус {t.get('status')}")
            if t.get("stage") not in idset:
                errors.append(f"tasks.json: {t.get('id')} ссылается на несуществующий этап {t.get('stage')}")
            for d in t.get("depends_on", []):
                if d not in tids:
                    errors.append(f"tasks.json: {t.get('id')} зависит от несуществующей задачи {d}")
    except Exception as e:  # noqa: BLE001
        errors.append(f"tasks.json: {e}")
    try:
        budget = load("project/estimates/budget.json")
        for it in budget.get("items", []):
            if it.get("category") not in BUDGET_CATEGORIES:
                errors.append(f"budget.json: {it.get('id')} неизвестная категория {it.get('category')}")
            if it.get("unit_price") is not None and not it.get("source"):
                errors.append(f"budget.json: {it.get('id')} цена без источника")
    except Exception as e:  # noqa: BLE001
        errors.append(f"budget.json: {e}")
    try:
        for it in load("project/purchases/purchases.json").get("items", []):
            if it.get("status") not in PURCHASE_STATUSES:
                errors.append(f"purchases.json: {it.get('id')} неизвестный статус {it.get('status')}")
    except Exception as e:  # noqa: BLE001
        errors.append(f"purchases.json: {e}")
    return errors


def cmd_validate(args) -> int:
    errs = validate()
    if errs:
        print("Ошибки данных проекта:")
        for e in errs:
            print("  - " + e)
        return 1
    print("Данные проекта корректны.")
    return 0


# --------------------------------------------------------------------------- calculators

def calc_mix(area, thickness_mm, consumption, bag_kg, waste_pct=10.0):
    """Сухая смесь: расход кг/м²/мм из техкарты."""
    kg = area * thickness_mm * consumption * (1 + waste_pct / 100.0)
    return {"kg": round(kg, 1), "bags": math.ceil(kg / bag_kg) if bag_kg else None}


def calc_tile(area, tile_w_mm, tile_h_mm, waste_pct=10.0, per_box_m2=None):
    tile_m2 = tile_w_mm * tile_h_mm / 1_000_000.0
    need_m2 = area * (1 + waste_pct / 100.0)
    pcs = math.ceil(need_m2 / tile_m2)
    res = {"m2_with_waste": round(need_m2, 2), "pieces": pcs}
    if per_box_m2:
        res["boxes"] = math.ceil(need_m2 / per_box_m2)
        res["m2_purchased"] = round(res["boxes"] * per_box_m2, 2)
    return res


def calc_paint(area, coats, consumption_l_m2, can_l, waste_pct=10.0):
    litres = area * coats * consumption_l_m2 * (1 + waste_pct / 100.0)
    return {"litres": round(litres, 2), "cans": math.ceil(litres / can_l) if can_l else None}


def calc_linear(length_m, piece_m, waste_pct=10.0):
    need = length_m * (1 + waste_pct / 100.0)
    return {"m_with_waste": round(need, 2), "pieces": math.ceil(need / piece_m)}


def calc_sheet(area, sheet_w_mm, sheet_h_mm, waste_pct=10.0, layers=1):
    sheet_m2 = sheet_w_mm * sheet_h_mm / 1_000_000.0
    need = area * layers * (1 + waste_pct / 100.0)
    return {"m2_with_waste": round(need, 2), "sheets": math.ceil(need / sheet_m2)}


def calc_slope(length_m, slope_pct=None, drop_mm=None):
    if slope_pct is not None:
        return {"drop_mm": round(length_m * 1000 * slope_pct / 100.0, 1), "slope_pct": slope_pct}
    if drop_mm is not None:
        return {"slope_pct": round(drop_mm / (length_m * 1000) * 100.0, 2), "drop_mm": drop_mm}
    raise ValueError("нужен slope_pct или drop_mm")


def calc_voltage_drop(length_m, current_a, section_mm2, voltage=230.0, material="cu", cos_phi=1.0):
    """Однофазная линия: ΔU = 2·L·I·ρ·cosφ / S (активная составляющая, без учёта нагрева)."""
    du = 2 * length_m * current_a * RHO[material] * cos_phi / section_mm2
    return {"drop_v": round(du, 2), "drop_pct": round(du / voltage * 100.0, 2)}


def calc_unit_price(price, qty_per_pack):
    return {"price_per_unit": round(price / qty_per_pack, 2)}


def parse_dims(s: str):
    m = re.fullmatch(r"\s*([\d.,]+)\s*[xх×*]\s*([\d.,]+)\s*", s)
    if not m:
        raise argparse.ArgumentTypeError(f"ожидается ШxВ, получено {s!r}")
    return float(m.group(1).replace(",", ".")), float(m.group(2).replace(",", "."))


def calc_room(length, width, height, openings=()):
    floor = length * width
    perimeter = 2 * (length + width)
    walls_gross = perimeter * height
    op_area = sum(w * h for w, h in openings)
    return {"floor_m2": round(floor, 2), "ceiling_m2": round(floor, 2), "perimeter_m": round(perimeter, 2),
            "walls_gross_m2": round(walls_gross, 2), "openings_m2": round(op_area, 2),
            "walls_net_m2": round(walls_gross - op_area, 2), "volume_m3": round(floor * height, 2)}


def cmd_calc(args) -> int:
    k = args.kind
    if k == "mix":
        r = calc_mix(args.area, args.thickness_mm, args.consumption, args.bag_kg, args.waste_pct)
    elif k == "tile":
        w, h = parse_dims(args.tile)
        r = calc_tile(args.area, w, h, args.waste_pct, args.per_box_m2)
    elif k == "paint":
        r = calc_paint(args.area, args.coats, args.consumption, args.can_l, args.waste_pct)
    elif k == "linear":
        r = calc_linear(args.length, args.piece_m, args.waste_pct)
    elif k == "sheet":
        w, h = parse_dims(args.sheet)
        r = calc_sheet(args.area, w, h, args.waste_pct, args.layers)
    elif k == "slope":
        r = calc_slope(args.length, args.slope_pct, args.drop_mm)
    elif k == "voltage-drop":
        r = calc_voltage_drop(args.length, args.current, args.section, args.voltage, args.material, args.cos_phi)
    elif k == "unit-price":
        r = calc_unit_price(args.price, args.qty_per_pack)
    elif k == "room":
        ops = [parse_dims(o) for o in args.openings.split(",")] if args.openings else []
        r = calc_room(args.length, args.width, args.height, ops)
    else:  # pragma: no cover
        raise SystemExit("неизвестный расчёт")
    print(json.dumps({"calc": k, "input": {kk: vv for kk, vv in vars(args).items() if kk not in ("func", "kind")},
                      "result": r}, ensure_ascii=False, indent=2))
    return 0


# --------------------------------------------------------------------------- CLI

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(prog="reno.py", description="Smart Renovation AI — состояние проекта и расчёты")
    sub = ap.add_subparsers(dest="cmd", required=True)

    sub.add_parser("status", help="общий статус").set_defaults(func=cmd_status)
    sub.add_parser("next", help="что можно делать сейчас").set_defaults(func=cmd_next)
    sub.add_parser("validate", help="проверка данных проекта").set_defaults(func=cmd_validate)

    g = sub.add_parser("gate", help="проверка ворот этапа")
    g.add_argument("stage", type=int)
    g.set_defaults(func=cmd_gate)

    b = sub.add_parser("budget", help="сводка сметы")
    b.add_argument("--recalc", action="store_true", help="пересчитать planned = qty × unit_price")
    b.set_defaults(func=cmd_budget)

    s = sub.add_parser("set-stage", help="изменить статус этапа")
    s.add_argument("stage", type=int)
    s.add_argument("status", choices=STAGE_STATUSES)
    s.add_argument("--note")
    s.add_argument("--checklist")
    s.add_argument("--confirmed-by-user", action="store_true")
    s.add_argument("--force-deviation", metavar="ПРИЧИНА")
    s.set_defaults(func=cmd_set_stage)

    c = sub.add_parser("calc", help="инженерные расчёты")
    cs = c.add_subparsers(dest="kind", required=True)
    m = cs.add_parser("mix", help="сухие смеси по толщине слоя")
    m.add_argument("--area", type=float, required=True, help="м²")
    m.add_argument("--thickness-mm", type=float, required=True)
    m.add_argument("--consumption", type=float, required=True, help="кг/м² на 1 мм (из техкарты)")
    m.add_argument("--bag-kg", type=float, required=True)
    m.add_argument("--waste-pct", type=float, default=10.0)
    t = cs.add_parser("tile", help="плитка/керамогранит/ламинат по площади")
    t.add_argument("--area", type=float, required=True)
    t.add_argument("--tile", required=True, help="мм, напр. 600x600")
    t.add_argument("--waste-pct", type=float, default=10.0)
    t.add_argument("--per-box-m2", type=float)
    pa = cs.add_parser("paint", help="краска/грунт")
    pa.add_argument("--area", type=float, required=True)
    pa.add_argument("--coats", type=int, default=2)
    pa.add_argument("--consumption", type=float, required=True, help="л/м² на слой (из техкарты)")
    pa.add_argument("--can-l", type=float, required=True)
    pa.add_argument("--waste-pct", type=float, default=10.0)
    li = cs.add_parser("linear", help="погонажные изделия (плинтус, профиль, кабель)")
    li.add_argument("--length", type=float, required=True, help="м")
    li.add_argument("--piece-m", type=float, required=True)
    li.add_argument("--waste-pct", type=float, default=10.0)
    sh = cs.add_parser("sheet", help="листовые материалы (ГКЛ, ГВЛ, панели)")
    sh.add_argument("--area", type=float, required=True)
    sh.add_argument("--sheet", required=True, help="мм, напр. 1200x2500")
    sh.add_argument("--layers", type=int, default=1)
    sh.add_argument("--waste-pct", type=float, default=10.0)
    sl = cs.add_parser("slope", help="уклон: перепад по длине или уклон по перепаду")
    sl.add_argument("--length", type=float, required=True, help="м")
    g2 = sl.add_mutually_exclusive_group(required=True)
    g2.add_argument("--slope-pct", type=float)
    g2.add_argument("--drop-mm", type=float)
    vd = cs.add_parser("voltage-drop", help="падение напряжения, однофазная линия")
    vd.add_argument("--length", type=float, required=True, help="длина трассы в одну сторону, м")
    vd.add_argument("--current", type=float, required=True, help="А")
    vd.add_argument("--section", type=float, required=True, help="мм²")
    vd.add_argument("--voltage", type=float, default=230.0)
    vd.add_argument("--material", choices=sorted(RHO), default="cu")
    vd.add_argument("--cos-phi", type=float, default=1.0)
    up = cs.add_parser("unit-price", help="цена за единицу (м², кг, м)")
    up.add_argument("--price", type=float, required=True)
    up.add_argument("--qty-per-pack", type=float, required=True)
    ro = cs.add_parser("room", help="площади помещения")
    ro.add_argument("--length", type=float, required=True)
    ro.add_argument("--width", type=float, required=True)
    ro.add_argument("--height", type=float, required=True)
    ro.add_argument("--openings", help="проёмы в метрах через запятую, напр. 0.9x2.05,1.5x1.4")
    c.set_defaults(func=cmd_calc)
    return ap


def main(argv=None) -> int:
    args = build_parser().parse_args(argv)
    try:
        return args.func(args)
    except (argparse.ArgumentTypeError, ValueError) as e:
        print(f"Ошибка: {e}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
