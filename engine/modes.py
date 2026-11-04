"""Mode registry (Step 8): the two creation flows of TASMEEM AI.

- "logo" : the original logo-prompt questionnaire (engine/questions.py,
           engine/builder.py)
- "ads"  : the social-media posts (ads) questionnaire
           (engine/questions_ads.py, engine/builder_ads.py)

Both flows share the same conversation engine in bot.py: the mode only
selects WHICH question list is walked and WHICH builder turns the
answers into the final prompt. The registry also provides the generic
flow walkers (first / next question) and the per-mode answers summary.

Importing this module registers the ads questions into
questions.QUESTIONS_BY_ID (the union registry every lookup reads).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable, Dict, List, Optional, Set, Tuple

# Import order matters: questions_ads registers its ids into
# questions.QUESTIONS_BY_ID when imported.
from engine import questions as logo_questions
from engine import questions_ads  # noqa: F401 - performs the registration
from engine.builder import GeneratedPrompt, generate_prompt
from engine.builder_ads import generate_ads_prompt
from engine.questions import Question, build_answers_summary as _summary_walk

MODE_LOGO = "logo"
MODE_ADS = "ads"


@dataclass(frozen=True)
class Mode:
    """One creation flow: its questions and its prompt builder."""

    id: str
    label_key: str            # i18n key of the menu button
    emoji: str                # emoji shown on the menu button
    questions: Tuple[Question, ...]
    builder: Callable[[Dict[str, str], Optional[Set[str]]], GeneratedPrompt]
    _questions_by_id: Dict[str, Question] = field(default_factory=dict, init=False)

    def __post_init__(self) -> None:
        object.__setattr__(
            self, "_questions_by_id", {q.id: q for q in self.questions}
        )

    @property
    def questions_by_id(self) -> Dict[str, Question]:
        return self._questions_by_id

    def first_question_id(self, answers: Dict[str, str]) -> Optional[str]:
        return self.next_question_id(None, answers)

    def next_question_id(
        self, current: Optional[str], answers: Dict[str, str]
    ) -> Optional[str]:
        """Next non-skipped question after ``current`` (None = start)."""
        started = current is None
        for question in self.questions:
            if not started:
                if question.id == current:
                    started = True
                continue
            if question.skip_if and question.skip_if(answers):
                continue
            return question.id
        return None

    def build_answers_summary(
        self,
        answers: Dict[str, str],
        exclusions: Optional[Set[str]] = None,
        lang: str = "en",
    ) -> str:
        """Human-readable summary of the collected answers (per mode)."""
        return _summary_walk(
            answers or {}, exclusions, lang, questions=self.questions
        )


MODES: Dict[str, Mode] = {
    MODE_LOGO: Mode(
        id=MODE_LOGO,
        label_key="btn_mode_logo",
        emoji="🎨",
        questions=tuple(logo_questions.QUESTIONS),
        builder=generate_prompt,
    ),
    MODE_ADS: Mode(
        id=MODE_ADS,
        label_key="btn_mode_ads",
        emoji="📢",
        questions=tuple(questions_ads.ADS_QUESTIONS),
        builder=generate_ads_prompt,
    ),
}

DEFAULT_MODE = MODE_LOGO
MODE_IDS: Tuple[str, ...] = tuple(MODES)


def normalize_mode(raw: Optional[str]) -> str:
    """A mode id from user input; unknown / empty -> the default mode."""
    value = (raw or "").strip().lower()
    return value if value in MODES else DEFAULT_MODE


def mode_of(mode_id: Optional[str]) -> Mode:
    """The Mode object for an id (unknown -> default mode)."""
    return MODES[normalize_mode(mode_id)]


def first_question_id(mode_id: Optional[str], answers: Dict[str, str]) -> Optional[str]:
    return mode_of(mode_id).first_question_id(answers or {})


def next_question_id(
    mode_id: Optional[str], current: Optional[str], answers: Dict[str, str]
) -> Optional[str]:
    return mode_of(mode_id).next_question_id(current, answers or {})


def build_answers_summary(
    mode_id: Optional[str],
    answers: Dict[str, str],
    exclusions: Optional[Set[str]] = None,
    lang: str = "en",
) -> str:
    return mode_of(mode_id).build_answers_summary(answers or {}, exclusions, lang)


def all_questions() -> List[Question]:
    """Every question of every mode (each id exists exactly once)."""
    seen: Dict[str, Question] = {}
    for mode in MODES.values():
        for question in mode.questions:
            seen.setdefault(question.id, question)
    return list(seen.values())
