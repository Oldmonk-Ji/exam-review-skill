# Review JSON schema and runtime contract

Requires Python 3.9+ and only its standard library. Open the generated HTML in a modern browser with JavaScript and WOFF2 support. No CDN or network request is needed for rendering: KaTeX 0.16.11, its auto-render script, CSS and all 20 bundled WOFF2 font faces are embedded. Build with:

```sh
python /absolute/path/to/scripts/build_review.py input.json output.html
python /absolute/path/to/scripts/build_review.py --help
```

The command can run from any working directory. Input is UTF-8 (optional BOM). Output is one UTF-8 HTML file; create its parent directory first. Paths under `figures` resolve relative to the input JSON, not the command's working directory. The Python API is `build(data, input_dir=path_to_input_directory)`; `input_dir` is required when using relative figure paths. Local figure files must be authorized inputs. The builder reads only named files and bundled assets.

## Top-level object

- `title`: nonempty string.
- `status`: string, including an empty string.
- `chapters`: nonempty array of chapter objects.
- `questions`: array of question objects. `[]` is supported for lecture-only material; no practice controls, reset button or report card is rendered.
- `sidebar`, `collapse_index`: optional booleans, default false.
- `lesson_base`: optional relative HTML path or HTTP(S) URL, default empty. Cannot contain a fragment, whitespace, backslashes or a protocol-relative URL. Question links append `#lesson_id` or `#chapter`. Even when linking another file, lesson IDs must refer to a declared section or chapter in this JSON.
- `exam_minutes`: optional positive finite number. Only this field enables timed closed-book practice; there is no default duration. Omit it for ordinary practice.
- `storage_digest`: optional 16 lowercase hexadecimal characters. See progress isolation below.

All chapter, section and question IDs are globally unique, start with an ASCII letter or digit, and otherwise contain ASCII letters, digits or hyphens. Generated UI IDs and `practice-{chapter-id}` are reserved. Required strings are validated explicitly with `ValueError`; Python `-O` does not disable validation. Text fields may contain newlines and tabs, but not other control characters. Unknown metadata fields are ignored by rendering but included in the default digest.

## Chapters and lecture sections

A chapter requires `id`, nonempty `title`, `source` (string), and `notes` (string). Optional:

- `sections`: array, each with unique `id`, nonempty `title`, and `body` string.
- Section strings `english_title`, `symbols`, and `pages` are optional.
- Section `bilingual`: array of `{ "en": "English explanation", "zh": "中文解释" }` pairs; both strings must be nonempty.
- `figures`: array of `{ "path": "images/example.png", "caption": "Description" }`. Supported extensions: `.png`, `.jpg`, `.jpeg`, `.gif`, `.webp`, `.svg`. Images are embedded as base64 data, SVG only in image context, never injected into the document DOM. Validate image provenance and visual content before publishing.

The sidebar and section index support English titles, notation, source page ranges and lesson links. Chapters without questions do not get empty practice headings.

## Questions

Every question requires:

- `id`, `chapter` (an existing chapter ID), `type` (`mcq`, `tf`, or `reveal`).
- Nonempty strings `text`, `solution`, `source`.
- Optional `lesson_id`, referencing its own chapter or a section in that chapter.
- Optional strings `difficulty`, `family`, `unique_focus`. The difficulty picker offers `基础`, `进阶`, `综合`; other strings are displayed but not offered as predefined filters.
- Optional `points`: positive finite number, default 1. Points are displayed; the page reports question counts, not a weighted exam score. Booleans are not accepted as points.

`mcq` requires an `options` object with at least two nonempty string values, keyed by single uppercase letters, and an `answer` string equal to an option key. `tf` requires `answer` equal to `T` or `F`. `reveal` uses a saved draft and manually revealed solution; no automatic grading is claimed. Its optional `answer` is a string, but the human explanation belongs in `solution`.

Objective accuracy uses only answered objective questions as its denominator. Reveal-only material reports viewing progress without objective accuracy. Viewing a solution is not evidence of mastery.

## Text and math safety

User text is HTML-escaped, including math inequalities and matrix ampersands, before KaTeX renders it. Supported lightweight markup includes paragraphs, lists, tables, callouts, bold, emphasis, HTTP(S) Markdown links, `$inline math$` and `$$display math$$`. Raw HTML is never trusted. JavaScript/data link schemes are not rendered as links. JSON escapes TeX backslashes: `"$\\alpha < \\beta$"`. Literal currency dollar signs are not a complete Markdown parser feature; avoid ambiguous delimiter pairs.

The generated `#selfcheck` stores JSON diagnostics, also accessible as `window.reviewSelfcheck`, after DOMContentLoaded: question type counts, missing answers/solutions, actual KaTeX nodes/errors and library load status. It becomes visible when errors are found. Browser verification is still necessary for typography, unsupported TeX and interaction behavior.

## Progress isolation and reset

By default, the full input JSON is SHA-256 hashed (first 16 hex characters). Changes to questions, options, answers, solutions or other JSON fields create a new storage namespace. Existing answers are never silently reused across a changed default digest. Repeated identical builds are deterministic. Progress is stored in browser localStorage for that origin and digest; storage behavior for `file://` is browser-dependent. It is not a cloud sync or backup.

A supplied `storage_digest` overrides isolation. Use it only for deliberately compatible layout-only rebuilds. The author is responsible for rotating it whenever IDs, questions, options, answers or meaning change; otherwise old answers and drafts may be reused incorrectly. When the digest matches, the previous generic renderer’s `ai_review_<digest>` question map and `notes_<digest>` drafts/bookmarks are normalized on load. Only valid current question IDs and option choices are retained. The old notes key is not deleted. The next normal save stores the new combined format; later resets do not resurrect old notes. Course-specific legacy namespaces are not imported.

“重置全部作答” asks for confirmation and clears answers, revealed solutions, drafts and bookmarks for this review. Starting a timed session separately asks confirmation that existing answers and drafts will be cleared while bookmarks are retained. Cancelling either confirmation preserves data.

## Timed practice

Timed practice hides notes, explanations, sources and correctness styling, including option circles; choices have a neutral selected outline. Search excludes hidden solution content. The deadline and active mode are saved with the review. Refresh resumes the mode and deadline; an expired deadline clearly ends the session with retained answers and an explanatory notice. Ending early asks confirmation. Storage denial/private-browser restrictions may prevent persistence; check browser storage before relying on refresh recovery.

This is a self-study interface, not secure assessment or anti-cheating software. Answers remain in the offline HTML, the device clock is user-controlled, and developer tools can inspect data.

## Regression tests

Synthetic public fixtures only, under `tests/fixtures/{mixed,reveal,notes}.json`:

```sh
PYTHONDONTWRITEBYTECODE=1 python -m unittest discover -s tests -v
node --check scripts/review.js
node tests/test_state.js
```

Tests cover mixed/reveal/lecture-only rendering, optimized-mode rejection, invalid schema, escaping, inequalities/matrices, deterministic rebuilds, progress digests, relative images, offline font URLs, and CLI use from another directory. Generate HTML from the fixtures outside the distributable skill directory for independent browser QA. Browser testing must exercise selection, filtering, drafts, bookmarks, cancellation/confirmation, refresh persistence, timed-session hiding, reset and selfcheck.
