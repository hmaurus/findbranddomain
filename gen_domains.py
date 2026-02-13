#!/usr/bin/env python3
"""
Gera lista expandida de domínios candidatos a partir de prefixos e termos,
incluindo plurais e variações.
"""

import sys

# Prefixos a testar (AI, AIs, AIx, etc.)
PREFIXES = ["ai", "ais", "aix", "aie", "aio"]

# Sufixos opcionais para depois do termo
SUFFIXES_AFTER = ["", "s", "x", "z", "ly", "fy", "er", "ed", "io", "app", "ai"]

# Termos base
TERMS = [
    "central", "hub", "flow", "docs", "lib", "kit", "space", "play", "studio",
    "guide", "workflow", "workbench", "handbook", "start", "manual", "man",
    "book", "reference", "zone", "learn", "center", "core", "stack", "engine",
    "map", "build", "nexus", "forge", "craft", "sphere", "state", "mind",
    "brain", "stream", "academy", "school", "base", "mentor", "campus", "path",
    "next", "trail", "courses", "portal", "gateway", "node", "dock", "lab",
    "arena", "vault", "archive", "library", "toolbox", "toolkit", "framework",
    "blueprint", "roadmap", "pipeline", "factory", "atelier", "workshop",
    "terminal", "console", "board", "panel", "deck", "grid", "matrix",
    "network", "cluster", "cloud", "domain", "realm", "field", "universe",
    "ecosystem", "platform", "system", "module", "suite", "package", "bundle",
    "collection", "catalog", "index", "compass", "track", "route", "journey",
    "launch", "kickoff", "prime", "spark", "ignite", "pulse", "drive",
    "motion", "orbit", "axis", "channel", "circuit", "command", "cockpit",
    "bridge", "station", "outpost", "stronghold", "foundation", "ground",
    "root", "source", "origin", "seed", "alpha", "beta", "depot", "harbor",
    "junction", "lattice", "fabric", "structure", "layer", "tier", "codex",
    "digest", "primer", "playbook", "compendium", "anthology", "script",
    "canvas", "hangar", "refinery", "foundry", "powerhouse", "insight",
    "mainframe", "backbone",
    # Termos curtos/branding
    "ly", "fy", "go", "up", "on", "pro", "max", "run", "box", "fox", "ops",
    "tap", "pin", "pop", "top", "bit", "byte", "net", "web", "dev", "gen",
    "bot", "pal", "ace", "zen", "way", "one", "now", "try", "do", "so",
    "me", "my", "us", "we", "to", "it", "at", "by",
    # Termos compostos curtos
    "wire", "wise", "ware", "work", "wave", "link", "line", "lite", "list",
    "loop", "loom", "lens", "grip", "glow", "crew", "cue", "clip", "chip",
    "cape", "cave", "cove", "den", "dex", "duo", "elm", "flo", "flux",
    "fold", "fort", "fuse", "hive", "hook", "isle", "jam", "jet", "key",
    "knot", "loft", "mark", "mesh", "mint", "muse", "nest", "nook", "note",
    "pact", "peak", "pier", "pod", "pool", "port", "rack", "rift", "ring",
    "rune", "saga", "sail", "scan", "shelf", "shift", "sign", "silk", "snap",
    "sync", "tale", "tone", "tune", "turn", "twin", "vibe", "vine", "warp",
    "yard", "yoke",
]

def generate():
    seen = set()
    domains = []

    for prefix in PREFIXES:
        for term in TERMS:
            # prefix + term: aiguide, aisguide
            d = f"{prefix}{term}.com"
            if d not in seen:
                seen.add(d)
                domains.append(d)

            # prefix + term + s (plural): aiguides, aisguides
            if not term.endswith("s"):
                d = f"{prefix}{term}s.com"
                if d not in seen:
                    seen.add(d)
                    domains.append(d)

            # prefix + hyphen + term: ai-guide
            d = f"{prefix}-{term}.com"
            if d not in seen:
                seen.add(d)
                domains.append(d)

    # Também: term + ai, term + ais, term-ai, term-ais
    for suffix in ["ai", "ais"]:
        for term in TERMS:
            d = f"{term}{suffix}.com"
            if d not in seen:
                seen.add(d)
                domains.append(d)

            d = f"{term}-{suffix}.com"
            if d not in seen:
                seen.add(d)
                domains.append(d)

            # plural do termo
            if not term.endswith("s"):
                d = f"{term}s{suffix}.com"
                if d not in seen:
                    seen.add(d)
                    domains.append(d)

                d = f"{term}s-{suffix}.com"
                if d not in seen:
                    seen.add(d)
                    domains.append(d)

    return domains


if __name__ == "__main__":
    domains = generate()
    for d in domains:
        print(d)
    print(f"# Total: {len(domains)} domínios", file=sys.stderr)
