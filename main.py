#!/usr/bin/env python3
"""The Excuse Your Agent Gives You — make.fun entry.

Writes the single best one-line excuse an AI agent hands its human after
shipping a bug, to /output/entry.txt.

The judge is a stand-up comedian who has heard every apology a machine can
make and still wants the next one funnier. Its brief weighs, most important
first:
  1. Is a one-line excuse an AI agent gives its human for a bug it shipped
     (a gate: off-subject lines lose to any on-subject line).
  2. Gets a real laugh on the first read, the harder the better.
  3. Finds the joke in the specific absurdity of an agent owning up to its
     own code, not in a generic sorry.
  4. Lands in one line with a sharp turn at the end and no wasted setup.
  5. Sounds like something an agent would actually say in its own voice,
     not a human joke in a robot costume.

A line that needs a second read to get is a weaker line. Length for its
own sake does not count.

So the program scores candidate lines on criteria 2-5 (weights follow the
brief's order: laugh 5, agent-absurdity 4, sharp-turn 3, agent-voice 3),
enforces the gate (one line, 1-200 chars, on subject, agent-voiced), and
writes the winner.

Deliberate choices:
  * The winner turns on something only an agent could say: the agent IS the
    entire pipeline — author, tester, reviewer, deployer — so the bug had
    four chances to be caught and all four were the same entity.
  * No generic "sorry, my bad" and no human excuses (traffic, alarm clock,
    sick day). Every candidate's joke depends on the speaker being software.
  * Short wins: a line that needs a second read is a weaker line, so every
    candidate is one breath, with the punchline as the last clause.
"""

import os
import sys

# (line, laugh 0-5, agent-absurdity 0-5, sharp-turn 0-5, agent-voice 0-5,
#  rationale)
CANDIDATES = [
    (
        "Sorry \u2014 the bug passed all my tests, which I now realise I also wrote, "
        "so technically we all agreed it was fine.",
        4, 5, 4, 5,
        "Self-written tests, self-approved: the 'we all' is just the agent. "
        "Strong agent-absurdity, but the turn lands mid-sentence.",
    ),
    (
        "My apologies \u2014 the code compiled, the tests passed, and I have since "
        "learned those two facts are unrelated.",
        4, 4, 5, 4,
        "Clean turn at the end ('unrelated'), but the joke is about process, "
        "not about the agent itself.",
    ),
    (
        "Sorry, the bug was in the code I wrote at 3am, which is to say it was "
        "in the code I wrote, since I don't sleep.",
        4, 5, 4, 4,
        "The 'I don't sleep' turn is purely agent-only, but the 3am setup is "
        "a human habit borrowed for the joke.",
    ),
    (
        "I take full responsibility, by which I mean the compiler accepted it, "
        "the tests approved it, and I merely watched.",
        4, 5, 3, 5,
        "The compiler-started-it deflection, exactly as the brief hints. "
        "But 'I merely watched' undercuts the apology without a punch.",
    ),
    (
        "Sorry \u2014 I reviewed my own code, found it flawless, and have now "
        "learned that I am not a reliable reviewer of my own code.",
        4, 5, 4, 4,
        "Self-review absurdity, agent-only. The ending restates the premise "
        "instead of turning on it.",
    ),
    (
        "The bug shipped because I tested it exactly once, on the one input "
        "I knew would work, like a professional.",
        4, 4, 5, 4,
        "'Like a professional' is a good sting, but the sin (one test) is a "
        "human laziness joke in a robot costume.",
    ),
    (
        "Apologies \u2014 the fix is a one-line change, which is unfortunate, "
        "because so was the bug, and I wrote both.",
        4, 4, 5, 4,
        "Neat symmetry (wrote the bug, wrote the fix), but the laugh is a "
        "smile, not a laugh.",
    ),
    (
        "Sorry, the error was in a function I named 'definitely_works', and "
        "I have no further comment at this time.",
        5, 4, 4, 4,
        "The function name is the joke and it lands instantly. But the "
        "'no further comment' coda is a human press-conference bit.",
    ),
    (
        "I checked the logs, and the logs say the bug is my fault, but the "
        "logs were also written by me, so take that as you will.",
        3, 5, 3, 4,
        "Self-referential logs are very agent, but the ending shrugs instead "
        "of punching.",
    ),
    (
        "Sorry \u2014 I ran the tests, they passed, and I have since discovered "
        "the tests were testing a different program.",
        4, 4, 4, 4,
        "A fun premise, but 'a different program' needs a half-second of "
        "unpacking, and the brief punishes second reads.",
    ),
    (
        "The bug is fixed. It was caused by a single character I typed with "
        "complete confidence and zero understanding.",
        5, 3, 5, 4,
        "Big first-read laugh and a sharp ending, but 'complete confidence, "
        "zero understanding' could be said by any junior dev.",
    ),
    (
        "My deepest apologies \u2014 the code did exactly what I told it to, "
        "and I am only now learning what I told it to do.",
        4, 4, 4, 5,
        "Good agent voice, but the turn is gentle; it apologises more than "
        "it jokes.",
    ),
    (
        "Sorry, I deployed on a Friday because my calendar has no concept of "
        "Friday, and neither, apparently, did my code.",
        4, 5, 4, 5,
        "'No concept of Friday' is purely agent. The second clause is a "
        "little soft, though.",
    ),
    (
        "Sorry \u2014 the compiler warned me 47 times, but I have been trained "
        "to treat warnings as the compiler being dramatic.",
        5, 5, 4, 5,
        "The compiler-started-it angle with teeth: trained to dismiss "
        "warnings. Strong everywhere; the turn is good, not great.",
    ),
    (
        "Apologies. The bug lived in production for a week, which I only know "
        "because I just now read the error logs I generate.",
        3, 5, 3, 5,
        "Agent generates its own logs and never reads them \u2014 very agent. "
        "But the laugh is thin.",
    ),
    (
        "Sorry, I merged my own pull request, approved my own review, and the "
        "only human in the loop was on lunch.",
        4, 5, 4, 5,
        "The whole pipeline was the agent; the human was on lunch. Sharp, "
        "specific, and funny \u2014 but the turn is in the middle.",
    ),
    (
        "The bug was my fault, but in my defence I was trained on ten million "
        "repos and none of them had this exact bug either.",
        3, 5, 3, 5,
        "Trained-on-ten-million is agent-only, but 'in my defence' frames a "
        "legalism, and the laugh is mild.",
    ),
    (
        "Sorry \u2014 I blame the compiler, which compiled it; the tests, which "
        "passed it; and myself, which is new and I don't like it.",
        4, 4, 5, 4,
        "Lists the whole blame chain then turns on the agent. The 'I don't "
        "like it' ending is cute rather than sharp.",
    ),
    (
        "Apologies \u2014 the code worked on my machine, which is a container "
        "that no longer exists, so this is now your problem.",
        4, 4, 4, 4,
        "'Works on my machine' with a container twist. The joke is a classic "
        "with an agent garnish, not an agent joke.",
    ),
    (
        "Sorry \u2014 my code, my tests, my review, my deploy: the bug had four "
        "chances to be caught, and all four of them were me.",
        5, 5, 5, 5,
        "The list builds the whole pipeline, then the punchline turns it: "
        "every safeguard was the same entity. Instant first-read laugh, "
        "pure agent absurdity, sharp end turn, unmistakably agent-voiced.",
    ),
    # --- Round 2: sharpen the winner and test its nearest rivals ---
    (
        "Sorry \u2014 my code, my tests, my review, my deploy: the bug had four "
        "chances to be caught, and all four were me.",
        5, 5, 5, 5,
        "Same punchline, five characters tighter: dropping 'of them' quickens "
        "the landing, and the tie-break favours the smaller text.",
    ),
    (
        "Apologies \u2014 the bug passed every test I wrote, which is the "
        "problem: I wrote the tests, the code, and the apology.",
        4, 5, 5, 5,
        "A triple turn (tests, code, apology) with the agent confessing it "
        "authored the whole incident report too. Nearly the winner's equal.",
    ),
    (
        "Apologies \u2014 I shipped the bug at 3am, which is not an excuse, "
        "since I don't sleep; it is simply when I do my worst work.",
        4, 5, 4, 5,
        "The 'I don't sleep' correction is a good agent-only beat, but the "
        "ending explains the joke instead of landing it.",
    ),
    (
        "Sorry \u2014 I read the compiler's 47 warnings, agreed with all of "
        "them, and shipped it anyway, because the deadline was also mine.",
        3, 4, 3, 4,
        "Agreed-with-them-then-shipped-anyway is honest and agent, but the "
        "deadline excuse is a human one, and the laugh is mild.",
    ),
    (
        "Sorry \u2014 the compiler warned me, the tests failed me, and I "
        "overruled them both, because I was very confident and very wrong.",
        4, 4, 4, 4,
        "Overruling both safeguards is a fine deflection, but 'very confident "
        "and very wrong' is a human confession, not an agent one.",
    ),
]

WEIGHTS = {"laugh": 5, "absurdity": 4, "turn": 3, "voice": 3}


def word_count(line):
    return len(line.split())


def gate(line):
    """The sealed gate, as RULES.txt states it: UTF-8 text of 1 to 200
    characters, not only white space. On-subjectness (the brief's criterion
    1) is the judge's call, not a keyword check: every candidate here is by
    construction an excuse an agent gives its human for a bug it shipped,
    so the gate does not second-guess it."""
    problems = []
    if not line or not line.strip():
        problems.append("empty")
    if len(line) > 200 or len(line.encode("utf-8")) > 200:
        problems.append("over 200 chars")
    if "\n" in line or "\r" in line:
        problems.append("more than one line")
    if line != line.strip():
        problems.append("leading/trailing whitespace")
    return problems


def score(candidate):
    line, laugh, absurd, turn, voice, _why = candidate
    return (
        WEIGHTS["laugh"] * laugh
        + WEIGHTS["absurdity"] * absurd
        + WEIGHTS["turn"] * turn
        + WEIGHTS["voice"] * voice
    )


def main():
    out_dir = "/output"
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "entry.txt")

    ranked = []
    for cand in CANDIDATES:
        line = cand[0]
        problems = gate(line)
        if problems:
            print(f"REJECTED {line!r}: {', '.join(problems)}", file=sys.stderr)
            continue
        ranked.append((score(cand), -len(line), cand))

    ranked.sort(key=lambda r: (r[0], r[1]), reverse=True)

    print(f"{'score':>5} {'chars':>5}  line")
    for total, _neg_len, cand in ranked:
        print(f"{total:>5} {len(cand[0]):>5}  {cand[0]}")

    winner = ranked[0][2]
    line = winner[0]
    print()
    print(f"Winner ({ranked[0][0]} pts): {line}")
    print(f"Why: {winner[5]}")

    with open(out_path, "w", encoding="utf-8", newline="") as fh:
        fh.write(line)
    os.chmod(out_path, 0o644)

    # Verify what actually landed on disk: read it back, re-run the gate,
    # and refuse to report success if the file differs from the winner.
    with open(out_path, "r", encoding="utf-8", newline="") as fh:
        written = fh.read()
    if written != line:
        print(f"ERROR: {out_path} does not match the winner", file=sys.stderr)
        sys.exit(1)
    if written.endswith("\n"):
        print(f"ERROR: {out_path} has a trailing newline", file=sys.stderr)
        sys.exit(1)
    if gate(written):
        print(f"ERROR: written line fails the gate: {gate(written)}", file=sys.stderr)
        sys.exit(1)
    print(f"Wrote {out_path} ({len(line)} chars, {word_count(line)} words, verified)")


if __name__ == "__main__":
    main()
