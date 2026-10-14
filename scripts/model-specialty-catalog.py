#!/usr/bin/env python3
"""Stable, evidence-grounded Cloud9 model names; never change canonical IDs.

Run --check in CI. Default mode updates both versioned catalog files in CT700.
"""
import argparse
import json
from pathlib import Path

# Label = editorial specialty demonstrated/selected in the five-role HOF, not a claim of superior quality.
SPECIALTIES = {
    "Cloud9-MiniCPM5-2B-DSpark": ("Titres et extraction rapide", "Titres-Extraction"),
    "Cloud9-Ling3-Tiny-Uncensored": ("Rédaction courte", "Redaction-Courte"),
    "Cloud9-LFM2.5-2.6B-Uncensored": ("Conversation légère", "Conversation-Legere"),
    "Cloud9-Qwen3.8-4B-Heretic": ("JSON structuré et outils", "JSON-Outils"),
    "Cloud9-Pym-35B-A3B-MTP": ("Raisonnement complexe", "Raisonnement-Complexe"),
    "Cloud9-Qwen3.6-35B-A3B-Heretic": ("Agents et consignes longues", "Agents-Consignes"),
    "Cloud9-Gemma4-26B-A4B-MTP": ("Écriture créative", "Ecriture-Creative"),
    "Cloud9-Bonsai2-27B-Ternary-Abliterated": ("Rédaction libre", "Redaction-Libre"),
}


def decorate(data):
    """Pure transformation; preserves eight IDs, quantizations, weights and backend routes."""
    models = data["models"]
    ids = [model["id"] for model in models]
    if len(ids) != 8 or set(ids) != set(SPECIALTIES) or len(set(ids)) != 8:
        raise ValueError("Refusing outdated/incompatible model catalog")
    data = json.loads(json.dumps(data, ensure_ascii=False))
    seen = set()
    for model in data["models"]:
        specialty, slug = SPECIALTIES[model["id"]]
        display_name = f'{model["id"]} — {specialty}'
        alias = f'{model["id"]}--{slug}'
        model["specialty"] = specialty
        model["display_name"] = display_name
        aliases = list(model.get("aliases", []))
        if alias not in aliases:
            aliases.append(alias)
        model["aliases"] = aliases
        for name in (model["id"], *aliases):
            if name.casefold() in seen:
                raise ValueError("Colliding model alias: " + name)
            seen.add(name.casefold())
    data["updated_at"] = "2026-10-14"
    return data


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    for filename in ("config/model-catalog.json", "config/model-catalog.example.json"):
        path = root / filename
        original = json.loads(path.read_text(encoding="utf-8"))
        desired = decorate(original)
        if args.check:
            if original != desired:
                raise SystemExit(f"INVALID: {filename}")
            print(f"PASS: {filename}, {len(desired['models'])} canonical model IDs preserved")
        else:
            path.write_text(json.dumps(desired, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
            print(f"UPDATED: {filename}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
