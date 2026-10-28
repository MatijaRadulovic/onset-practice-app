"""Pick the best wording of a draft text so that the (mechanical) gaps fall on good words.

Drafts live in tools/drafts/exam-NN.txt. They are normal texts with optional slots:
    {very |}          optional word (empty option = leave out)
    {big|large}       alternative phrasings (first option = preferred)
Every combination is tried; the one whose gaps best match the profile of the original test
(see analysis.md) wins. Ties go to the first options. Nothing here judges whether an answer is
unique - read the result with `qa.py exam-NN -c`.

python3 tools/tune.py exam-02            show the best wording of every text
python3 tools/tune.py exam-02 --write    ... and write it to tools/sources/exam-02.txt
python3 tools/tune.py exam-02 --only Chocolate --write   re-tune one text, keep the others
"""
import itertools
import pathlib
import random
import re
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import qa  # noqa: E402

SLOT = re.compile(r"\{([^{}]*)\}")
WH_CLASH = {"when", "while", "where"}
DEMONSTRATIVE = {"this", "that", "these", "those"}  # all share the stump 'th'


def render(draft, choice):
    it = iter(choice)
    return " ".join(SLOT.sub(lambda m: m.group(1).split("|")[next(it)], draft).split())


def score(f):
    s = 10 * len(f["flags"])
    s += max(0, 6 - f["func"], f["func"] - 9)
    s += max(0, 5 - f["one_letter"], f["one_letter"] - 7)
    s += 0.5 * max(0, 2 - f["verbal"])
    s += 0.5 * sum(c - 1 for c in f["dups"].values())
    s += 0.15 * sum(1 for k, _, w in f["answers"] if qa.rivals(w, k))
    s += 0.3 * len(f["repeats"])
    s += 0.25 * sum(1 for k, _, w in f["answers"] if qa.corpus_rivals(w, k))
    for (k, m, w), p in zip(f["answers"], f["pos"]):  # demonstrative use: "Before th[at] time", "Th[is] saves"
        prev = f["btoks"][p - 1].lower().strip(",;:")
        if w.lower() in {"this", "these", "those"} or (
                w.lower() == "that" and (qa.gen.ends_sentence(f["btoks"][p - 1]) or prev in qa.GROUPS["PREP"])):
            s += 1
        if len(k) == 1 and qa.gen.ends_sentence(f["btoks"][p - 1]):  # sentence-initial one-letter stump: no context
            s += 0.7
        if w.lower() in WH_CLASH:  # Wh[en] / Wh[ile] / Wh[ere]
            s += 0.7
        if w.lower() == "the" and qa.gen.ends_sentence(f["btoks"][p - 1]):  # T[he] / T[wo] / T[en]
            s += 0.7
    return s


def tune(title, draft, cap=4000):
    slots = [m.split("|") for m in SLOT.findall(draft)]
    combos = list(itertools.product(*[range(len(o)) for o in slots]))
    if len(combos) > cap:
        rnd = random.Random(7)
        combos = sorted(rnd.sample(combos, cap))
    best = None
    for c in combos:
        f = qa.analyse(title, render(draft, c))
        sc = score(f)
        if best is None or sc < best[0] - 1e-9:
            best = (sc, c, f)
    return best, len(combos), slots


def main():
    name = sys.argv[1]
    src = HERE / "drafts" / (name + ".txt")
    only = sys.argv[sys.argv.index("--only") + 1] if "--only" in sys.argv else None
    done = {}  # existing resolved texts, kept as they are when --only is used
    if only and (HERE / "sources" / (name + ".txt")).exists():
        for b in (HERE / "sources" / (name + ".txt")).read_text().split("== ")[1:]:
            t, body = b.strip().split("\n", 1)
            done[t] = body.strip()
    out = []
    for b in src.read_text().split("== ")[1:]:
        title, draft = b.strip().split("\n", 1)
        if only and title != only:
            out.append(f"== {title}\n{done[title]}\n")
            continue
        (sc, choice, f), n, slots = tune(title, draft)
        qa.show(f, False, True)
        picked = [s[i] for s, i in zip(slots, choice) if len(s) > 1 and i > 0]
        print(f"      score={sc:.2f} over {n} wordings; non-default choices: {picked}")
        out.append(f"== {title}\n{f['body']}\n")
    if "--write" in sys.argv:
        (HERE / "sources" / (name + ".txt")).write_text("\n".join(out))
        print(f"written tools/sources/{name}.txt")


if __name__ == "__main__":
    main()
