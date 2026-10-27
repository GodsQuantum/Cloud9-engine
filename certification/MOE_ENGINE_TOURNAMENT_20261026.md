# Cloud9 — Tournoi MoE sur Radeon 780M (26 octobre 2026)

Objectif : choisir le moteur optimal pour Pym 35B-A3B et Flash-Next, puis optimiser le gagnant sans perte de qualité ni de fiabilité. Jamais de remplacement par un 4B/8B comme « benchmark décisif ».

## Cibles et preuves
1. Pym Qwen3.6-35B-A3B Q2 MTP, GGUF local de 13 222 476 000 octets. Ancien meilleur MTP2 : 34,56 tok/s médiane, 37,20 sur maths. Ancien Atomic 1.6 Vulkan : 36,28 tok/s MTP2 KV f16. Le modèle a été chargé récemment en configuration GPU partielle mais la pression mémoire a interrompu toute inférence.
2. Pym Heretic APEX-I-Compact MTP, GGUF local de 17 016 624 544 octets : CHALLENGER DE QUALITÉ. Une différence entre ce modèle et Pym Q2 ne doit jamais être présentée comme un gain de moteur.
3. Flash-Next historique AD-4.27 + draft FR-Spec Q8, record 17,878 tok/s avec moteur Vulkan modifié 53f34cfaa b10738, MTP3, TurboQuant, SET_ROWS, FlashAttention, CPU-WHT et fusion GDN OFF. Ces GGUF exacts ne sont plus disponibles localement dans le catalogue examiné. Variante GSQ-RCO IQ1_M Coder de 58,4 Go présente, mais autre famille de quantification ; **ne jamais substituer dans le même leaderboard**.
4. Nouvelles variantes agentiques/Heretic/Nemotron/GLM/Gemma après le choix de moteur sur Pym et Flash, chacune avec son propre SHA et sa propre grille qualité.

## Protocole expérimental

**À chaque fois le même GGUF / mêmes hashes / prompts / context / sampler / threads / température / seed / quantification.** Un seul paramètre change par A/B, une seule inférence LAB en cours, verrou GPU et gardien officiel. L'historique réussi n'est pas rejoué pour remplir un compteur.

Étape 0 : préserver preuves HALL_OF_FAME, SHAs des binaires, headers GGUF, archives de tests et releases existantes. Distinguer upstream pur, fork, config custom, build CPU/GPU et tests perdus. Contrôler également slots embeddings à 192.168.1.219:8091, AutoSubs, Proxmox, PBS, RAM, swap et PSI.

Étape 1 : Pym exact, moteur upstream b11844 et Atomic2 b10298-2.0.0. 8K réel, baseline FA+f16, puis MTP2 avec same GGUF/seed. MTP3 uniquement après MTP2, car MTP2 était meilleur historiquement. 3x jeux maths/code/prose/raisonnement avec décodage et réponse finale. Mesures startup à froid, débit et prefill à chaud, temps de la réponse finale, MTP acceptance, p95, MB mémoire et erreur watchdog.

Étape 2 : **transfert de fonctionnalités entre moteurs**. Toute fonction accélérant un moteur est testée sur tous les moteurs compatibles. Si absent, rechercher et réaliser un portage dans une branche LAB indépendante avec QA et comparaison sur le même GGUF. Statut explicite unavailable si portage non viable ou dépendance architecturale. Jamais de score fictif.

Étape 3 : ablations dans cet ordre : MTP0/1/2/3 et MTP-adaptive Atomic; KV f16, q8, puis turbo3/turbo4 Atomic (l'ancien Atomic 1.6 Pym MTP2 f16 = 36,28 vs turbo3 = 34,40, donc Turbo3 PAS optimal présumé) ; microbatch 128/256/512/1024; poll100/batch0; cache experts MoE seulement si CPU experts et contraintes de mémoire; CPU-WHT, Vulkan SET_ROWS et async seulement lorsqu'implémentation effective vérifiée; GDN fusion ON uniquement en laboratoire si QA et tests de corruption réussis. Éviter RADV nogttspill qui a historiquement fait régresser Pym. Garder les 2 ou 3 meilleures combinaisons, puis les vérifier sur des seeds distincts pour éviter le sur-ajustement.

Étape 4 : agentique strict : JSON valide et sans fences, sélection outils/arguments sûrs C09 (36 cas), code exécuté et testé, raisonnement, FR, cinq marqueurs exacts en 8K, 16K, 32K, 64K, **128K réellement ingérés**. Meta GGUF 262K ne vaut pas test 128K. Toute sortie vide, perte de marqueur, hallucination, erreur native ou watchdog disqualifie la configuration pour la production.

Étape 5 : Flash-Next avec **même** ancien couple AD-4.27/FR-Spec s'il est retrouvé/recréé et validé. Baseline sans draft, puis MTP2/3, et mêmes fonctionnalités (CPU WHT, SET_ROWS, TurboQuant, GDN OFF) sur upstream, Atomic et fork Cloud9. Toute nouvelle quantification = nouvelle catégorie distincte. Si format Strata incompatible, ne pas lui attribuer zéro tok/s : indisponible.

Étape 6 : Atomic 2 optimisé. Version stock cda0f925 conservée intacte. Nouvelle variante Zen4/LTO native Vulkan compilée séparément en CT700, sans mise en service. Avant tout tuning noyau, comparer stock vs Zen4/LTO **sur Pym**, et vérifier que GGML_NATIVE était déjà actif : n'annoncer aucun gain avant mesure. Ensuite seulement isoler un tweak Vulkan prouvé, propre à gfx1103, sans changement global RADV ni du routeur productif.

Étape 7 : deux championnats, moteur chaud en agent continu et moteur chargé à la demande. À qualité égale, privilégier temps global et contexte réellement viable, pas seulement TG. Canary 24 heures, rollback prêt, puis OmniRoute/Dify/n8n/Paperclip; conserver le combo stable jusqu'à validation.

## Features cross-engine

| Fonction | llama.cpp upstream Vulkan | Atomic TurboQuant 2 Vulkan | Politique |
|---|---|---|---|
| draft MTP1/2/3 | natif | natif | MTP2 historique gagnant Pym |
| MTP adaptatif | absent dans aide b11844 | natif | A/B Atomic ; port upstream seulement si gain |
| FA, KV f16/q8, microbatch, polling | natif | natif | strictement mêmes options |
| KV turbo3/4 | absent | natif | qualité d'abord, puis port upstream si avantage établi |
| Cache experts MoE | natif upstream | non visible dans aide Atomic | utile seulement avec experts CPU; ancien cache Pym perdant |
| Placement complet experts GPU | natif | natif | contrôle, pas de comparaison faussée par CPU |
| CPU-WHT / SET_ROWS / Vulkan async | auditer code réel | auditer code réel | expérimenter uniquement si prouvé |
| GDN cache fusion | selon fork | selon fork | OFF par défaut, ancien risque de corruption |
| Zen4 / LTO | contrôle sans modification | variante LAB isolée | ne pas présumer gain GPU |

## Règles de sûreté et de score

- Pas de préemption des embeddings actifs, arrêt PBS/HAOS, reboot, swapoff ni baisse du gardien.
- Zéro réponse visible = zéro réussite qualité même si les tokens/s sont élevés.
- Sont requis : réponse correcte, outils sûrs, JSON strict, code validé, marqueurs exacts à contexte promis, répétitions et rollback.
- Un benchmark rejeté par la pression hôte = non-admis, jamais une défaite du moteur.
- GitHub, source et preuve SHA du projet actualisés après chaque étape, sans écraser les essais passés.

## État réel constaté le 26 octobre

CPU Ryzen 7 PRO 8845HS Zen4, iGPU Radeon 780M gfx1103, Mesa RADV 26.0.8, RAM installée 96 Go, souvent 24–27 GiB disponibles et swap ~17 Gio ; quatre slots embeddings occupés simultanément, PBS I/O concurrente. Pym 13,22 Go chargé en GPU partiel mais arrêté au watchdog avant génération ; full GPU 8K non-admis. LFM2.5 8B-A1B ne fait pas partie du verdict. Le correctif routeur des embeddings est en production et vérifié. Aucune promotion de moteur sans vrais essais cibles.

## Implémentation Atomic2 LAB validée après rédaction du plan
La variante Zen4/LTO du code source identique cda0f925 est maintenant compilée, copiée en CT410 LAB et ses 11 ELF sont corrigés nativement avec RUNPATH $ORIGIN. Version, aide MTP adaptatif et toutes les bibliothèques dynamiques validées. Aucun modèle Pym/Flash n’a été chargé avec ce binaire et aucun gain de débit/qualité n’est démontré. Voir la preuve SHAs 2026-10-26_ATOMIC2_ZEN4_LTO_NATIVE_BUILD_STAGED_410.json. La production utilise toujours ses binaires inchangés.
