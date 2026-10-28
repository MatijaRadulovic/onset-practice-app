# onSET practice test: analysis and design

Based only on the 4 screenshots of the practice test (no access to onSET's own documentation).
Anything about "the real test" below is inferred from those 4 texts (80 gaps).

## 1. What the test is

A **C-test**: reduced-redundancy gap-filling. The first sentence stays whole; after that the second half of every
second word is deleted. Test-takers rebuild the words from the left-over letters and the context.

Reverse-engineered gap rule (my generator reproduces all 80 original gaps exactly):

- The first sentence is intact ("St." is not a sentence end). The first word of sentence 2 is intact.
- After every gap, **the next word is always left intact**, whatever it is (a number, a name, "one-hundred").
  Then the first *eligible* word is gapped.
- Not eligible: 1-letter words, numbers, hyphenated words, proper nouns (Patrick, France, Ireland).
- Gap = word minus its second half. The stump keeps `floor(length / 2)` letters (`sit|ting`, `t|he`, `a|nd`).
- 20 gaps, then the text continues intact. The tails are 14-25 words, ending on a full sentence.

## 2. Linguistic analysis of the 4 originals

| | Learning | Saint Patrick | Flea Markets | Olympic Disciplines |
|---|---|---|---|---|
| Type | abstract / opinion | narrative (past) | description | historical fact |
| Words | 68 | 89 | 81 | 77 |
| First sentence (words) | 13 | 26 | 15 | 19 |
| Words per sentence | 22.7 | 14.5 | 16.4 | 18.2 |
| Flesch reading ease | 46 | 69 | 66 | 55 |
| Function-word gaps | 9 | 6 | 7 | 6 |
| One-letter stumps | 7 | 7 | 5 | 5 |
| Verb gaps | 4 | 8 | 3 | 0 (+3 `-ing` nouns) |

Every text is neutral, encyclopedic, British English, culturally neutral, with no specialist knowledge needed.
The difficulty is not ordered easy to hard (Flesch 46, 69, 66, 55), so I did not build a ramp. Instead each of my
exams mixes text types and difficulty.

**What gets gapped (80 gaps)**

- Word classes: nouns 25, verbs 15, prepositions 11, adverbs 8, conjunctions 5, auxiliaries 4, pronouns 4, adjectives 4,
  quantifiers 2, article 1, negation 1. That makes 28/80 = **35 % function words**, 65 % content words.
- Stump length: 1 letter 30 %, 2 letters 38 %, 3 letters 21 %, 4+ letters 11 %. A third of the gaps are one-letter
  stumps, which are almost always grammar words (`t|he`, `a|t`, `i|n`, `a|nd`, `o|f`).
- Which cue solves the gap (my hand labels, see `tools/original-labels.tsv`):
  **grammar 34 %** (agreement, tense, parallelism), **fixed phrase / collocation 34 %** (`a lot of`, `in fact`, `such as`,
  `taken place`, `all kinds of`, `went by`), **sentence meaning 25 %**, **needs wider context only 8 %**.
- So about two thirds of the gaps are solvable from 1-3 neighbouring words, and most gaps have exactly one natural answer.
- The text type changes the gaps: the narrative text has 8 verb gaps (irregular past `grew`, `spent`, `went`; passive
  `kidnapped`), the expository ones lean on nouns and collocations.

## 3. Testing point of view

- **What it measures:** overall language proficiency (vocabulary, grammar, spelling, reading) in one task. The gaps
  are a sample of the text's own word types, so no individual item is "designed"; the designer controls the *text*.
- **A good gap has one acceptable answer.** Collocations and grammar make that happen. Open-class guesses
  (any adjective, any noun) are the weak spots.
- **Gaps in one text are not independent** (a solved neighbour helps). Treat each text as one unit, as my app does
  with its per-text scores.
- **Difficulty is controlled by the text**: sentence length, vocabulary frequency, abstraction, and how many gaps are
  grammar words (easy) versus inflected verbs and open-class words (harder).
- **Spelling variants are a hazard** (colour/color, harbour/harbor, kilometres/kilometers, realise/realize): the same
  stump fits both, so a correct answer might be marked wrong. My checker rejects these as gap words.

## 4. How my texts were designed

1. **Blueprint from the original:** 68-95 words, first sentence 12-28 words, tail 14-30 words, 25-50 % function words,
   4-8 one-letter stumps, no gap word repeated more than twice, at most one gapped word visible elsewhere in the text,
   gap words up to 10 letters, no UK/US variants.
2. **Gap placement is mechanical, so I tune the wording, not the gaps.** Each draft (`tools/drafts/`) has optional
   phrases such as `{really |}` or `{big|large}`. `tools/tune.py` tries every combination and keeps the one whose gaps
   fit the blueprint and avoid known ambiguity patterns. Whatever the tuner picks, I then re-read.
3. **By-eye review of every gap** for a second acceptable answer. I read all 80 texts gap by gap. This found
   a lot that the numbers cannot see, for example:
   - same-stump rivals: `qui[ckly/etly]`, `po[les/sts]`, `pla[nted/ced]`, `ever[yone/ybody]`, `sm[all/art]`
   - tense / aspect rivals: `dr[ank/ink]`, `sa[ys/id]`
   - the "which word" families: `th[is/at/ese/ose]`, `wh[en/ile/ere]`, sentence-initial `T[he/wo/en]`
   - knowledge-only answers (`Joha[nnes]`, `gold[smith]`, `samba sch[ools]`) and gaps on names (`Rio d[e] Janeiro`)
   - number answers that fit two numbers (`fo[ur/rty]`)
   - a wording bug the tuner could not see: two option slots combined into "passed on by word of mouth by word of mouth"
4. The checker (`tools/qa.py`) enforces the numeric blueprint, and it was calibrated on the 4 originals first:
   all four pass it.

## 5. Result: 10 exams x 8 texts (+ the original)

| | Original (4 texts) | Mine (80 texts) |
|---|---|---|
| Words per text | 79 (68-89) | 84 (69-95) |
| First sentence | 18 | 16 |
| Tail after gap 20 | 18 | 22 |
| Flesch reading ease | 59 (46-69) | 60 (44-75) |
| Function-word gaps | 7.0 | 8.1 |
| One-letter stumps | 6.0 | 6.2 |
| Stump length 1 / 2 / 3 / 4+ | 30 / 38 / 21 / 11 % | 31 / 36 / 21 / 12 % |
| Gap word repeated more than twice | 0 | 0 |
| Inflected-verb gaps per text | 3.8 | **1.4** |

Every text has exactly 20 gaps and passes all the numeric checks (80/80).

## 6. Limits (be honest about these)

- **Fewer verb gaps than the original** (1.4 vs 3.8 per text). My texts are mostly explanatory; the original mixes in
  a narrative text. It is similar in every exam (0.8-1.9 per text); the narrative-style texts (Coffee, Cats, Tea Culture,
  Moon Landing, Lighthouses) have the most (4-5).
- **No real item statistics.** I cannot know how hard each gap really is without people taking the test. I only
  controlled what can be controlled from the text.
- **Soft spots I accepted** (a competent reader may type the other word): Ice Cream `sa[ys/id]`,
  Electric Cars `qui[eter/cker]`, Time Zones `bec[ame/ome]`, Lighthouses `da[wn]` / `dark`,
  Recycling `th[em/ese]`, Noise `mo[re/st] likely`, Smartphones `th[is/eir] habit`, Bridges `str[eam]`.
- **Found in the manual read-through and fixed:** Space Exploration ("let us forecast…, to find… and to watch" was
  ungrammatical), Titanic ("described it unsinkable"), Online Shopping ("you … our door"), Printing Press
  ("churches and people"), Silk Road ("added a profit"), Music ("beloved tune"), Coral Reefs `th[ese/ose]`,
  Electric Cars `wh[ile/en]`, Time Zones (1884 conference fact). Cause: the tuner never checks grammar, so two
  drafts had option combinations that did not fit together.
  Expect one or two debatable gaps per text, which the original also has (`ma[kes/de]`, `different t[o/han]`).
- **Reconstructed answers of the original:** the screenshots show only stumps. I fixed one answer after review:
  `ma[kes]` (not `made`), because the sentence says "always means". The others fit but are my reconstruction.

## 7. Files

- `tools/gen.py` builds every exam folder from `tools/sources/`: `python3 tools/gen.py`
- `tools/qa.py` checks texts; `exam-03 -c` shows the gaps inline, `--original` prints the profile above
- `tools/tune.py` picks the best wording of a draft: `python3 tools/tune.py exam-03 --write`
- `tools/drafts/` the authored texts with optional phrases; `tools/sources/` the chosen wording
- `tools/original-labels.tsv` hand labels of the 80 original gaps
