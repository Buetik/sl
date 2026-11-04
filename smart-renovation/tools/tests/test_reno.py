"""Тесты Smart Renovation AI: расчёты, ворота этапов, валидация данных, целостность системы.

Запуск из корня репозитория:
    python3 -m unittest discover -s smart-renovation/tools/tests -v
"""
import io
import json
import os
import re
import shutil
import sys
import tempfile
import unittest
from contextlib import redirect_stdout, redirect_stderr
from pathlib import Path

HERE = Path(__file__).resolve()
SR = HERE.parents[2]            # smart-renovation/
REPO = SR.parent                # корень репозитория
sys.path.insert(0, str(SR / "tools"))
import reno  # noqa: E402

AGENTS = ["project-manager", "interior-designer", "construction-engineer", "electrical-engineer",
          "plumbing-engineer", "hvac-engineer", "materials-expert", "tools-expert",
          "innovation-researcher", "quality-controller", "financial-controller"]
COMMANDS = ["renovation-start", "apartment-analysis", "design", "plan-stage", "materials", "compare",
            "innovation", "instruction", "estimate", "tools", "quality", "next", "project-status",
            "decision", "risks", "audit", "log"]


def run(*argv):
    out, err = io.StringIO(), io.StringIO()
    with redirect_stdout(out), redirect_stderr(err):
        code = reno.main(list(argv))
    return code, out.getvalue() + err.getvalue()


class Sandbox(unittest.TestCase):
    """Копия данных проекта во временный каталог (RENO_ROOT)."""

    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        for sub in ("project", "knowledge"):
            shutil.copytree(SR / sub, self.tmp / sub)
        os.environ["RENO_ROOT"] = str(self.tmp)

    def tearDown(self):
        os.environ.pop("RENO_ROOT", None)
        shutil.rmtree(self.tmp)

    def state(self):
        return json.loads((self.tmp / "project/state.json").read_text(encoding="utf-8"))

    def write(self, rel, data):
        (self.tmp / rel).write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")


class TestCalculators(unittest.TestCase):
    def test_mix_plaster(self):
        # 20 м² × 15 мм × 0,9 кг/м²/мм × 1,1 = 297 кг → 10 мешков по 30 кг
        r = reno.calc_mix(20, 15, 0.9, 30, 10)
        self.assertEqual(r, {"kg": 297.0, "bags": 10})

    def test_tile_with_boxes(self):
        r = reno.calc_tile(10, 600, 600, 10, per_box_m2=1.44)
        self.assertEqual(r["pieces"], 31)          # 11 / 0.36 = 30.56 → 31
        self.assertEqual(r["boxes"], 8)            # 11 / 1.44 = 7.64 → 8
        self.assertAlmostEqual(r["m2_purchased"], 11.52)

    def test_paint(self):
        r = reno.calc_paint(50, 2, 0.12, 9, 10)    # 13.2 л → 2 банки
        self.assertEqual(r, {"litres": 13.2, "cans": 2})

    def test_sheet_two_layers(self):
        r = reno.calc_sheet(12, 1200, 2500, 10, layers=2)  # 26.4 / 3 = 8.8 → 9
        self.assertEqual(r["sheets"], 9)

    def test_linear(self):
        self.assertEqual(reno.calc_linear(14.6, 2.5, 10)["pieces"], 7)

    def test_slope_shower(self):
        # Душ без поддона: 1,2 м до дальней точки при 2 % → 24 мм перепада
        self.assertEqual(reno.calc_slope(1.2, slope_pct=2)["drop_mm"], 24.0)
        self.assertEqual(reno.calc_slope(3, drop_mm=60)["slope_pct"], 2.0)

    def test_voltage_drop(self):
        # 25 м, 16 А, 2,5 мм² Cu: 2·25·16·0,0175/2,5 = 5,6 В ≈ 2,43 %
        r = reno.calc_voltage_drop(25, 16, 2.5)
        self.assertEqual(r, {"drop_v": 5.6, "drop_pct": 2.43})

    def test_room(self):
        r = reno.calc_room(4.0, 3.0, 2.7, [(0.9, 2.05), (1.5, 1.4)])
        self.assertEqual(r["floor_m2"], 12.0)
        self.assertEqual(r["walls_gross_m2"], 37.8)
        self.assertEqual(r["walls_net_m2"], 33.86)

    def test_expr_safe(self):
        self.assertEqual(reno.calc_expr("2*25*16*0.0175/2.5")["value"], 5.6)
        self.assertEqual(reno.calc_expr("ceil(10.2)")["value"], 11)
        # акустика: закон массы и сложение уровней
        self.assertEqual(reno.calc_expr("lg(1000)")["value"], 3.0)
        self.assertAlmostEqual(reno.calc_expr("10*lg(10**(40/10)+10**(40/10))")["value"], 43.0103, places=3)
        for bad in ("__import__('os')", "open('x')", "a+1", "(1).__class__", "2**1000"):
            with self.assertRaises(ValueError):
                reno.calc_expr(bad)

    def test_shower_floor_scenario(self):
        """Сценарий из теста сантехника: вход стояка 60 мм, трасса 1,6 м при 2 %, трап 80 мм,
        выпуск на 40 мм от основания, уклон душа 0,75 м × 2 %, коридор 40 мм."""
        r = reno.calc_shower_floor(60, 1.6, 2, 40, 80, 0.75, 2, 40)
        self.assertEqual(r["pipe_drop_mm"], 32.0)
        self.assertEqual(r["drain_outlet_min_mm"], 92.0)
        self.assertEqual(r["drain_base_mm"], 52.0)
        self.assertEqual(r["grate_level_mm"], 132.0)
        self.assertEqual(r["shower_edge_level_mm"], 147.0)
        self.assertEqual(r["threshold_mm"], 107.0)
        # высокий вход стояка не нужен — подставка 0
        self.assertEqual(reno.calc_shower_floor(0, 0.6, 3, 40, 80, 0.75, 2)["drain_base_mm"], 0.0)

    def test_power(self):
        r = reno.calc_power([("варочная", 7000), ("духовка", 3500)], 0.7)
        self.assertEqual(r["installed_kw"], 10.5)
        self.assertEqual(r["design_kw"], 7.35)
        self.assertEqual(r["design_current_a"], 31.96)

    def test_cli_calc_outputs_json(self):
        code, out = run("calc", "tile", "--area", "5", "--tile", "300x600")
        self.assertEqual(code, 0)
        self.assertEqual(json.loads(out)["result"]["pieces"], 31)

    def test_bad_dims(self):
        code, out = run("calc", "tile", "--area", "5", "--tile", "abc")
        self.assertEqual(code, 2)
        self.assertIn("ШxВ", out)


class TestStageGates(Sandbox):
    def test_initial_project_valid(self):
        self.assertEqual(reno.validate(), [])
        code, out = run("gate", "1")
        self.assertEqual(code, 0)

    def test_gate_closed_until_dependencies_accepted(self):
        code, out = run("gate", "4")
        self.assertEqual(code, 1)
        self.assertIn("ЗАКРЫТО", out)

    def test_cannot_start_stage_out_of_order(self):
        code, out = run("set-stage", "12", "in_progress")
        self.assertEqual(code, 1)
        self.assertIn("зависимости не приняты", out)

    def test_accept_requires_user_and_checklist(self):
        code, out = run("set-stage", "1", "accepted")
        self.assertEqual(code, 1)
        code, out = run("set-stage", "1", "accepted", "--confirmed-by-user")
        self.assertEqual(code, 1)
        chk = self.tmp / "chk.md"
        chk.write_text("ok", encoding="utf-8")
        code, out = run("set-stage", "1", "accepted", "--confirmed-by-user", "--checklist", str(chk))
        self.assertEqual(code, 0)
        self.assertEqual(self.state()["stages"][0]["status"], "accepted")
        self.assertEqual(run("gate", "2")[0], 0)

    def test_forced_deviation_is_journaled(self):
        code, _ = run("set-stage", "12", "in_progress", "--force-deviation", "тест")
        self.assertEqual(code, 0)
        self.assertIn("ОТСТУПЛЕНИЕ", (self.tmp / "project/log/journal.md").read_text(encoding="utf-8"))

    def test_full_happy_path_scenario(self):
        """Сценарий: проходим все 24 этапа в порядке зависимостей — ворота открываются последовательно."""
        chk = self.tmp / "chk.md"
        chk.write_text("ok", encoding="utf-8")
        st = self.state()
        remaining = {s["id"] for s in st["stages"]}
        order = []
        while remaining:
            ready = [i for i in sorted(remaining) if run("gate", str(i))[0] == 0]
            self.assertTrue(ready, f"тупик зависимостей: {remaining}")
            i = ready[0]
            self.assertEqual(run("set-stage", str(i), "accepted", "--confirmed-by-user", "--checklist", str(chk))[0], 0)
            remaining.discard(i)
            order.append(i)
        self.assertEqual(order[0], 1)
        self.assertEqual(order[-1], 24)
        self.assertLess(order.index(12), order.index(11))   # штукатурка до стяжки
        self.assertLess(order.index(13), order.index(15))   # гидроизоляция до плитки

    def test_validate_detects_cycle_and_bad_refs(self):
        st = self.state()
        st["stages"][0]["depends_on"] = [24]
        st["stages"][1]["depends_on"] = [1, 99]
        self.write("project/state.json", st)
        errs = reno.validate()
        self.assertTrue(any("цикл" in e for e in errs))
        self.assertTrue(any("99" in e for e in errs))

    def test_next_lists_tasks(self):
        code, out = run("next")
        self.assertEqual(code, 0)
        self.assertIn("T-001", out)
        self.assertNotIn("T-003", out)  # зависит от T-001


class TestBudget(Sandbox):
    def test_budget_scenario(self):
        """Сценарий: смета санузла, лимит превышен, позиция без цены, факт по оплаченной позиции."""
        self.write("project/estimates/budget.json", {
            "currency": "RUB", "user_budget": 100000, "contingency_pct": 15, "items": [
                {"id": "B1", "stage": 15, "category": "materials", "item": "Керамогранит", "qty": 12, "unit": "м2",
                 "unit_price": 3000, "planned": None, "actual": None, "source": "магазин, 2026-11-04", "status": "planned"},
                {"id": "B2", "stage": 13, "category": "materials", "item": "Гидроизоляция", "qty": 1, "unit": "компл",
                 "unit_price": 9000, "planned": None, "actual": 9500, "source": "магазин, 2026-11-04", "status": "paid"},
                {"id": "B3", "stage": 8, "category": "equipment", "item": "Трап", "qty": 1, "unit": "шт",
                 "unit_price": None, "planned": None, "actual": None, "source": None, "status": "planned"},
                {"id": "B4", "stage": 7, "category": "services", "item": "Электрик: измерения", "qty": 1, "unit": "усл",
                 "unit_price": 60000, "planned": None, "actual": None, "source": "прайс, 2026-11-04", "status": "planned"},
            ]})
        s = reno.budget_summary(reno.load("project/estimates/budget.json"))
        self.assertEqual(s["planned_without_reserve"], 105000)
        self.assertEqual(s["reserve"], 15750)
        self.assertEqual(s["actual"], 9500)
        self.assertEqual(s["missing_prices"], 1)
        self.assertEqual(s["forecast"], 36000 + 9500 + 60000 + 15750)
        code, out = run("budget", "--recalc")
        self.assertEqual(code, 0)
        self.assertIn("ПЕРЕРАСХОД", out)
        self.assertEqual(reno.validate(), [])

    def test_price_without_source_is_error(self):
        self.write("project/estimates/budget.json", {"currency": "RUB", "items": [
            {"id": "X", "category": "materials", "unit_price": 10, "qty": 1, "source": None}]})
        self.assertTrue(any("без источника" in e for e in reno.validate()))


class TestSystemIntegrity(unittest.TestCase):
    """Структура мультиагентной системы: агенты, команды, ссылки на файлы."""

    def frontmatter(self, path):
        text = path.read_text(encoding="utf-8")
        m = re.match(r"^---\n(.*?)\n---\n", text, re.S)
        self.assertIsNotNone(m, f"нет frontmatter в {path}")
        return dict(line.split(":", 1) for line in m.group(1).splitlines() if ":" in line), text

    def test_agents_exist_and_have_frontmatter(self):
        for a in AGENTS:
            fm, body = self.frontmatter(REPO / ".claude/agents" / f"{a}.md")
            self.assertEqual(fm["name"].strip(), a)
            self.assertTrue(fm["description"].strip())
            self.assertIn("smart-renovation/CLAUDE.md", body)

    def test_commands_exist(self):
        for c in COMMANDS:
            fm, body = self.frontmatter(REPO / ".claude/commands" / f"{c}.md")
            self.assertTrue(fm["description"].strip())

    def test_referenced_agents_exist(self):
        known = set(AGENTS)
        files = list((REPO / ".claude/commands").glob("*.md")) + list((SR / "workflows").glob("*.md"))
        for f in files:
            for name in re.findall(r"`([a-z]+-[a-z]+(?:-[a-z]+)?)`", f.read_text(encoding="utf-8")):
                if name.endswith(("-engineer", "-expert", "-designer", "-manager", "-controller", "-researcher")):
                    self.assertIn(name, known, f"{f.name}: неизвестный агент {name}")

    def test_referenced_paths_exist(self):
        files = list((REPO / ".claude").rglob("*.md")) + list(SR.rglob("*.md"))
        pat = re.compile(r"(?:smart-renovation/)?((?:knowledge|templates|workflows|tools|inputs)/[\w./-]+\.(?:md|py|json))")
        for f in files:
            for rel in pat.findall(f.read_text(encoding="utf-8")):
                if "<" in rel or "XX" in rel or "YYYY" in rel:
                    continue
                self.assertTrue((SR / rel).exists(), f"{f.relative_to(REPO)} ссылается на отсутствующий {rel}")

    def test_work_instruction_template_has_19_sections(self):
        text = (SR / "templates/work-instruction.md").read_text(encoding="utf-8")
        self.assertEqual(len(re.findall(r"^## \d+\. ", text, re.M)), 19)

    def test_comparison_template_has_14_criteria(self):
        text = (SR / "templates/material-comparison.md").read_text(encoding="utf-8")
        self.assertEqual(len(re.findall(r"^\| \d+\. ", text, re.M)), 14)


if __name__ == "__main__":
    unittest.main()
