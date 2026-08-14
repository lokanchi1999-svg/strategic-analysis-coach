import json
from pathlib import Path
from backend.storage.case_store import FileCaseStore
from backend.storage.skill_store import FileSkillStore
from backend.tools.validation import validate_case, validate_skill

ROOT=Path(__file__).parents[1]

def test_current_placeholder_content_validates_with_warnings():
    skill=validate_skill(ROOT/"skills"/"analysis"/"five_forces")
    case=validate_case(ROOT/"cases"/"SAMPLE-CASE-01",ROOT)
    assert skill.valid and skill.warnings
    assert case.valid and case.warnings

def test_skill_validator_rejects_unknown_dimension_and_level(tmp_path):
    skill=tmp_path/"test_skill"; skill.mkdir()
    (skill/"manifest.yaml").write_text("id: test_skill\ntype: analysis\nversion: 0.1.0\nname: {en: Test, zh: 测试}\ndimensions: [known]\ndepth_levels: [1]\n",encoding="utf-8")
    (skill/"ontology.yaml").write_text("items: [{id: x, dimension: unknown}]",encoding="utf-8")
    (skill/"rubric.yaml").write_text("known: {level_2: placeholder}",encoding="utf-8")
    (skill/"questioning_policy.yaml").write_text("{}",encoding="utf-8")
    report=validate_skill(skill)
    assert not report.valid and any("unknown dimension" in x for x in report.errors) and any("depth level" in x for x in report.errors)

def test_skill_validator_rejects_duplicate_ids(tmp_path):
    skill=tmp_path/"test_skill"; skill.mkdir()
    (skill/"manifest.yaml").write_text("id: test_skill\ntype: analysis\nversion: 0.1.0\nname: {en: Test, zh: 测试}\ndimensions: []\ndepth_levels: [1]\n",encoding="utf-8")
    for name in ("ontology.yaml","rubric.yaml","questioning_policy.yaml"): (skill/name).write_text("items: [{id: duplicate}]",encoding="utf-8")
    assert any("duplicate" in x for x in validate_skill(skill).errors)

async def _load_dummy(skill_root,case_root):
    return await FileSkillStore(skill_root).load("test_skill"), await FileCaseStore(case_root).load("CASE-TEST-01")

def test_new_skill_and_case_are_discovered_without_engine_changes(tmp_path):
    skills=tmp_path/"skills"/"analysis"/"test_skill"; skills.mkdir(parents=True)
    (skills/"manifest.yaml").write_text("id: test_skill\ntype: analysis\nversion: 0.1.0\nname: {en: Test, zh: 测试}\ndimensions: []\ndepth_levels: [1]\n",encoding="utf-8")
    for name in ("ontology.yaml","rubric.yaml","questioning_policy.yaml"): (skills/name).write_text("{}",encoding="utf-8")
    case=tmp_path/"cases"/"CASE-TEST-01"; case.mkdir(parents=True)
    (case/"manifest.yaml").write_text("case_code: CASE-TEST-01\ntitle: Test\nskill_id: test_skill\ninstructor_id: default\nlanguage: en-US\n",encoding="utf-8")
    (case/"student_material.md").write_text("material",encoding="utf-8"); (case/"teacher_annotations.yaml").write_text("{}",encoding="utf-8")
    import asyncio
    loaded_skill,loaded_case=asyncio.run(_load_dummy(tmp_path/"skills",tmp_path/"cases"))
    assert loaded_skill["manifest"]["id"]=="test_skill" and loaded_case.manifest.skill_id=="test_skill"
