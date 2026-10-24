# Moteurs IA - selection pour les agents locaux, 24 octobre 2026

Ce sont des candidats existants pour routage natif CT410 vers OmniRoute, PAS une nouvelle configuration de production.

| Tache | Modele | Vitesse historique du catalogue | Restriction |
| --- | --- | --- | --- |
| Extraction rapide | Cloud9-MiniCPM5-2B-DSpark | 47.73 t/s | validation vrais outils manquante |
| JSON, outils | Cloud9-Qwen3.8-4B-Heretic | 25.81 t/s | qualite agentique robuste non certifiee |
| Raisonnement complexe | Cloud9-Pym-35B-A3B-MTP | 30.87 t/s | non-uncensored; contexte 8K; GPU exclusif |
| Raisonnement uncensored | Cloud9-Qwen3.6-35B-A3B-Heretic | 10.29 t/s long contexte ancien | verification outils manquante |
| Candidat 9B | Qwen3.8-9B Heretic | 14 t/s pour autre quant historique | non expose sur routeur; correction de code 0/3 |
| Candidat Flash-Next | GSQ-RCO IQ1_M | 5.96 t/s autre prototype historique | 58GB de GGUF, plafond generique 40GiB |

Le routeur actuel ne charge qu'un seul worker LLM GPU; plusieurs agents changeant de modele peuvent subir la latence de rechargement. Sous forte pression swap/RAM/GTT, le gardien GPU interdit les tests; la validation ponctuelle de 4GiB ne constitue pas une certification de fiabilite.

Le script audit_current_router.py est EN LECTURE SEULE : catalogue, modeles, binaires, REST /health et /v1/models et arbitre GPU. Aucune inference, aucun changement de service, de sauvegarde ou de production.

Gates restants: vraie qualite JSON/outils/agentique, 8K-16K, concurrence, sans preemption de l'engine embeddings, compatibilite OmniRoute/Dify/n8n, chimere GPU testee, rollback.
