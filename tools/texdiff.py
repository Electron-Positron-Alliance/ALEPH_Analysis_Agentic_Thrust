#!/usr/bin/env python3
r"""
Minimal latexdiff replacement: word-level LaTeX markup diff.

latexdiff is not installed in this environment and cannot be fetched, so this
does the same job for the subset of LaTeX this manuscript uses.

Design notes / safety rules:
  * Tokenises into "atoms": inline math ($...$), LaTeX commands with their
    braced arguments, braced groups, alignment/row separators (& and \\),
    comments, whitespace, and words.
  * Never splits inside inline math or inside a command's argument list --
    such an atom is replaced wholesale if it changed.
  * Never wraps markup ACROSS a structural separator (&, \\, \begin, \end,
    \item, blank line, or a display-math delimiter). Changes are emitted per
    segment, so a table row or an equation body can never be broken.
  * Segments containing display math or verbatim-like environments are marked
    at segment granularity rather than word granularity.

Output: for each changed file, a copy with \DIFadd{...} / \DIFdel{...} markup.
The preamble is injected into main.tex.
"""

import os
import re
import shutil
import sys
from difflib import SequenceMatcher

PREAMBLE = r"""
%% ---- diff markup (latexdiff-compatible macro names) ----
\usepackage{color}
\usepackage[normalem]{ulem}
\providecommand{\DIFadd}[1]{{\protect\color{blue}\uwave{#1}}}
\providecommand{\DIFdel}[1]{{\protect\color{red}\sout{#1}}}
\providecommand{\DIFaddbegin}{}
\providecommand{\DIFaddend}{}
\providecommand{\DIFdelbegin}{}
\providecommand{\DIFdelend}{}
%% ---- end diff markup ----
"""

# True structural separators: markup must never span these.
# NB: commands that own a braced argument (\caption, \label, \includegraphics,
# \multicolumn, ...) are deliberately NOT listed. Splitting there would sever a
# command from its own argument and emit e.g. a bare \caption.
SEPARATOR_RE = re.compile(
    r"(\\\\|&|\\begin\b|\\end\b|\\item\b|\\hline\b|\\cline\b|\n\s*\n)"
)

# Environments whose bodies we diff only at segment granularity.
FRAGILE_ENV = re.compile(r"\\begin\{(equation|align|eqnarray|tabular|tabularx|verbatim|lstlisting|tikzpicture)\*?\}")

# Commands where a changed argument must be diffed INSIDE the braces. Replacing
# the whole atom would emit the command twice -- two \caption's in one float, or
# a \abstract inside \DIFdel in the preamble.
RECURSE_CMDS = {
    "abstract", "caption", "title", "section", "subsection", "subsubsection",
    "paragraph", "textbf", "textit", "emph", "texttt", "footnote", "keywords",
}

# Commands that must never carry markup: wrapping them breaks the reference,
# the float, or the build. If changed, the new value is emitted unmarked.
NEVER_MARK_CMDS = {
    "label", "ref", "eqref", "cite", "input", "include", "includegraphics",
    "bibliography", "bibliographystyle", "author", "affiliation", "emailAdd",
    "documentclass", "usepackage", "newcommand", "renewcommand",
    "providecommand", "setcounter", "usetikzlibrary", "definecolor",
    # tabular primitives: these must be the first token in a cell and cannot
    # appear inside another command's argument
    "multicolumn", "multirow", "multispan", "hline", "cline",
}

# A line containing any of these is structural: it cannot be struck through as
# a unit, so deletions are dropped and insertions emitted unmarked.
TABULAR_LINE_RE = re.compile(r"(&|\\\\\s*$|\\multicolumn|\\multirow|\\hline|\\cline)")

CMD_HEAD_RE = re.compile(r"^\\([A-Za-z@]+)\*?")


def cmd_name(atom):
    m = CMD_HEAD_RE.match(atom)
    return m.group(1) if m else None


def is_comment(atom):
    """A % comment atom. Wrapping one in markup comments out the closing brace."""
    return atom.lstrip().startswith("%")


def split_cmd_arg(atom):
    """Split '\\name[opt]{body}' into ('\\name[opt]{', body, '}'). None if not that shape."""
    if not atom.startswith("\\") or not atom.endswith("}"):
        return None
    i = atom.find("{")
    if i == -1:
        return None
    depth = 0
    for j in range(i, len(atom)):
        if atom[j] == "{":
            depth += 1
        elif atom[j] == "}":
            depth -= 1
            if depth == 0:
                if j != len(atom) - 1:
                    return None  # multiple args - too risky to recurse
                return atom[: i + 1], atom[i + 1 : j], atom[j:]
    return None

ATOM_RE = re.compile(
    r"""
      (?P<comment>(?<!\\)%[^\n]*\n?)
    | (?P<dmath>\$\$.*?\$\$)
    | (?P<imath>(?<!\\)\$(?:\\.|[^$\\])*\$)
    | (?P<cmd>\\[A-Za-z@]+\*?(?:\s*\[[^\]]*\])*(?:\s*\{(?:[^{}]|\{[^{}]*\})*\})*)
    | (?P<esc>\\[^A-Za-z])
    | (?P<group>\{(?:[^{}]|\{[^{}]*\})*\})
    | (?P<space>\s+)
    | (?P<word>[^\s\\${}&%]+)
    | (?P<other>.)
    """,
    re.VERBOSE | re.DOTALL,
)


def atomise(text):
    return [m.group(0) for m in ATOM_RE.finditer(text)]


def split_segments(text):
    """Split into segments at structural separators, keeping the separators."""
    parts = SEPARATOR_RE.split(text)
    return [p for p in parts if p is not None]


def is_separator(s):
    return bool(SEPARATOR_RE.fullmatch(s))


def is_blank(s):
    return s.strip() == ""


def wrap(macro, atoms):
    """Wrap a run of atoms in \\DIFadd/\\DIFdel, preserving outer whitespace."""
    s = "".join(atoms)
    if s.strip() == "":
        return s
    lead = s[: len(s) - len(s.lstrip())]
    trail = s[len(s.rstrip()):]
    core = s.strip()
    if re.search(r"(?<!\\)%", core):
        # Defensive: some other path handed us a comment. Put the closing brace
        # on its own line so the % cannot comment it out.
        return f"{lead}\\{macro}{{{core}\n}}{trail}"
    return f"{lead}\\{macro}{{{core}}}{trail}"


def mark_run(macro, atoms):
    """Wrap a run, but emit never-mark commands bare so nothing breaks.

    A deleted \\label or \\includegraphics must not end up inside \\DIFdel: for
    deletions we drop them, for insertions we keep them unmarked.
    """
    if not any(is_comment(t) or (t.startswith("\\") and cmd_name(t) in NEVER_MARK_CMDS)
               for t in atoms):
        return wrap(macro, atoms)
    out = []
    buf = []
    for t in atoms:
        if is_comment(t):
            # A comment can never be wrapped: the % would swallow the closing
            # brace. Keep added comments verbatim, drop deleted ones.
            if buf:
                out.append(wrap(macro, buf))
                buf = []
            if macro == "DIFadd":
                out.append(t)
            continue
        if t.startswith("\\") and cmd_name(t) in NEVER_MARK_CMDS:
            if buf:
                out.append(wrap(macro, buf))
                buf = []
            if macro == "DIFadd":
                out.append(t)  # keep new structural commands, unmarked
        else:
            buf.append(t)
    if buf:
        out.append(wrap(macro, buf))
    return "".join(out)


def diff_segment(old, new):
    """Word-level diff of one segment. Falls back to whole-segment markup."""
    if FRAGILE_ENV.search(old) or FRAGILE_ENV.search(new):
        if old == new:
            return new
        out = ""
        if old.strip():
            out += wrap("DIFdel", [old])
        if new.strip():
            out += wrap("DIFadd", [new])
        return out or new

    a, b = atomise(old), atomise(new)
    sm = SequenceMatcher(None, a, b, autojunk=False)
    out = []
    for tag, i1, i2, j1, j2 in sm.get_opcodes():
        if tag == "equal":
            out.append("".join(b[j1:j2]))
        elif tag == "delete":
            out.append(mark_run("DIFdel", a[i1:i2]))
        elif tag == "insert":
            out.append(mark_run("DIFadd", b[j1:j2]))
        else:  # replace
            # A 1:1 command swap where only the argument changed: recurse into
            # the braces instead of duplicating or wrapping the command.
            if i2 - i1 == 1 and j2 - j1 == 1:
                oa, na = a[i1], b[j1]
                name = cmd_name(na)
                if name and name == cmd_name(oa):
                    if name in NEVER_MARK_CMDS:
                        out.append(na)
                        continue
                    if name in RECURSE_CMDS:
                        so, sn = split_cmd_arg(oa), split_cmd_arg(na)
                        if so and sn:
                            out.append(sn[0] + diff_segment(so[1], sn[1]) + sn[2])
                            continue
            # mark_run, not wrap: a replaced run can contain a never-mark
            # command. Wrapping a deleted \\ref inside \\DIFdel leaves the diff
            # citing a label that the new version removed -- an undefined
            # reference in the diff build -- and a wrapped \\label would collide
            # with the same label in the added text.
            out.append(mark_run("DIFdel", a[i1:i2]))
            out.append(mark_run("DIFadd", b[j1:j2]))
    return "".join(out)


def diff_line(old, new):
    """Diff one physical line, segment by segment, never spanning separators."""
    so, sn = split_segments(old), split_segments(new)
    sm = SequenceMatcher(None, so, sn, autojunk=False)
    out = []
    for tag, i1, i2, j1, j2 in sm.get_opcodes():
        if tag == "equal":
            out.append("".join(sn[j1:j2]))
        elif tag == "delete":
            for seg in so[i1:i2]:
                out.append(seg if (is_separator(seg) or is_blank(seg))
                           else mark_run("DIFdel", atomise(seg)))
        elif tag == "insert":
            for seg in sn[j1:j2]:
                out.append(seg if (is_separator(seg) or is_blank(seg))
                           else mark_run("DIFadd", atomise(seg)))
        else:
            olds, news = so[i1:i2], sn[j1:j2]
            if len(olds) == len(news):
                for o, n in zip(olds, news):
                    out.append(n if (o == n or is_separator(n) or is_blank(n))
                               else diff_segment(o, n))
            else:
                for seg in olds:
                    if not (is_separator(seg) or is_blank(seg)):
                        out.append(mark_run("DIFdel", atomise(seg)))
                for seg in news:
                    out.append(seg if (is_separator(seg) or is_blank(seg))
                               else mark_run("DIFadd", atomise(seg)))
    return "".join(out)


def diff_file(old_text, new_text):
    """Line-level diff, with word-level markup inside changed lines.

    Line granularity at the top level is what keeps tabular material safe: a
    deleted table row is dropped rather than struck through, because
    \\multicolumn cannot survive inside \\DIFdel and a half-struck row has the
    wrong number of & separators.
    """
    ol, nl = old_text.split("\n"), new_text.split("\n")
    sm = SequenceMatcher(None, ol, nl, autojunk=False)
    out = []
    for tag, i1, i2, j1, j2 in sm.get_opcodes():
        if tag == "equal":
            out.extend(nl[j1:j2])
        elif tag == "delete":
            for line in ol[i1:i2]:
                if line.strip() and not TABULAR_LINE_RE.search(line):
                    out.append(mark_run("DIFdel", atomise(line)))
                # structural / blank deleted lines: dropped
        elif tag == "insert":
            for line in nl[j1:j2]:
                if line.strip() and not TABULAR_LINE_RE.search(line):
                    out.append(mark_run("DIFadd", atomise(line)))
                else:
                    out.append(line)
        else:
            olds, news = ol[i1:i2], nl[j1:j2]
            if len(olds) == len(news):
                for o, n in zip(olds, news):
                    out.append(n if o == n else diff_line(o, n))
            else:
                # unequal block: word-diff the joined text if neither side is
                # tabular, else fall back to emitting the new lines
                if not any(TABULAR_LINE_RE.search(x) for x in olds + news):
                    out.append(diff_line("\n".join(olds), "\n".join(news)))
                else:
                    for line in olds:
                        if line.strip() and not TABULAR_LINE_RE.search(line):
                            out.append(mark_run("DIFdel", atomise(line)))
                    out.extend(news)
    return "\n".join(out)


def _match_brace(s, i):
    """i points at '{'. Return index just past the matching '}', or -1."""
    depth = 0
    while i < len(s):
        if s[i] == "\\":
            i += 2
            continue
        if s[i] == "{":
            depth += 1
        elif s[i] == "}":
            depth -= 1
            if depth == 0:
                return i + 1
        i += 1
    return -1


REPAIR_CMDS = ("caption", "abstract", "title", "section", "subsection",
               "subsubsection", "paragraph", "keywords")


def repair_singletons(text):
    """Undo any \\DIFdel{\\cmd{A}}\\DIFadd{\\cmd{B}} that would emit \\cmd twice.

    Rewrites to \\cmd{<word-diff of A vs B>}. A float with two \\caption's, or a
    duplicated \\abstract, is a hard LaTeX error, so this is a correctness pass,
    not cosmetics.
    """
    fixed = 0
    for name in REPAIR_CMDS:
        pat = "\\DIFdel{\\" + name + "{"
        while True:
            k = text.find(pat)
            if k == -1:
                break
            # outer \DIFdel{...}
            dopen = k + len("\\DIFdel")
            dend = _match_brace(text, dopen)
            if dend == -1:
                break
            inner_del = text[dopen + 1 : dend - 1]           # \cmd{A}
            rest = text[dend:]
            m = re.match(r"(\s*)\\DIFadd\{", rest)
            if not m:
                # deletion with no paired insertion: keep the command, drop markup
                text = text[:k] + inner_del + rest
                fixed += 1
                continue
            aopen = dend + m.end() - 1
            aend = _match_brace(text, aopen)
            if aend == -1:
                break
            inner_add = text[aopen + 1 : aend - 1]           # \cmd{B}
            sa, sb = split_cmd_arg(inner_del), split_cmd_arg(inner_add)
            if sa and sb:
                repl = sb[0] + diff_segment(sa[1], sb[1]) + sb[2]
            else:
                repl = inner_add
            text = text[:k] + repl + text[aend:]
            fixed += 1

    # Emitting a never-mark command bare can leave a stray space after a
    # non-breaking tilde ("Sec.~ \ref{...}"), which prints a double space.
    text = re.sub(r"~[ \t]+(\\(?:ref|eqref|cite|citep|citet)\b)", r"~\1", text)
    return text, fixed


def inject_preamble(text):
    m = re.search(r"(\\documentclass[^\n]*\n)", text)
    if not m:
        return PREAMBLE + text
    i = m.end()
    return text[:i] + PREAMBLE + text[i:]


def main():
    if len(sys.argv) != 4:
        print("usage: texdiff.py <OLD_dir> <NEW_dir> <OUT_dir>")
        return 2
    old_dir, new_dir, out_dir = (os.path.abspath(p) for p in sys.argv[1:4])

    if os.path.exists(out_dir):
        shutil.rmtree(out_dir)
    shutil.copytree(new_dir, out_dir)

    def tex_files(root_dir):
        found = []
        for root, _dirs, files in os.walk(root_dir):
            for fn in sorted(files):
                if fn.endswith(".tex"):
                    found.append(os.path.relpath(os.path.join(root, fn), root_dir))
        return sorted(found)

    new_rel = tex_files(new_dir)
    old_rel = tex_files(old_dir)

    changed, added, removed = [], [], []
    for rel in new_rel:
        o, n = os.path.join(old_dir, rel), os.path.join(new_dir, rel)
        nt = open(n, encoding="utf-8").read()
        if os.path.exists(o):
            ot = open(o, encoding="utf-8").read()
        else:
            # A file with no counterpart in OLD is entirely new. Diffing it
            # against the empty string routes it through the same line-level
            # logic as any other change, so every line lands in \DIFadd and
            # tabular rows are still emitted unmarked rather than struck.
            ot = ""
            added.append(rel)
        if ot == nt:
            continue
        marked = diff_file(ot, nt)
        marked, nrep = repair_singletons(marked)
        open(os.path.join(out_dir, rel), "w", encoding="utf-8").write(marked)
        na = marked.count("\\DIFadd{")
        nd = marked.count("\\DIFdel{")
        changed.append((rel, na, nd, nrep))

    # Files deleted since OLD. out_dir is a copy of new_dir, so they are absent
    # from it and their removal would otherwise never appear anywhere in the
    # markup. Write the old body marked as deleted; it renders only if NEW's
    # main.tex still \input's the path, so say which case each one is.
    main_new = ""
    mp = os.path.join(new_dir, "main.tex")
    if os.path.exists(mp):
        main_new = open(mp, encoding="utf-8").read()
    for rel in old_rel:
        if rel in new_rel:
            continue
        stem = re.sub(r"\.tex$", "", rel)
        still_input = bool(re.search(
            r"\\(?:input|include)\s*\{\s*" + re.escape(stem) + r"(?:\.tex)?\s*\}", main_new))
        ot = open(os.path.join(old_dir, rel), encoding="utf-8").read()
        marked = diff_file(ot, "")
        marked, _ = repair_singletons(marked)
        dest = os.path.join(out_dir, rel)
        os.makedirs(os.path.dirname(dest), exist_ok=True)
        open(dest, "w", encoding="utf-8").write(marked)
        removed.append((rel, len(ot.splitlines()), still_input))

    mainp = os.path.join(out_dir, "main.tex")
    t = open(mainp, encoding="utf-8").read()
    open(mainp, "w", encoding="utf-8").write(inject_preamble(t))

    print(f"changed files: {len(changed)}")
    tot_a = tot_d = tot_r = 0
    for rel, na, nd, nrep in changed:
        flag = f"   (repaired {nrep})" if nrep else ""
        print(f"  {rel:48s} +{na:<4d} -{nd}{flag}")
        tot_a += na
        tot_d += nd
        tot_r += nrep
    print(f"  {'TOTAL':48s} +{tot_a:<4d} -{tot_d}   singleton repairs: {tot_r}")
    for rel in added:
        print(f"  NOTE {rel}: new file - every line marked as added")
    for rel, nlines, still_input in removed:
        if still_input:
            print(f"  NOTE {rel}: deleted ({nlines} lines) - body marked as deleted "
                  f"and still \\input, so it renders struck through")
        else:
            print(f"  WARN {rel}: deleted ({nlines} lines) and no longer \\input by "
                  f"main.tex, so its body CANNOT appear in the diff PDF; "
                  f"see `git diff` for what was cut")
    return 0


if __name__ == "__main__":
    sys.exit(main())
