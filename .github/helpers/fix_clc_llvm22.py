#!/usr/bin/env python3
"""Fix Mesa src/compiler/clc/clc_helpers.cpp for LLVM/Clang 22.

Anchors on the first/last `#include <clang/...>` line rather than on
specific headers, because Debian/upstream reorder includes between
releases and clang headers may be included transitively.
"""
import re
import sys


GUARD = (
    "#ifdef UNUSED\n"
    "#  undef UNUSED\n"
    "#endif\n"
    "#include <clang/Basic/OffloadArch.h>\n"
    "#define UNUSED __attribute__((unused))\n"
    "\n"
)


def dump_context(src, needle):
    """Print 60 lines around needle (or the first 60 lines) to stderr."""
    lines = src.splitlines()
    print(f"--- DEBUG: context for {needle!r} ---", file=sys.stderr)
    idx = next((i for i, l in enumerate(lines) if needle in l), None)
    lo = max(0, (idx or 0) - 30)
    hi = min(len(lines), lo + 60)
    for i in range(lo, hi):
        print(f"{i + 1:5d}: {lines[i]}", file=sys.stderr)
    print("--- END DEBUG ---", file=sys.stderr)


def fix_create_diagnostics_llvm22(src):
    """Wrap createDiagnostics in #if LLVM_VERSION_MAJOR >= 22.

    LLVM 22 changed CompilerInstance::createDiagnostics():
      LLVM 20/21: createDiagnostics(FileSystem&, DiagnosticConsumer*)
      LLVM 22:    createDiagnostics(DiagnosticConsumer*, bool)

    For LLVM 22 we drop the FileSystem& argument and let the
    CompilerInstance create its own VFS. The DiagnosticConsumer is
    constructed inline, same as for older LLVM.
    """
    marker = "c->createDiagnostics("
    idx = src.find(marker)
    if idx < 0:
        return src, "marker-not-found"

    # Indentation of the line starting with `c->createDiagnostics(`
    line_start = src.rfind("\n", 0, idx) + 1
    indent = src[line_start:idx]
    if indent.strip():
        # Not at start of a line - bail out, cannot guess indentation.
        indent = "   "

    # Already patched?
    look_back = max(0, line_start - 200)
    if "#if LLVM_VERSION_MAJOR >= 22" in src[look_back:idx]:
        return src, "already-patched"

    # Find matching closing `)` for the call (balance parentheses).
    i = idx + len(marker)
    depth = 1
    while i < len(src) and depth > 0:
        if src[i] == '(':
            depth += 1
        elif src[i] == ')':
            depth -= 1
        i += 1
    if depth != 0:
        return src, "unbalanced-parens"

    old_call = src[idx:i]

    new_block = (
        "#if LLVM_VERSION_MAJOR >= 22\n"
        + indent + "c->createDiagnostics(\n"
        + indent + "   new clang::TextDiagnosticPrinter(diag_log_stream,\n"
        + indent + "                                    c->getDiagnosticOpts()));\n"
        + "#else\n"
        + old_call + "\n"
        + "#endif"
    )

    src = src[:idx] + new_block + src[i:]
    return src, "patched"


def patch(path):
    with open(path) as f:
        src = f.read()

    # --- 1. UNUSED macro guard ------------------------------------------
    # Insert before the first `#include <clang/...>`, whatever it is.
    m = re.search(r"^#include <clang/[^>]+>\n", src, flags=re.MULTILINE)
    if not m:
        dump_context(src, "#include <clang/")
        sys.exit("no `#include <clang/...>` line found")
    if "clang/Basic/OffloadArch.h" not in src:
        src = src[:m.start()] + GUARD + src[m.start():]

    # --- 2. clang/Options/OptionUtils.h for GetResourcesPath ------------
    # Insert after the last `#include <clang/...>` line.
    matches = list(re.finditer(r"^#include <clang/[^>]+>\n",
                               src, flags=re.MULTILINE))
    if not matches:
        sys.exit("no `#include <clang/...>` line found (step 2)")
    if "clang/Options/OptionUtils.h" not in src:
        pos = matches[-1].end()
        src = src[:pos] + "#include <clang/Options/OptionUtils.h>\n" + src[pos:]

    # --- 3. TextDiagnosticPrinter takes DiagnosticOptions& --------------
    src = src.replace("&c->getDiagnosticOpts()", "c->getDiagnosticOpts()")

    # --- 3b. DiagnosticsEngine ctor: DiagnosticOptions& not pointer -----
    # LLVM 21+ signature:
    #   DiagnosticsEngine(IntrusiveRefCntPtr<DiagnosticIDs> Diags,
    #                     DiagnosticOptions &DiagOpts,
    #                     DiagnosticConsumer *client = nullptr, ...)
    # Mesa 25.0.x still passes `new clang::DiagnosticOptions`, which
    # decays to a pointer. CompilerInstance owns DiagnosticOptions, so
    # reuse its instance instead of allocating a fresh one.
    if "new clang::DiagnosticOptions," in src:
        src = src.replace("new clang::DiagnosticOptions,",
                          "c->getDiagnosticOpts(),")

    # --- 3c. createDiagnostics: LLVM 22 changed the signature -----------
    src, _ = fix_create_diagnostics_llvm22(src)

    # --- 4. TargetOpts is protected; use getTargetOpts() ----------------
    src = src.replace(
        "c->getInvocation().TargetOpts)",
        "c->getInvocation().getTargetOpts())",
    )

    # --- 5. Driver::GetResourcesPath -> clang::GetResourcesPath ---------
    src = src.replace("Driver::GetResourcesPath(", "clang::GetResourcesPath(")

    # --- 6a. lookupTarget(StringRef) short form -------------------------
    short = "auto target = TargetRegistry::lookupTarget(triple, error_msg);"
    if short not in src:
        dump_context(src, "TargetRegistry::lookupTarget")
        sys.exit("short lookupTarget call not found")
    src = src.replace(
        short,
        "llvm::Triple TT(triple);\n"
        "      auto target = TargetRegistry::lookupTarget(TT, error_msg);",
        1,
    )

    # --- 6b. lookupTarget multi-line form -------------------------------
    src = re.sub(
        r'^(\s*)triple, "", "", \{\}, std::nullopt, std::nullopt,',
        r'\1TT, "", "", {}, std::nullopt, std::nullopt,',
        src,
        flags=re.MULTILINE,
    )

    with open(path, "w") as f:
        f.write(src)

    checks = [
        ("getTargetOpts()", True),
        ("clang::GetResourcesPath", True),
        ("clang/Basic/OffloadArch.h", True),
        ("clang/Options/OptionUtils.h", True),
        ("&c->getDiagnosticOpts()", False),
        ("getInvocation().TargetOpts)", False),
        ("TargetRegistry::lookupTarget(triple, error_msg)", False),
        ("TargetRegistry::lookupTarget(TT, error_msg)", True),
        ('TT, "", "", {}, std::nullopt, std::nullopt,', True),
        ("new clang::DiagnosticOptions,", False),
        ("new clang::DiagnosticOptions)", False),
        ("#if LLVM_VERSION_MAJOR >= 22", True),
        ("#endif", True),
    ]
    for needle, want in checks:
        present = needle in src
        if present != want:
            dump_context(src, needle)
            sys.exit(f"sanity check failed: {needle!r} present={present}")

    # Structural check: createDiagnostics call must still be present and
    # wrapped in the LLVM 22 guard.
    marker = "c->createDiagnostics("
    idx = src.find(marker)
    if idx < 0:
        dump_context(src, marker)
        sys.exit("sanity check failed: createDiagnostics call not found")
    look_back = max(0, idx - 200)
    if "#if LLVM_VERSION_MAJOR >= 22" not in src[look_back:idx]:
        dump_context(src, marker)
        sys.exit("sanity check failed: createDiagnostics not wrapped in "
                 "#if LLVM_VERSION_MAJOR >= 22")

    print("OK: clc_helpers.cpp patched for LLVM 22")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        sys.exit("usage: fix_clc_llvm22.py <path-to-clc_helpers.cpp>")
    patch(sys.argv[1])
