"""Quality checks for C-test sources (tools/sources/exam-*.txt).

python3 tools/qa.py                     summary of all exams (flags only)
python3 tools/qa.py exam-03 -v          annotated texts: stump[answer], rivals, flags
python3 tools/qa.py --original          profile of the 4 original texts vs. hand labels

A text is "clean" when no hard flag is raised. "rivals" are other closed-class words that
fit the same stump (same first letters, same length rule) - check by eye that the context
rules them out; a good C-test gap has exactly one acceptable solution.
"""
import collections
import pathlib
import re
import statistics as st
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import gen  # noqa: E402

W = lambda s: set(s.split())
GROUPS = {
    "ART": W("a an the"),
    "PREP": W("in on at by for with from of to into onto over under through during before after between "
              "among about against across along behind below beneath beside beyond despite down except "
              "inside near off out outside past since than toward towards until up upon within without "
              "like unlike throughout"),
    "CONJ": W("and but or nor so yet because although though while whereas if unless whether as that "
              "once when where than"),
    "PRON": W("i you he she it we they me him her us them my your his its our their mine yours hers ours "
              "theirs myself yourself himself herself itself ourselves themselves who whom whose which "
              "what whatever whoever this that these those"),
    "AUX": W("be am is are was were been being have has had having do does did will would shall should "
             "can could may might must"),
    "QUANT": W("some any no every each all both either neither many much more most few fewer less least "
               "several other another such own same enough one"),
    "NEG": W("not no"),
}
FUNC_GROUPS = set(GROUPS)
ADV = W("always never often usually also too very quite just only even still already ever then there "
        "here why how today now soon again far well almost rather really however perhaps therefore thus "
        "indeed later around")
IRREG = W("went gone grew grown spent made took taken saw seen came became begun began brought built "
          "bought caught chose chosen drew drawn drove driven ate eaten fell fallen felt found flew flown "
          "forgot gave given got held kept knew known led left lost met paid ran rose said sold sent shown "
          "sat stood taught told thought threw thrown understood wore won wrote written spoke spoken broke "
          "broken heard lay meant")
LINK_GROUPS = {"PREP": "LINK", "CONJ": "LINK"}  # in/if, at/as ... compete as 'linking words'
VARIANTS = re.compile(r"^(real|organ|recogn|apolog|summar|emphas|special|critic|civil|popular|modern|industrial|"
                      r"global|familiar|minim|maxim|util|memor|symbol|final|local|author|character|categor|"
                      r"priorit|visual|digital|national|analy)(is|iz|s)(e|ed|es|ing|ation|ations|er|ers)$"
                      r"|^(colour|color|centre|center|grey|gray|programme|program|favour|behaviour|neighbour|"
                      r"honour|labour|harbour|flavour|humour|rumour|vapour|armour|savour|theatre|metre|litre|defence|licence|practise|travelling|traveling|"
                      r"cancelled|jewellery|tyre|tire|cheque|storey|whilst|amongst|travell?(ed|er|ers|ing)|travel(ed|er|ers))|(metres?|meters?)$")

# hard limits, widened a little around what the 4 original texts show (see analysis.md)
try:  # lowercase dictionary entries only, so names (Johannes, Gutenberg) are not "words"
    LOWER = {w.strip() for w in open("/usr/share/dict/american-english") if w[:1].islower()}
except OSError:
    LOWER = None

LIMITS = dict(words=(65, 95), first=(12, 28), tail=(14, 30), func=(0.25, 0.50), one_letter=(4, 8),
              avg_sent=(10, 24), max_dup=2, max_len=10, min_unique=15, max_repeats=1)


def groups_of(w):
    return {g for g, s in GROUPS.items() if w in s}


def is_func(w):
    return bool(groups_of(w))


def verbform(w):
    return w in IRREG or (w.endswith("ed") and len(w) >= 5) or (w.endswith("ing") and len(w) >= 6)


def weight(word, stump_len):
    """Heuristic gap difficulty: grammar words easy, open-class and inflected forms harder."""
    if is_func(word):
        return 1.0 if stump_len == 1 else 1.3
    base = 1.8 if word in ADV else (2.4 if verbform(word) else 2.0)
    if word in IRREG:
        base += 0.2
    return base + (0.4 if len(word) >= 8 else 0)


def syllables(w):
    w = re.sub(r"[^a-z]", "", w.lower())
    n = len(re.findall(r"[aeiouy]+", w))
    if w.endswith("e") and not w.endswith("le") and n > 1:
        n -= 1
    if w.endswith("ed") and not re.search(r"[td]ed$", w) and n > 1:
        n -= 1
    return max(n, 1)


def readability(body):
    sents = [s for s in re.split(r"(?<=[.!?])\s+", body.replace("St.", "St")) if s.strip()]
    words = [w for w in re.findall(r"[A-Za-z']+", body)]
    syl = sum(syllables(w) for w in words)
    wps, spw = len(words) / len(sents), syl / len(words)
    return len(sents), len(words), wps, 206.835 - 1.015 * wps - 84.6 * spw, 0.39 * wps + 11.8 * spw - 15.59


def analyse(title, body):
    body = " ".join(body.split())
    text, answers = gen.make_gaps(body)
    btoks, gtoks = body.split(" "), text.split(" ")
    pos = [i for i, t in enumerate(gtoks) if gen.BLANK in t]
    first = next(i for i, t in enumerate(btoks) if gen.ends_sentence(t)) + 1
    n_sent, n_words, wps, fre, fk = readability(body)
    full_words = [a[2].lower() for a in answers]
    info = dict(title=title, body=body, text=text, answers=answers, pos=pos, btoks=btoks, gtoks=gtoks,
                words=len(btoks), first=first, tail=len(gtoks) - pos[-1] - 1 if pos else 0,
                sents=n_sent, avg_sent=wps, fre=fre, fk=fk)
    info["func"] = sum(is_func(w) for w in full_words)
    info["func_ratio"] = info["func"] / max(len(answers), 1)
    info["one_letter"] = sum(len(k) == 1 for k, _, _ in answers)
    info["verbal"] = sum((not is_func(w)) and verbform(w) for w in full_words)
    info["adv"] = sum(w in ADV for w in full_words)
    info["D"] = st.mean(weight(w.lower(), len(k)) for k, _, w in answers) if answers else 0
    dup = collections.Counter(full_words)
    info["dups"] = {w: c for w, c in dup.items() if c > 1}
    info["unique"] = len(dup)

    flags = []
    if len(answers) != gen.GAPS:
        flags.append(f"{len(answers)} gaps")
    for key in ("words", "first", "tail"):
        lo, hi = LIMITS[key]
        if not lo <= info[key] <= hi:
            flags.append(f"{key}={info[key]} (want {lo}-{hi})")
    lo, hi = LIMITS["func"]
    if not lo <= info["func_ratio"] <= hi:
        flags.append(f"function words {info['func']}/20")
    lo, hi = LIMITS["one_letter"]
    if not lo <= info["one_letter"] <= hi:
        flags.append(f"1-letter stumps={info['one_letter']} (want {lo}-{hi})")
    lo, hi = LIMITS["avg_sent"]
    if not lo <= wps <= hi:
        flags.append(f"avg sentence {wps:.1f} words")
    for w, c in info["dups"].items():
        if c > LIMITS["max_dup"]:
            flags.append(f"'{w}' gapped {c}x")
    if info["unique"] < LIMITS["min_unique"]:
        flags.append(f"only {info['unique']} different gap words")
    repeats = []
    # giveaway: gapped content word (or its stem) is visible elsewhere in the text
    for (k, m, w), p in zip(answers, pos):
        wl = w.lower()
        if wl in GROUPS["ART"] or is_func(wl):
            continue
        if len(wl) > LIMITS["max_len"]:
            flags.append(f"'{wl}' longer than {LIMITS['max_len']} letters")
        if LOWER is not None and w[:1].isupper() and wl not in LOWER and wl not in ADV:
            flags.append(f"'{w}' looks like a proper noun")
        if VARIANTS.search(wl):
            flags.append(f"'{wl}' has UK/US spelling variants")
        stem = wl[: max(4, len(wl) - 3)]
        others = [re.sub(r"[^a-z]", "", t.lower()) for j, t in enumerate(gtoks) if j != p and gen.BLANK not in t]
        if any(o.startswith(stem) for o in others):
            repeats.append(wl)
    if len(repeats) > LIMITS["max_repeats"]:
        flags.append("gapped words visible elsewhere in the text: " + ", ".join(repeats))
    info["repeats"] = repeats
    info["flags"] = flags
    return info


def _vocab():
    words = set()
    for f in (HERE / "sources").glob("exam-*.txt"):
        words |= {w.lower() for w in re.findall(r"[A-Za-z]{4,}", f.read_text())}
    return words


VOCAB = _vocab()


def corpus_rivals(answer, stump):
    """Other words used somewhere in our texts that fit the same stump (e.g. quickly/quietly)."""
    a, k = answer.lower(), len(stump)
    if is_func(a) or k < 2:
        return []
    # same ending = same grammar slot (quickly/quietly, painting/paintings), the real danger
    return sorted(w for w in VOCAB if w != a and w.startswith(stump.lower()) and len(w) // 2 == k
                  and w[-2:] == a[-2:])


def rivals(answer, stump):
    """Closed-class words that fit the same stump and share the answer's word group."""
    a = answer.lower()
    gs = {LINK_GROUPS.get(g, g) for g in groups_of(a)}
    if not gs:
        return []
    pool = set().union(*GROUPS.values()) | ADV
    out = []
    for w in sorted(pool):
        if w != a and w.startswith(stump.lower()) and len(w) // 2 == len(stump):
            if gs & {LINK_GROUPS.get(g, g) for g in groups_of(w)}:
                out.append(w)
    return out


def inline(f):
    """Text with every gap written as stump[missing], for reading the whole text at once."""
    out, k = [], 0
    for t in f["gtoks"]:
        if gen.BLANK in t:
            kept, miss, _ = f["answers"][k]
            k += 1
            out.append(f"{kept}[{miss}]" + re.sub(r"^[A-Za-z]+" + gen.BLANK, "", t))
        else:
            out.append(t)
    return " ".join(out)


def show(info, verbose, compact=False):
    f = info
    print(f"  {f['title']:28s} words={f['words']:3d} first={f['first']:2d} tail={f['tail']:2d} "
          f"sent={f['avg_sent']:4.1f} FRE={f['fre']:3.0f} | func={f['func']:2d} 1-letter={f['one_letter']:2d} "
          f"verbal={f['verbal']:2d} D={f['D']:.2f}  {'OK' if not f['flags'] else 'FLAGS'}")
    for fl in f["flags"]:
        print(f"      ! {fl}")
    if compact:
        print("      " + inline(f))
        riv = [f"{w}~{'/'.join(rivals(w, k))}" for k, _, w in f["answers"] if rivals(w, k)]
        if riv:
            print("      rivals: " + "  ".join(riv))
        cr = [f"{w}~{'/'.join(corpus_rivals(w, k))}" for k, _, w in f["answers"] if corpus_rivals(w, k)]
        if cr:
            print("      similar words in corpus: " + "  ".join(cr))
    if verbose:
        for n, ((k, m, w), p) in enumerate(zip(f["answers"], f["pos"]), 1):
            left = " ".join(f["btoks"][max(0, p - 4):p])
            right = " ".join(f["btoks"][p + 1:p + 4])
            riv = rivals(w, k)
            tag = f"   <- also fits stump: {', '.join(riv)}" if riv else ""
            print(f"      {n:2d}. {left} [{k}|{m}]{re.sub(r'^[A-Za-z]+', '', f['btoks'][p])} {right}{tag}")


def load(path):
    out = []
    raw = sys.stdin.read() if path is None else path.read_text()  # path=None: try a text from stdin
    for b in raw.split("== ")[1:]:
        title, body = b.strip().split("\n", 1)
        out.append(analyse(title, body))
    return out


def original_profile():
    texts = load(HERE / "sources" / "exam-original.txt")
    labels = collections.defaultdict(list)
    for line in (HERE / "original-labels.tsv").read_text().splitlines():
        if line and not line.startswith("#") and not line.startswith("text\t"):
            t, n, ans, cls, cue = line.split("\t")
            labels[int(t)].append((ans, cls, cue))
    print("ORIGINAL TEXTS - text level")
    for f in texts:
        show(f, False)
    allv = [(i, ans, cls, cue) for i in labels for ans, cls, cue in labels[i]]
    func = FUNC_GROUPS
    print("\nHAND LABELS (80 gaps)")
    for i in sorted(labels):
        c = collections.Counter(cls for _, cls, _ in labels[i])
        cue = collections.Counter(cu for _, _, cu in labels[i])
        nf = sum(v for k, v in c.items() if k in func)
        print(f"  text {i}: function {nf:2d} | " + " ".join(f"{k}={v}" for k, v in c.most_common()) +
              " | cues " + " ".join(f"{k}={v}" for k, v in cue.most_common()))
    c = collections.Counter(cls for _, _, cls, _ in allv)
    cue = collections.Counter(cu for *_, cu in allv)
    nf = sum(v for k, v in c.items() if k in func)
    print(f"  ALL: function {nf}/80 ({nf/80:.0%}) | " + " ".join(f"{k}={v}" for k, v in c.most_common()))
    print("  cues: " + " ".join(f"{k}={v} ({v/80:.0%})" for k, v in cue.most_common()))
    stumps = collections.Counter(len(k) for f in texts for k, _, _ in f["answers"])
    print("  stump length:", dict(sorted(stumps.items())))
    agree = sum(is_func(ans) == (cls in func) for _, ans, cls, _ in allv)
    print(f"  heuristic function/content classifier agrees with hand labels on {agree}/80 gaps")
    return texts


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("-")]
    verbose = "-v" in sys.argv
    if "--original" in sys.argv:
        original_profile()
        return
    if "--stdin" in sys.argv:  # echo "== Title\ntext" | python3 tools/qa.py --stdin -c
        srcs = [None]
    else:
        srcs = [HERE / "sources" / (a if a.endswith(".txt") else a + ".txt") for a in args] or \
            sorted((HERE / "sources").glob("exam-[0-9]*.txt"))
    bad = total = 0
    for src in srcs:
        print(src.stem if src else "stdin")
        for f in load(src):
            show(f, verbose, "-c" in sys.argv)
            total += 1
            bad += bool(f["flags"])
    print(f"\n{total - bad}/{total} texts without hard flags")


if __name__ == "__main__":
    main()
