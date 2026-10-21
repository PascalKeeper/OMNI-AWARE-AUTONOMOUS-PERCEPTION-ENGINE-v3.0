# Author: Joseph Rocco Peransi
"""Decision engine: weigh survival odds against cost.

Scores each hazard path and picks the best survival-to-cost ratio.
Example: cliff on the left, waterfall on the right — which do you take?
"""


def score_path(survival_odds: float, cost: float) -> float:
    """Survival-to-cost ratio. Higher is better."""
    return survival_odds / cost


def decide(options: dict) -> tuple:
    """Choose the best path from a dict of {name: (survival_odds, cost)}."""
    scores = {name: score_path(s, c) for name, (s, c) in options.items()}
    best = max(scores, key=scores.get)
    return best, scores[best], scores


# Default scenario: cliff left, waterfall right
DEFAULT_SCENARIO = {
    "cliff": (0.15, 1.0),       # low survival, high cost
    "waterfall": (0.85, 0.3),   # high survival, low cost
}


if __name__ == "__main__":
    choice, score, all_scores = decide(DEFAULT_SCENARIO)
    print(f"Decision: {choice} (score {score:.2f})")
    for name, s in all_scores.items():
        print(f"  {name}: {s:.2f}")