# Cloud9 Engine — audit historique, accélération et calendrier de jalons

Date: 25 octobre 2026. État = un moteur Qwen 4B optionnel utilisable, PAS encore la release par défaut de tous les agents.

## Le plus court chemin, sans redo

**Version Qwen4 production restreinte = six gates C08, C09, C10, C11, C14 et C15.**
- C11: stabiliser RAM/swap, I/O/PBS, admission GPU sans reboot ni préemption des services.
- C08: sur la chimère ACTUELLE, réutiliser les fixtures cinq aiguilles Atomic déjà certifiées pour mesurer contexte effectivement absorbé 8K puis 16K; aller 32K/64K/128K et plus selon hardware, sans cap arbitraire.
- C09: jouer les 12 scénarios agentiques existants x3, JSON strict, code patch, risques d'outils, FR. Ne pas recréer les fixtures.
- C10: charge client 1/2/4 et une file unique, temps avant premier token, p95, tokens/s, contention GPU et résilience sous erreur.
- C14: tests réels OmniRoute + Dify + n8n + Paperclip (lecture seule), permissions par profils; ne pas reconfigurer d'emblée les combos stables.
- C15: canary, surveillance, rollback automatique et promotion de la release si toutes les étapes vérifiées.

**Moteur universel complet = huit gates C08–C15.** Deux de plus: C12 véritable TurboQuant KV GPU + A/B strict MTP/MMB versus upstream; C13 quatre modèles role-qualifiés y compris FlashNext >20tok/s (historique 17.878 tok/s).

## Ne jamais recommencer ces preuves historiques
- Ancien Cloud9 Vulkan MUL_MAT_ID: 921/921 tests kernel, noyau version ancienne, PAS preuve 921/921 du moteur actuel.
- Atomic TurboQuant 2.0.0: 8K avec 8026 tokens réellement préremplis et cinq aiguilles 3/3; 16K avec 16330 tokens et cinq aiguilles 3/3. JSON et journaux originaux vérifiés avec SHA.
- 17 octobre: duel upstream/Atomic sur le MÊME GGUF; inutile de refaire à l'identique.
- 23 octobre: duel véritable HIP/Vulkan et watchdog; conserver même les échecs pour éviter de choisir une combinaison déjà défaite.
- 24 octobre: compilations CPU/Vulkan/HIP, tests numériques, gardien GPU, routeur safe et 202 tests Python sur code courant. Un pass CI code n'est PAS un pass GPU modèle.
- 25 octobre: chimère opt-in 33.7565tok/s en appel d'outil 32 tokens; MiniCPM5 Heretic+DSpark mesuré 22.1551tok/s sur 137 tokens. Ces nouveaux résultats viennent d'être ajoutés au HALL_OF_FAME unique: 188->190 records.

## Recherche Web 25/10/2026 et décision d'accélération

1. llama.cpp SPEED-Bench: opère directement sur un serveur OpenAI déjà démarré; sélection des catégories coding/rag/reasoning et petit --limit, JSON résultats; compare baseline vs speculative MTP avec speed_bench_compare.py. PAS de rebuild moteur pour comparer deux réglages. https://github.com/ggml-org/llama.cpp/blob/master/tools/server/bench/speed-bench/README.md
2. llama-bench officiel: comparaison A/B 3 répétitions, prompt/decode/contexte, moyenne écart-type, JSON. Ne juge pas la sûreté des outils ni la qualité FR. https://github.com/ggml-org/llama.cpp/blob/master/tools/llama-bench/README.md
3. Tests serveur llama.cpp sous pytest: exécuter uniquement modules HTTP JSON/chat/function calling pertinents au lieu de reconstruire toute la suite de tests à chaque patch. https://github.com/ggml-org/llama.cpp/blob/master/tools/server/tests/README.md
4. GuideLLM: évaluer vraie latence p95, TTFT, ITL, concurrence 1/2/4, à partir de la même API HTTP OpenAI, sans simuler 100 utilisateurs sur une iGPU. Article daté 22/10/2026: https://developers.redhat.com/articles/2026/10/22/local-inference-and-benchmarking-red-hat-ai-inference ; https://github.com/vllm-project/guidellm/blob/main/docs/getting-started/benchmark.md
5. BFCL v4: réutiliser catégories refus et outils multi-tour mais ne pas exécuter naïvement 5000+ exemples. Audit indépendant du 10 septembre 2026 a repéré des problèmes dans 24 des 50 échantillons analysés. https://epoch.ai/benchmarks/berkeley-function-calling-leaderboard/review ; https://gorilla.cs.berkeley.edu/leaderboard
6. llama-server natif: dispose déjà du continuous batching, slots, endpoints OpenAI, prompts contraints et mesures. Ne pas ajouter un deuxième proxy. Le mode routeur natif n'est à considérer qu'après vérification de la sécurité GPU et de la non-préemption actuelle. https://github.com/ggml-org/llama.cpp/blob/master/tools/server/README.md
7. OpenZFS ARC: réglage zfs_arc_max dynamique mais non immédiatement libérateur de RAM; à mesurer sous I/O réelles avant persistance de 4.5GiB. https://openzfs.github.io/openzfs-docs/Performance%20and%20Tuning/Module%20Parameters.html
8. GitHub required status checks: rendre la CI de registre obligatoire via ruleset si nécessaire; CI seule détecte mais n'interdit pas un merge contournant les checks. https://github.com/github/docs/blob/main/content/repositories/configuring-branches-and-merges-in-your-repository/managing-rulesets/available-rules-for-rulesets.md

## Timeline observée: dates prouvées par commits, pas promesses

| Date et jalon | Avant | Gain net prouvé |
|---|---|---|
| 16 septembre | idée d'amélioration RDNA3 | noyau MUL_MAT_ID correct 921/921, ancien binaire |
| 17 septembre | moteur de production local | version MTP et premiers benchmarks GPU |
| 13 octobre | résultats dispersés | Hall of Fame unique et historique |
| 17 octobre | forks concurrents non triés | duel upstream/Atomic Qwen4 mêmes poids, tests outils |
| 22 octobre | manque de preuve de long contexte | Atomic Qwen4 8K et 16K cinq aiguilles 3/3, record FlashNext historisé |
| 23 octobre | nouveaux forks sans vraie QA | appariement HIP/Vulkan, décisions fail-closed sans perturber services |
| 24 octobre 01:46–15:38 | branches MMB/MTP/Turbo distinctes | chimère code native compilée CPU/HIP/Vulkan + tests numériques |
| 24 octobre 19:38–22:40 | OmniRoute / GPU admission fragiles | garde officiel, correctif nonpréemption et 182->194 tests |
| 24 octobre 23:07–23:22 | GPU partagé trop exclusif | reconnaissance VoiceStudio/AutoSubs inactifs, outils natifs sans appels parallèles, 200 tests |
| 24 octobre 23:31–23:58 | pas d'inférence de la chimère | premier Qwen4 Vulkan 26–34 tok/s, OpenBMB ~22.16 tok/s |
| 25 octobre 00:02 | chimère n'est que LAB séparé | modèle optionnel routé sur CT410, 9 entrées, 33.76 tok/s outil strict |
| 25 octobre audit | HOF bloqué à 188 | 190 preuves, 15 gates, SHA, CI d'intégrité + handoff généré |

La source Git ne permet PAS d'attribuer chaque commit au mot exact «continue» d'un message utilisateur. Ce sont des jalons datés. La valeur d'un prochain cycle se mesure par gate complet et preuves SHA, pas par le nombre de recompilations.

## Projection par cycles de travail, pas promesse d'échéance

- Voie restreinte Qwen4: 6 gates restant, certains déjà préparés et groupables. Ordre conseillé C11 puis C08/C09, C10, C14/C15. Nombre indicatif 3 à 5 cycles de validation SI gardien GPU stable. Toute pression mémoire peut bloquer plusieurs cycles.
- Voie moteur complet FlashNext/Turbo/4 rôles: deux gates lourds de plus dont vitesses et qualité encore inconnues. Aucune date certaine.
- Ne jamais appeler le produit 15/15 uniquement parce que 202 tests Python passent; chaque gate a sa portée et son critère.

## Anti-redondance pérenne

HALL_OF_FAME.json dans le dossier projet est le classement canonique unique; il possède 190 enregistrements.
Le registre Git versionné certification/certification_registry.json décrit l'état de release actuel avec la portée exacte, les preuves SHA et les étapes restantes.
Les fichiers CURRENT_STATUS.md et NEXT_HANDOFF.md sont produits déterministiquement depuis le registre par tools/qualification/check_proof_registry.py. La CI certification-ledger.yml exécute la vérification à chaque push lab ou PR et exige un handoff actualisé avec les changements de code moteur.
Pour chaque reprise: lire le registre, vérifier les SHA des preuves existantes et ne tester que les gates NON validés ou invalidés par un changement identifié.
