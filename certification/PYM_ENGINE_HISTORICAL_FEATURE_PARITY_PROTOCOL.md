# Pym 35B : reprise des meilleurs paramètres AVANT tuning

Règle : On ne recommence pas par les valeurs out-of-box à chaque version moteur. Les paramètres du précédent gagnant sont portés avant le premier A/B.

## Historique prouvé
- Atomic 1.6 du 11 septembre : Pym 35B Q2, MTP2, f16 KV, 36,28 tok/s. Binaire original c044dff24 toujours exécutable en CT410. La CLI historique complète n'est pas enregistrée.
- Cloud9 Vulkan du 14 septembre : médiane MTP2 34,56 tok/s, pic maths 37,20 tok/s ; CLI historique incomplète.
- Upstream du 2 octobre : même GGUF et 5 runs, médiane 30,49 tok/s avec serveur full GPU -ngl99, contexte16384, t8/tb8, b/ub1024, mmap, polling100/0, KVf16, Flash Attention et inline MTP2. Toutes ces options figurent dans la preuve de lancement.

## Phase 0 : comparer les moteurs avec les mêmes features
Preset logiciel atom16-mtp2-f16-fullgpu (nom exact : atomic16-mtp2-f16-fullgpu) dans tools/qualification/moe_upstream_bakeoff.py. Candidats : Atomic 1.6 original, Atomic 1.7, Atomic 2, Atomic 2 Zen4/LTO, upstream b11844.

Identité modèle : /srv/lxc/ia-compute/data/models/qwen36-pym-q2-mtp/Qwen3.6-35B-A3B-Pym-Q2-MTP.gguf, 13 222 476 000 octets.
Fixés : 99 couches GPU, CPU MoE off, 16384 contexte, batch1024, microbatch1024, threads8, f16 KV, MTP2, spéculation p-min0 et backend-sampling désactivé, polling100/0, mmap, FlashAttention on, prompt cache off, 192 tokens, seed42 et prompts strictement identiques.

SEULE différence de surface : --lazy-mode off explicite sur upstream, non disponible sur Atomic. Équivalence effective à vérifier. Il s'agit d'une RECONSTRUCTION PARITAIRE basée sur les données préservées, pas d'une prétention que chaque flag Atomic1.6 de septembre est connu.

Gardien officiel14GTT, verrou GPU et watchdog NON contournés. Aucun LXC stoppé. Trois réponses correctes minimum, puis trois répétitions dans conditions de charge équivalentes. Un démarrage refusé par RAM/PSI n'est PAS une mesure de débit ni une défaite d'un moteur.

## Phase 1 : optimiser uniquement après la première vraie mesure
Après un gagnant sur le même modèle et avec les mêmes features : ablation unitaire de MTP1/2/3/adaptive, KV f16/q8/turbo3/turbo4, batch/ubatch, cache MoE, Vulkan, polling, offload et contextes 8→128K. Transférer aux concurrents les meilleures fonctionnalités qui existent uniquement dans un moteur, sans prétendre comparer si le portage n'est pas identique.

Qualification obligatoire : sorties finales correctes, Python réellement exécuté, JSON strict et tool use, stabilité, p95, latence prefill/decode, températures, 128K réel, canary et rollback avant promotion. Aucun petit 4B ou LFM ne remplace Pym35B dans ce classement.

Machine-readable manifest et SHA de chacun des cinq binaires dans Sources/Worklogs/2026-10-26_PYM35B_HISTORICAL_FEATURE_PARITY_MANIFEST.json.

## Résultat matériel 26 octobre : première comparaison paritaire réussie en 8K
Le même code de bench et le même GGUF Pym Q2 13,222,476,000 octets ont servi à tester le binaire Atomic1.6 c044dff24 et Atomic2 cda0f92 **GPU99, CPU-MoE0, MTP2, KV f16, contexte 8192, b/ub1024, t8, poll100/0**. Le profil 16K exact d’octobre a été refusé au chargement des deux candidats à cause de PSI mémoire. En 8K avec cache ZFS ARC temporairement plafonné à3GiB puis **restauré à 4,5GiB**, Atomic1.6 original obtient **27,8104 maths / 28,0922 code / 23,9433 français tok/s, 3 sorties visibles sur3, math correcte**. Atomic2 a produit **27,2461 tok/s sur maths, math correcte**, puis son watchdog officiel a arrêté l’exécution avant code/FR à PSI mémoire1,83 et MemAvailable23,367GiB. Sur ce seul prompt, Atomic2 est **2,03% plus lent que 1.6** ; il n’y a PAS encore de verdict global entre moteurs, ni d’équivalence quantitative aux records de septembre : contexte et prompts différents. Aucun LXC/VM ni moteur de prod arrêté.

Fiche de verdict Source de vérité : Sources/Worklogs/2026-10-26_PYM35B_FULL_GPU_FEATURE_MATCHED_AB_CURRENT_VERDICT.json ; logs bruts des deux comparateurs joints dans certification/evidence/2026-10-26/. **Reprendre une fenêtre de RAM disponible réelle pour finir code/FR Atomic2 avec le même preset**, puis seulement tester les nouveaux tweaks. Ne pas dépasser le gardien GPU ni supprimer les sauvegardes.

### Hypothèse de performance upstream à vérifier séparément
Il existe un signalement récent sur un écart de vitesse Vulkan MTP v0.7 vs v0.6 (issue ggml-org/llama.cpp #30688 : https://github.com/ggml-org/llama.cpp/issues/30688). **Ne pas imputer les performances locales à ce bug sans reproduction** et ne pas appliquer de revert non testé. À investiguer après l’A/B Atomic1.6→Atomic2.

## Native load-mode ablation — STOP sur erreur GPU
26 octobre, unique paramètre modifié à l’identique sur Atomic1.6 et Atomic2 : -lm mmap vers -lm none. Atomic1.6 chargeant le vrai Pym fullGPU8K a échoué en RADV avec « Not enough memory for command submission » puis « vk::Queue::submit: ErrorDeviceLost », sans réponse. Atomic2 a été refusé par son précontrôle avant de charger, donc AUCUN verdict de débit non-mmap. Les embeddings et routeur sont restés actifs ; ZFS ARC max rétabli. Le banc refuse désormais cette variante avant chargement pour Pym fullGPU sur Radeon780M. Ne pas relancer automatiquement ; garder mmap comme référence historique.
