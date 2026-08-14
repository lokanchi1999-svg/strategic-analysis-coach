import pytest
from pathlib import Path
from backend.storage.skill_store import FileSkillStore, InvalidSkillError

@pytest.mark.asyncio
async def test_load_valid_skill():
    store = FileSkillStore(Path(__file__).parents[1] / "skills")
    assert (await store.load("five_forces"))["manifest"]["id"] == "five_forces"

@pytest.mark.asyncio
async def test_broken_skill_is_clear(tmp_path):
    folder = tmp_path / "analysis" / "broken"
    folder.mkdir(parents=True)
    (folder / "manifest.yaml").write_text("id: [", encoding="utf-8")
    with pytest.raises(InvalidSkillError, match="Invalid skill manifest"):
        await FileSkillStore(tmp_path).load("broken")
