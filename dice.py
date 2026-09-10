"""Pure dice logic — no discord imports. Easily unit-testable."""

from __future__ import annotations

import re
import secrets
from dataclasses import dataclass
from typing import Final

# Limits: generous but bounded to avoid abuse / huge embeds.
MAX_DICE: Final[int] = 100
MAX_SIDES: Final[int] = 1000
MAX_MODIFIER_ABS: Final[int] = 10_000

# Matches:  [N]dM[+-K]  e.g. "d20", "2d6", "2d6+3", " 1d20 - 5 "
_DICE_RE: Final[re.Pattern[str]] = re.compile(
    r"^\s*(?P<num>\d*)\s*d\s*(?P<sides>\d+)\s*(?P<mod>[+-]\s*\d+)?\s*$",
    re.IGNORECASE,
)


class DiceError(ValueError):
    """User-facing dice parsing/validation error."""


@dataclass(frozen=True, slots=True)
class RollResult:
    num_dice: int
    num_sides: int
    modifier: int
    rolls: tuple[int, ...]
    total: int

    @property
    def subtotal(self) -> int:
        return sum(self.rolls)

    @property
    def spec(self) -> str:
        base = f"{self.num_dice}d{self.num_sides}"
        if self.modifier > 0:
            return f"{base}+{self.modifier}"
        if self.modifier < 0:
            return f"{base}{self.modifier}"
        return base

    @property
    def is_nat20(self) -> bool:
        return self.num_dice == 1 and self.num_sides == 20 and self.rolls[0] == 20

    @property
    def is_nat1(self) -> bool:
        return self.num_dice == 1 and self.num_sides == 20 and self.rolls[0] == 1

    @property
    def is_all_max(self) -> bool:
        return bool(self.rolls) and all(r == self.num_sides for r in self.rolls)

    @property
    def is_all_min(self) -> bool:
        return bool(self.rolls) and all(r == 1 for r in self.rolls)


def parse_dice_spec(spec: str | None) -> tuple[int, int, int]:
    """Parse a dice spec string.

    Returns (num_dice, num_sides, modifier).
    Defaults to (1, 20, 0) when spec is None/empty.
    Raises DiceError on invalid input.
    """
    if not spec or not spec.strip():
        return (1, 20, 0)

    m = _DICE_RE.match(spec)
    if not m:
        raise DiceError("Invalid format. Use `XdY` or `XdY±Z` — e.g. `2d6`, `1d20+5`, `d6`.")

    raw_num = m.group("num")
    raw_sides = m.group("sides")
    raw_mod = m.group("mod")

    num_dice = int(raw_num) if raw_num else 1
    num_sides = int(raw_sides)
    modifier = int(raw_mod.replace(" ", "")) if raw_mod else 0

    if not (1 <= num_dice <= MAX_DICE):
        raise DiceError(f"Number of dice must be 1–{MAX_DICE} (got {num_dice}).")
    if not (2 <= num_sides <= MAX_SIDES):
        raise DiceError(f"Sides must be 2–{MAX_SIDES} (got {num_sides}).")
    if abs(modifier) > MAX_MODIFIER_ABS:
        raise DiceError(f"Modifier must be within ±{MAX_MODIFIER_ABS} (got {modifier}).")

    return (num_dice, num_sides, modifier)


def roll(
    spec: str | None = None,
    *,
    num_dice: int | None = None,
    num_sides: int | None = None,
    modifier: int = 0,
    rng: secrets.SystemRandom | None = None,
) -> RollResult:
    """Roll dice, either from a spec string or explicit numbers.

    Provide *either* `spec` *or* `num_dice`+`num_sides`.  If both are given,
    explicit numbers take precedence.  `rng` is injectable for deterministic tests.
    """
    if num_dice is not None or num_sides is not None:
        if num_dice is None or num_sides is None:
            raise DiceError("Both num_dice and num_sides are required.")
        parsed_num, parsed_sides, parsed_mod = num_dice, num_sides, modifier
        # Validate bounds consistently with parse_dice_spec.
        if not (1 <= parsed_num <= MAX_DICE):
            raise DiceError(f"Number of dice must be 1–{MAX_DICE} (got {parsed_num}).")
        if not (2 <= parsed_sides <= MAX_SIDES):
            raise DiceError(f"Sides must be 2–{MAX_SIDES} (got {parsed_sides}).")
        if abs(parsed_mod) > MAX_MODIFIER_ABS:
            raise DiceError(f"Modifier must be within ±{MAX_MODIFIER_ABS} (got {parsed_mod}).")
    else:
        parsed_num, parsed_sides, parsed_mod = parse_dice_spec(spec)

    rnd = rng or secrets.SystemRandom()
    rolls = tuple(rnd.randint(1, parsed_sides) for _ in range(parsed_num))
    total = sum(rolls) + parsed_mod
    return RollResult(
        num_dice=parsed_num,
        num_sides=parsed_sides,
        modifier=parsed_mod,
        rolls=rolls,
        total=total,
    )


def format_roll(result: RollResult, *, mention: str | None = None) -> str:
    """Legacy plain-text formatter (kept for parity). Prefer embeds in cogs."""
    prefix = f"{mention} " if mention else ""
    dice_label = f"D{result.num_sides}" if result.num_dice == 1 else f"{result.num_dice}d{result.num_sides}"
    mod_str = f"{result.modifier:+d}" if result.modifier else ""

    if result.num_dice == 1:
        r = result.rolls[0]
        if result.num_sides == 20:
            if r == 20:
                return f"{prefix}rolled a nat 20! Insane! 🎉 ({dice_label}{mod_str} → {result.total})"
            if r == 1:
                return f"{prefix}rolled a 1 on a D20... Bro's luck ran out ☠️ ({dice_label}{mod_str} → {result.total})"
            if r >= 19:
                return f"{prefix}rolled a D20 and got {r}! Bro is being edged by fate ☠️! ({dice_label}{mod_str} → {result.total})"
            return f"{prefix}rolled a D20 and got {r}! ({dice_label}{mod_str} → {result.total})"
        return f"{prefix}rolled a D{result.num_sides} and got {r}! ({dice_label}{mod_str} → {result.total})"

    if result.is_all_max:
        return f"{prefix}rolled {result.num_dice}d{result.num_sides}{mod_str} → {result.rolls} = {result.total} — maxed all of them! BRO WHAT THE HECK! 😭"
    if result.is_all_min:
        return f"{prefix}rolled {result.num_dice}d{result.num_sides}{mod_str} → {result.rolls} all 1s... astronomically unlucky ☠️☠️☠️ (= {result.total})"
    rolls_str = ", ".join(map(str, result.rolls))
    base = f"[{rolls_str}] = {result.subtotal}"
    if result.modifier:
        base += f" {result.modifier:+d} = {result.total}"
    return f"{prefix}rolled {result.num_dice}d{result.num_sides}{mod_str} → {base}"
