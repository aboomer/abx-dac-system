import random

MAX_RUN_LENGTH = 3


def _max_run_length(seq: list[str]) -> int:
    longest = current = 1
    for i in range(1, len(seq)):
        if seq[i] == seq[i - 1]:
            current += 1
            longest = max(longest, current)
        else:
            current = 1
    return longest


def generate_balanced_sequence(num_trials: int, seed: int) -> list[str]:
    """Deterministic: same (num_trials, seed) -> same sequence, forever.

    Returns which label ('A' or 'B') dac_path_1 holds each trial; dac_path_2
    gets the other label. Balanced (exactly num_trials/2 each), no run
    longer than MAX_RUN_LENGTH, via rejection sampling.
    """
    if num_trials <= 0 or num_trials % 2 != 0:
        raise ValueError("num_trials must be a positive even number")
    rng = random.Random(f"{seed}:dac_label")
    half = num_trials // 2
    pool = ["A"] * half + ["B"] * half
    while True:
        rng.shuffle(pool)  # random.Random.shuffle() IS Fisher-Yates
        if _max_run_length(pool) <= MAX_RUN_LENGTH:
            return pool[:]  # copy — caller must not see it mutate further


def generate_x_identity_sequence(num_trials: int, seed: int) -> list[str]:
    """Difference-test only. Independent per-trial coin flips.

    Deliberately NOT balanced like generate_balanced_sequence() — the
    methodology only specifies balance + max-run-3 for DAC<->label, not for
    label<->X. Balancing X too would make trials non-independent, which
    would undermine the binomial-significance comparison the results screen
    relies on (that comparison assumes each trial is an independent
    Bernoulli(0.5) draw for what X is).
    """
    rng = random.Random(f"{seed}:x_identity")
    return [rng.choice(["A", "B"]) for _ in range(num_trials)]


def generate_trial_sequence(
    num_trials: int, seed: int, test_type: str, dac_path_1_id: int, dac_path_2_id: int
) -> list[dict]:
    dac_label_seq = generate_balanced_sequence(num_trials, seed)
    x_seq = (
        generate_x_identity_sequence(num_trials, seed)
        if test_type == "difference"
        else [None] * num_trials
    )
    trials = []
    for i in range(num_trials):
        dac_a_id, dac_b_id = (
            (dac_path_1_id, dac_path_2_id)
            if dac_label_seq[i] == "A"
            else (dac_path_2_id, dac_path_1_id)
        )
        trials.append({
            "trial_index": i,
            "dac_a_path_id": dac_a_id,
            "dac_b_path_id": dac_b_id,
            "x_identity": x_seq[i],
        })
    return trials
