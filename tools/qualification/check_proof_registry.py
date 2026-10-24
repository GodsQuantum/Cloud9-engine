#!/usr/bin/env python3
"""Validate proof SHA, statuses and deterministic generated handoff. No runtime access."""
import argparse
import hashlib
import json
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
REGISTRY = REPO / "certification/certification_registry.json"
SUMMARY = REPO / "certification/CURRENT_STATUS.md"
HANDOFF = REPO / "certification/NEXT_HANDOFF.md"
STATES = {"HISTORICAL_VALID", "CURRENT_PASS_LIMITED", "PARTIAL", "BLOCKED_RESOURCE", "NOT_RUN"}

def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()

def validate(data, project=None):
    assert data["schema_version"] == 1
    gates = data["gates"]
    ids = [g["id"] for g in gates]
    assert ids == ["C%02d" % i for i in range(1, len(ids)+1)]
    assert len(ids) == len(set(ids))
    for g in gates:
        assert g["status"] in STATES
        assert g["title"] and g["scope"] and g["remaining"] and g["acceptance"]
        if g["status"] in ("HISTORICAL_VALID", "CURRENT_PASS_LIMITED"):
            assert len(g["evidence"]) > 0, g["id"] + " has no sources"
        for e in g["evidence"]:
            rel = Path(e["project_path"])
            assert not rel.is_absolute() and ".." not in rel.parts
            assert e["note"]
            assert len(e["sha256"]) == 64
            int(e["sha256"],16)
            if project is not None:
                path=project/rel
                assert path.is_file(), "Missing: " + str(path)
                assert sha(path) == e["sha256"], "Historic/attached proof changed: " + str(path)
    for k in ("minimum_production_path","full_product_path","historic_proofs_not_current_build_certification"):
        assert all(v in ids for v in data[k]),k
    assert set(data["minimum_production_path"]).issubset(data["full_product_path"])
    assert not set(data["historic_proofs_not_current_build_certification"]) & set(data["full_product_path"])

def render_status(d):
    parts=["# Cloud9 Engine - matrice canonique de certification", "",
      "Date du registre: "+d["as_of"], "",
      "Moteur disponible sur demande: "+d["engine_current_id"],
      "",
      "Historique valide != validation du nouveau binaire. C01-C03 ne doivent pas être rejoués sur leurs anciens exécutables.",
      "",
      "| ID | Résultat exact | État | Nouvelle étape requise |",
      "|---|---|---|---|"]
    for g in d["gates"]:
        parts.append("| "+g["id"]+" | "+g["title"].replace("|","/")+" | "+g["status"]+
                     " | "+g["remaining"].replace("|","/")+" |")
    parts.extend(["",
      "## Voie production minimale, modèle local Qwen4", "",
      ", ".join(d["minimum_production_path"]), "",
      "## Voie produit complet, plusieurs modèles dont FlashNext", "",
      ", ".join(d["full_product_path"]), "",
      "## Preuves numériques à conserver", ""])
    for g in d["gates"]:
        if g.get("measured"):
            parts.append("- "+g["id"]+": "+json.dumps(g["measured"],ensure_ascii=False,sort_keys=True))
    parts.extend(["","## Interdictions de fausse certification","",
      "- Compilation et tests de kernels ne valent pas inférence sur GPU avec les poids actuels.",
      "- 2K ne prouve ni 8K ni 16K; les succès Atomic 8K/16K conservent leurs propres hashes.",
      "- Ne jamais réécrire un ancien benchmark avec les nouveaux nombres.",
      "- Le gardien GPU et le verrou restent obligatoires; pas de pause PBS, swapoff, reboot automatique ou arrêt VoiceStudio.",
      "- Tout changement de code/champs de configuration exige une vérification des gates affectés; ne refaire que ces gates.",
      ""])
    return "\n".join(parts)

def render_handoff(d):
    gates={g["id"]:g for g in d["gates"]}
    parts=["# Handoff automatique Cloud9 Engine", "",
     "Registre mis à jour: "+d["as_of"], "",
     "Moteur disponible: "+d["engine_current_id"],"",
     "SHA routeur: "+d["engine_current_sha256"],"SHA catalogue: "+d["catalog_sha256"],
     "Maintenir les combos OmniRoute actuels. Ne pas promouvoir ce LAB en défaut avant les gates restants.",
     "","## Certifié dans sa portée et A NE PAS REFAIRE",""]
    for g in d["gates"]:
        if g["status"] in ("HISTORICAL_VALID","CURRENT_PASS_LIMITED"):
            parts.append("- "+g["id"]+" ("+g["status"]+") "+g["title"]+": "+g["scope"])
    parts.extend(["","## Restant et ordonné",""])
    for id in d["full_product_path"]:
        g=gates[id]
        parts.append("- "+id+" ("+g["status"]+") "+g["remaining"]+". Réussite: "+g["acceptance"])
    parts.extend(["","## Règle de reprise future","",
      "1. Lire certification_registry.json + CURRENT_STATUS.md, puis HALL_OF_FAME.json dans le projet Cloud9.",
      "2. Vérifier les fichiers de preuve SHA256 si l'accès SentinelX au projet est disponible.",
      "3. Ne jamais recommencer C01/C02/C03 sur l'ancien runtime: fixtures historiques réutilisables.",
      "4. Après tout changement touchant au moteur/benchmark/router: mettre à jour le JSON, régénérer ces deux documents, committer et pousser. GitHub Actions vérifie qu'ils concordent.",
      "5. Ne pas annoncer 36 tests, 128K ni FlashNext >20 tok/s avant les nouveaux résultats.",
      ""])
    return "\n".join(parts)

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--check",action="store_true")
    ap.add_argument("--project-root")
    a=ap.parse_args()
    d=json.loads(REGISTRY.read_text())
    validate(d,Path(a.project_root).resolve() if a.project_root else None)
    for p,txt in [(SUMMARY,render_status(d)),(HANDOFF,render_handoff(d))]:
        if a.check:
            assert p.exists() and p.read_text() == txt, str(p)+" stale; run without --check"
        else:
            p.write_text(txt)
    print("CERTIFICATION_OK",len(d["gates"]),"gates","check",a.check,"project_shas",bool(a.project_root))

if __name__=="__main__":
    main()
