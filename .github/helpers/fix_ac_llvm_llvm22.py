#!/usr/bin/env python3
"""Fix Mesa src/amd/llvm/ac_llvm_helper.cpp for LLVM 22.

LLVM 22's Module::setTargetTriple takes Triple, not StringRef.
Mesa 25.0.x passes TM->getTargetTriple().getTriple() (a std::string),
which no longer converts implicitly.
"""
import sys

OLD = "unwrap(module)->setTargetTriple(TM->getTargetTriple().getTriple());"
NEW = "unwrap(module)->setTargetTriple(TM->getTargetTriple());"


def patch(path):
    with open(path) as f:
        src = f.read()

    if NEW in src and OLD not in src:
        print("OK: ac_llvm_helper.cpp already patched")
        return

    if OLD not in src:
        sys.exit(f"anchor not found in {path}: {OLD!r}")

    src = src.replace(OLD, NEW)

    with open(path, "w") as f:
        f.write(src)

    if OLD in src or NEW not in src:
        sys.exit("sanity check failed after replacement")

    print("OK: ac_llvm_helper.cpp patched for LLVM 22")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        sys.exit("usage: fix_ac_llvm_llvm22.py <path-to-ac_llvm_helper.cpp>")
    patch(sys.argv[1])
