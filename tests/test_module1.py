"""Module 1 tests. The LLM is replaced by a fake transport, so no API key or network is needed."""
import json
import sys
from pathlib import Path

import pytest
from pydantic import BaseModel

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

import module1_pipeline as m1  # noqa: E402
from llm_client import LLMError, complete_json  # noqa: E402

TONE = m1.load_tone_profile(ROOT / "templates" / "tone_of_voice.yaml")

HOOKS = {"hooks": [{"hook_type": t, "text": f"hook about {t}", "platform_fit": ["linkedin"]} for t in m1.HOOK_TYPES]}
SCRIPT = {"rows": [{"time_range": f"{i * 5}-{i * 5 + 5}s", "voiceover": f"line {i}", "broll": "shot",
                    "text_overlay": "TEXT", "sfx": "none"} for i in range(6)]}
INSIGHTS = {"core_thesis": "Editing takes too long", "arguments": ["a"], "data_points": [], "soundbites": [],
            "pain_points": ["p"]}


class FakeLLM:
    """Answers each request according to the schema the pipeline asked for, and records the prompts."""

    def __init__(self):
        self.calls = []

    def __call__(self, system: str, user: str) -> str:
        self.calls.append((system, user))
        if '"hooks"' in system:
            return json.dumps(HOOKS)
        if '"rows"' in system:
            return json.dumps(SCRIPT)
        if '"core_thesis"' in system:
            return json.dumps(INSIGHTS)
        return json.dumps({"content": "A caption grounded in the transcript. #video"})


class Answer(BaseModel):
    value: int


def test_complete_json_retries_with_the_validation_error():
    replies = iter(["not json", '```json\n{"value": 3}\n```'])
    prompts = []

    def transport(system, user):
        prompts.append(user)
        return next(replies)

    assert complete_json("s", "u", Answer, transport=transport).value == 3
    assert "rejected" in prompts[1]


def test_complete_json_gives_up_after_retries():
    with pytest.raises(LLMError):
        complete_json("s", "u", Answer, transport=lambda s, u: "{}", retries=1)


def test_hooks_plan_requires_one_hook_per_type():
    duplicated = {"hooks": [dict(HOOKS["hooks"][0]) for _ in range(5)]}
    with pytest.raises(ValueError):
        m1.HooksPlan.model_validate(duplicated)


def test_pipeline_generates_from_the_transcript(tmp_path):
    transcript = tmp_path / "t.txt"
    transcript.write_text("Tese: Captions by hand waste an editor's afternoon.\nDor: Retyping every word.\n",
                          encoding="utf-8")
    llm = FakeLLM()
    out = m1.run_pipeline(transcript, TONE, ["instagram", "linkedin"], transport=llm)

    assert sorted(h.hook_type for h in out.hooks) == sorted(m1.HOOK_TYPES)
    assert len(out.script_table) == 6
    assert [c.platform for c in out.captions] == ["instagram", "linkedin"]
    assert out.captions[0].hashtags == ["video"]
    # every generation prompt carries the transcript, so output cannot be canned text
    assert all("Captions by hand waste" in user for _, user in llm.calls)
    assert out.metadata["mode"] == "llm"


def test_unmarked_transcript_is_structured_by_the_model(tmp_path):
    transcript = tmp_path / "t.txt"
    transcript.write_text("We talked for an hour about why editing takes so long.", encoding="utf-8")
    llm = FakeLLM()
    m1.run_pipeline(transcript, TONE, ["linkedin"], transport=llm)
    assert '"core_thesis"' in llm.calls[0][0]
    assert "Editing takes too long" in llm.calls[1][1]


def test_offline_mode_generates_nothing_and_calls_no_model(tmp_path):
    llm = FakeLLM()
    out = m1.run_pipeline(ROOT / "sample_transcript.txt", TONE, ["instagram"], offline=True, transport=llm)
    assert llm.calls == []
    assert out.hooks == [] and out.script_table == [] and out.captions == []
    assert len(out.cleaned_segments) > 1
    assert "not generated" in m1.write_output(out, tmp_path).read_text(encoding="utf-8")
