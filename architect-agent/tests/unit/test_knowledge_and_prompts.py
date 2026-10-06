from archagent.agent.prompts import ArchitectPrompts, PERSONA
from archagent.knowledge import load_rules, rules_brief

REQUIRED = {"spatial_planning", "room_adjacency", "dimensions", "circulation", "walls", "doors_windows", "stairs",
            "ventilation", "lighting", "geometry_rules", "rendering_rules"}


def test_all_rule_files_exist_and_separate_hard_from_heuristic():
    rules = load_rules()
    assert REQUIRED <= set(rules)
    for name in REQUIRED - {"rendering_rules", "walls", "lighting"}:
        assert "HARD" in rules[name] or "HEURISTIC" in rules[name], name


def test_validator_codes_quoted_in_rules_exist_in_code():
    import re
    from pathlib import Path
    src = "".join(p.read_text() for p in Path("src/archagent").rglob("*.py"))
    for code in set(re.findall(r"\b([A-Z]{3,}(?:_[A-Z]+)+)\b", rules_brief())):
        if code in {"HARD_RULE", "HARD_RULES"}:
            continue
        probe = code.split('_', 1)[1] if code.split('_')[0] in {'DOOR', 'WINDOW'} else code   # f-string built codes
        assert probe in src, f"rules mention {code} but no validator emits it"


def test_system_prompt_states_the_product_and_formats_cleanly():
    assert "AI architecture agent" in PERSONA and "not software" in PERSONA
    text = ArchitectPrompts.main_system.format(final_reminders="", shell_cmd_prompt="")
    assert "NEVER regenerate the whole building" in text and "VALIDATION PASSED" in text
