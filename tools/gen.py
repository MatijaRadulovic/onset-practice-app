import re, sys, pathlib

GAPS = 20
TAIL_MIN = 14
BLANK = "______"
ABBR = {"St.", "Mr.", "Mrs.", "Ms.", "Dr.", "Prof.", "Jr.", "Sr.", "vs."}
WORD = re.compile(r"([A-Za-z]+)([.,;:!?]*)")


def slug(s):
    return re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-")


def ends_sentence(tok):
    return bool(re.search(r"[.!?]$", tok)) and tok not in ABBR


def make_gaps(body):
    """onSET-style C-test gaps, reverse-engineered from the original practice texts.

    - first sentence stays intact ("St." etc. do not end a sentence)
    - first word of the 2nd sentence stays intact
    - after every gap, the NEXT word stays intact whatever it is (number, name, ...)
    - then the first ELIGIBLE word gets a gap: >= 2 letters, only letters (no digits,
      hyphens, apostrophes), and not a proper noun (capitalised mid-sentence)
    - gap = second half of the word removed, keeping floor(len/2) letters
    - after GAPS gaps the rest of the text is intact, cut after the first sentence
      end that leaves at least TAIL_MIN words (originals: 14-25 words)
    """
    tokens = body.split(" ")
    start = next(i for i, t in enumerate(tokens) if ends_sentence(t)) + 1
    out, answers = tokens[:start], []
    skip = True  # first word of sentence 2
    for i in range(start, len(tokens)):
        tok = tokens[i]
        if len(answers) >= GAPS:
            out.append(tok)
        elif skip:
            out.append(tok)
            skip = False
        else:
            m = WORD.fullmatch(tok)
            initial = ends_sentence(tokens[i - 1])
            if m and len(m.group(1)) >= 2 and (initial or not m.group(1)[0].isupper()):
                word, punct = m.groups()
                keep = len(word) // 2
                out.append(word[:keep] + BLANK + punct)
                answers.append((word[:keep], word[keep:], word))
                skip = True
            else:
                out.append(tok)
    # originals end shortly after the last gap: cut at the first sentence end
    # that leaves >= TAIL_MIN intact words after it
    last = max(i for i, t in enumerate(out) if BLANK in t)
    for n, j in enumerate(range(last + 1, len(out)), 1):
        if ends_sentence(out[j]) and n >= TAIL_MIN:
            out = out[: j + 1]
            break
    return " ".join(out), answers


def build(src, out_dir):
    exam = src.stem  # e.g. exam-01
    blocks = [b.strip() for b in src.read_text().split("== ")[1:]]
    folder = out_dir / exam
    folder.mkdir(parents=True, exist_ok=True)
    for old in folder.glob("text-*.md"):  # names depend on order/titles
        old.unlink()
    ans_lines = [f"# {exam.replace('-', ' ').title()} - Answers", ""]
    ok = True
    for i, b in enumerate(blocks, 1):
        title, body = b.split("\n", 1)
        body = " ".join(body.split())
        text, answers = make_gaps(body)
        if len(answers) != GAPS:
            print(f"!! {exam} text {i} '{title}': {len(answers)} gaps")
            ok = False
        tail = text.split(BLANK)[-1].split()
        if len(tail) < 8:
            print(f"?? {exam} text {i} '{title}': only {len(tail)} words after last gap")
        name = f"text-{i}-{slug(title)}.md"
        (folder / name).write_text(
            f"# {title}\n\n"
            f"*{exam.replace('-', ' ').title()} · Text {i} of {len(blocks)} · "
            f"Complete the {GAPS} gaps (each gap = missing second half of the word).*\n\n"
            f"{text}\n"
        )
        ans_lines += [f"## Text {i}: {title}", ""]
        for k, (kept, miss, full) in enumerate(answers, 1):
            ans_lines.append(f"{k}. **{kept}**{miss} → {full}")
        ans_lines.append("")
    (folder / "answers.md").write_text("\n".join(ans_lines))
    print(exam, "OK" if ok else "PROBLEMS")


def main():
    """python3 tools/gen.py            -> rebuild every exam from tools/sources/exam-*.txt
    python3 tools/gen.py SRC OUT_DIR   -> build one source file into OUT_DIR"""
    here = pathlib.Path(__file__).resolve().parent
    if len(sys.argv) == 3:
        build(pathlib.Path(sys.argv[1]), pathlib.Path(sys.argv[2]))
    else:
        for src in sorted((here / "sources").glob("exam-*.txt")):
            build(src, here.parent)


if __name__ == "__main__":
    main()
