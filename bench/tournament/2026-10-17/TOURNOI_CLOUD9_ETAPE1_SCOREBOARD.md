# Cloud9 — Tournoi Vulkan moteurs IA, phase 1 — 17 octobre 2026

**But** : filtrer vitesse et qualité agentique AVANT l'exploration du contexte maximal propre à chaque modèle. **Aucun candidat production-ready**.

Protocole : CT700 Radeon 780M RADV Vulkan, ctx alloué 8K, mêmes poids GGUF et SHA dans l'A/B moteurs, KV F16/F16, FlashAttention ON, 0 speculation, 3 répétitions par scénario, température 0, outils en lecture seule, refroidissement entre requêtes pour les séries complètes.

| Modèle / quant | Moteur / template | JSON | Calendrier outil | Code JSON exact | Latence outil | Decode outil | État |
|---|---|---:|---:|---:|---:|---:|---|
| Qwen3.5-4B-Qwen3.8-Distill-Heretic-MTP-Q4_K_M.gguf | atomic-dev 3cde9e4, GGUF | 3/3 | 3/3 | 0/3 | 3.302 s | 22.43 tok/s | complete |
| Qwen3.5-4B-Qwen3.8-Distill-Heretic-MTP-Q4_K_M.gguf | atomic-2.0, GGUF | 3/3 | 3/3 | 0/3 | 3.303 s | 22.29 tok/s | complete |
| Agents-A1-4B-Q4_K_M.gguf | llama-oct17, GGUF | 3/3 | 3/3 | 0/3 | 2.926 s | 22.34 tok/s | complete |
| Qwen3.5-4B-Qwen3.8-Distill-Heretic-MTP-Q4_K_M.gguf | llama-oct17, GGUF | 3/3 | 3/3 | 0/3 | 2.403 s | 22.13 tok/s | complete |
| Qwen3.5-4B-Qwen3.8-Distill-Heretic-MTP-Q4_K_M.gguf | llama-oct17, GGUF | 3/3 | 3/3 | 0/3 | 2.430 s | 22.07 tok/s | interrupted_by_host_thermal_watchdog |
| Qwen3.5-4B-Qwen3.8-Distill-Heretic-MTP-Q4_K_M.gguf | llama-oct17, GGUF | — | — | 0/3 | — | — | complete |
| Qwen3.8-9B-Distill-Heretic-Uncensored-MTP-Q4_K_M.gguf | llama-oct17, GGUF | 1/1 | 1/1 | — | 3.920 s | 13.35 tok/s | error |
| Sharp-Spark-X2.5-4B-Q6_K_XL.gguf | llama-oct17, GGUF | 3/3 | 0/3 | 0/3 | 0.858 s | 19.28 tok/s | complete |
| Sharp-Spark-X2.5-4B-Q6_K_XL.gguf | llama-oct17, jinja officiel | 3/3 | 0/3 | 0/3 | 0.859 s | 19.15 tok/s | complete |

## Décisions provisoires (n'ajouter AUCUN alias production)

- **À poids exactement identiques sur Qwen 4B** : upstream llama.cpp 9d1878a améliore la latence des outils (2,403 s médiane vs 3,303 s Atomic 2.0) et le prefill des outils (387,82 vs 210,66 tok/s). Decode voisin (~22 tok/s). Même qualité limitée **6/9** : JSON 3/3 et outils 3/3, mais correction de code sous JSON strict 0/3. Cela **ne démontre pas** que le même moteur gagne sur d'autres familles ou à long contexte.
- **Agents-A1-4B Q4_K_M** : outil 3/3, JSON 3/3, code exact 0/3, délai outil 2,926s ; ne supplante pas Qwen 4B sur ce banc. 262144 tokens annoncés par sa fiche HF, PAS testés ici.
- **Sharp-Spark 4B Q6_K_XL** : outil 0/3 avec le template GGUF puis 0/3 avec le template Jinja officiel exact SHA vérifié ; le message renvoie simplement le nom d'outil. Code exact 0/3, JSON 3/3, ~19 tok/s. Rejet du rôle agent général dans cette configuration, malgré la promesse upstream.
- **Qwen3.8-9B Q4_K_M** : deux premières requêtes réussies ~13 tok/s, puis impossible de descendre sous 69,5°C à chaud pour la troisième (seuil prudent du banc, pas la limite thermique matérielle) ; série INCOMPLÈTE. Pas de jugement final sur ses aptitudes mais vitesse inférieure au repère interactif.
- **JSON Schema natif avec Qwen4B** : 3/3 réponses JSON valides mais **0/3 contenu correct** pour le champ `corrected_line`. La grammaire ne suffit pas pour raisonner juste.
- Un premier banc **non refroidi** upstream 4B avait 11/14 requêtes correctes avant arrêt à 80,4°C ; son quinzième cas manquant reste explicitement NON TESTÉ. Ne pas fusionner cet échantillon avec le protocole refroidi.

## Suite

1. Tester les modèles experts mieux adaptés au code/outils et des MoE rapides (Pym 35B-A3B et Gemma4 26B-A4B issus des historiques), uniquement après admission RAM/GTT/température. Poursuivre le choix des quatre modèles handpicked ; Qwen 4B est seulement un candidat outil.
2. Comparer upstream llama/Atomic nouvelles branches et Strata sur même GGUF lorsque familles réellement prises en charge ; préserver erreurs/skips, templates source et SHA.
3. Seulement après filtre qualité/rapidité, mesurer le **contexte maximum utile par modèle** à 32K/64K/128K/**256K, 512K, 1M+ si applicable**, à 5 positions et sur outils; noter rupture/cadence/GTT et plusieurs agents. Ne pas remplacer par une seule allocation -c.
4. Tester architecture OmniRoute Local → runtime(s) gagnant(s), alternative directe/Lemonade/vLLM uniquement si gains prouvés sur gfx1103, vrais clients Hermes, n8n, Dify, Paperclip.

## Artefacts

- `atomic-2.0-Qwen3.5-4B-Qwen3.8-Disti-agentic-cool69.json` : complete, 9 réponses recueillies
- `llama-oct17-Agents-A1-4B-Q4_K_M-agentic-cool69.json` : complete, 9 réponses recueillies
- `llama-oct17-Qwen3.5-4B-Qwen3.8-Disti-agentic-cool69.json` : complete, 9 réponses recueillies
- `llama-oct17-Qwen3.5-4B-Qwen3.8-Disti-all.json` : interrupted_by_host_thermal_watchdog, 14 réponses recueillies
- `llama-oct17-Qwen3.5-4B-Qwen3.8-Disti-code_schema-cool69-schema.json` : complete, 3 réponses recueillies
- `llama-oct17-Qwen3.8-9B-Distill-Heret-agentic-cool69.json` : error, 2 réponses recueillies
- `llama-oct17-Sharp-Spark-X2.5-4B-Q6_K-agentic-cool69.json` : complete, 9 réponses recueillies
- `llama-oct17-Sharp-Spark-X2.5-4B-Q6_K-agentic-sharp-template.json` : complete, 9 réponses recueillies
