# Cloud9 — audit des petits services et tâches récurrentes (26 octobre 2026)

## Périmètre et règle impérative
Audit du host Proxmox, de 14 LXC (12 actifs et 2 arrêtés), des 2 VM avec QGA si disponible, des timers/cron et des healthchecks Docker (environ 165 conteneurs actifs). HAOS ne propose pas son inventaire interne Linux via QGA ; ressources connues depuis PVE. L'audit brut et les arguments de processus ne sont PAS publiés sur GitHub : seul ce rapport sanitisé l'est.

**Ne jamais arrêter une LXC/VM entière pour benchmarker.** CT400 a été involontairement arrêté par une précédente commande asynchrone, redémarré immédiatement à 09h11 et toutes les applications cœur (OmniRoute, Dify, n8n, Open WebUI, MCPProxy, Hindsight, CloakBrowser) ont été revérifiées healthy. Cet incident ne doit jamais se reproduire.

## Nettoyage réel sans arrêt de conteneur

| Emplacement | Pollueur prouvé | Action native appliquée |
|---|---|---|
| Host Cloud9 | Collecteur terminé de réhabilitation ZFS relisant SMART, zpool et journal toutes les 120 s | Timer désactivé, script de récupération conservé ; 720 lectures périodiques/jour supprimées |
| CT300 DaVinci | Ancien PathChanged sur lien de polices déclenchait des dizaines de services/seconde et start-limit-hit | Remplacé par timer systemd toutes les 30 min, même service de mise à jour polices/LUT testé OK |
| Host Cloud9 | Arbitre GPU DaVinci toutes les 5 s | Timer natif passé à 10 s ; même script et priorité GPU, 8640 activations/jour évitées |
| Host (déjà corrigé auparavant) | ZFS collector 5s, operations collector 8s, PBS status15min, post-scrub stage1min | Priorités alignées puis collecteur terminé désactivé, operations30s, PBS3h, post-scrub terminé désactivé |

Timers conservés par nécessité : superviseur et autosleep DaVinci CT300 chaque minute, ComfyUI idle-stop CT410 chaque minute (important pour rendre la VRAM), Hindsight Guides10min CT400 (0,12 seconde CPU au dernier run, aucune tâche de synchronisation en attente). Les scrubs standard/apt et tâches MoneyMatter normales ne justifient pas d'interruption. Services CT410 ComfyUI/Docling en statut failed à diagnostiquer sans occuper le GPU durant une qualification ; CT700 previews transient failed mais des serveurs preview réels tournent. Ne pas arrêter ces composants à l'aveugle.

## Docker Compose : healthchecks anormalement fréquents

| CT | Service | Runtime actuel | Source Compose validée pour prochaine recréation |
|---|---|---|---|
| 110 | NetBox Redis | 1s | 15s |
| 110 | NetBox Redis-cache | 1s | 15s |
| 400 | Dify PostgreSQL | 1s | 15s |
| 300 | DaVinci PostgreSQL | 5s | 15s |

Les fichiers Compose canoniques sont corrigés, syntaxe native validée ; sauvegardes root dans /var/backups/cloud9-compose-20261026 à l'intérieur de chaque CT. **Aucun conteneur DB n'a été redémarré** et leurs intervalles effectifs Docker restent encore à 1s/5s. Après recréations de service ciblées, et seulement alors, économie théorique de 253 440 healthchecks/jour. Les redéployer un par un pendant une fenêtre sans transactions, avec attente de healthy et rollback. Pas de redémarrage de LXC.

## Benchmark sur le VRAI modèle Pym 35B
Atomic TurboQuant 2.0 standard, Pym 35B-A3B Q2 GGUF 13,22GB, contexte 2048, GPU partiel -ngl4 et CPU-MoE41, KV f16, MTP désactivé, 768 tokens, trois prompts :
- Maths 8,974 tok/s, résultat attendu 925 vérifié, réponse visible.
- Code 6,956 tok/s, réponse visible mais tests du code non exécutés.
- Français 8,598 tok/s, réponse visible mais exactitude sémantique non certifiée.
- Chargement serveur 2,516s ; trois réponses sur trois, zéro watchdog.
Hall of Fame mis à jour en catégorie déport partiel. **Ne pas comparer directement à Pym MTP2 GPU complet historique 34,56 médiane / 37,20 maths.**

Essais comparatifs même modèle : upstream MTP2 et sans MTP ont déclenché la protection mémoire PSI, Atomic Zen4/LTO a interrompu ses essais sur pression mémoire, Atom stock192 a été refusé à l'admission dans la dernière fenêtre. Aucun véritable A/B apparié en qualité/vitesse, aucune promotion de production. La charge hôte concurrente varie : une tentative refusée n'est pas une incapacité absolue du moteur.

## Suivi vérifiable
1. Pas d'arrêt LXC/VM pour faire de la place, seules les tâches périodiques inutiles démontrées sont nettoyées.
2. Appliquer les fréquences Compose corrigées seulement via recréation de service ciblée et après vérification d'absence de transactions.
3. Terminer les diagnostics CT410 ComfyUI/Docling et CT700 previews après la fenêtre GPU.
4. Obtenir une fenêtre RAM et PSI réellement stable afin de comparer upstream, Atomic stock, Atomic Zen4/LTO, MTP2 et contexte 8→128K, avec qualité JSON/tools/code ; conserver un seul LLM en production après qualification.
5. Ne pas défaire la politique PBS et les sauvegardes metadata natives déjà corrigées.
6. Avant une nouvelle session, lire CLOUD9_FIVE_PRIORITIES_PBS_MOE_20261026.md et certification/NEXT_HANDOFF.md ; ne pas rejouer de benchmarks déjà enregistrés.

Retours arrière détaillés dans Sources/Worklogs et les miroirs SHA sous certification/evidence/2026-10-26. Aucun fichier Docker Compose complet ou secret n'est partagé sur GitHub.

## 26 Oct — DaVinci quotidien et tournoi MoE 35B
DaVinci CT300: refresh fonts/LUT via timer systemd daily06:15, script de service existant conservé, vérifié actif. Les deux services DaVinci agent/render ont déjà un preflight via ExecStartPre → assets-refresh.sh --prestart AVANT LE DÉMARRAGE DU NŒUD, et non une garantie sur chaque job reçu par un nœud déjà démarré. DaVinci 21 propose un « Trigger script at Start » natif par job/preset, à activer et tester sur le workflow de soumission distant.
Moteur : Pym35B-A3B Q2 identique Atomic2 stock Vulkan partiel -ngl4 cpu-moe41 2048 ctx 192 tokens : MTP2 11.082 / 10.726 / 11.168 tok/s (math/code/fr), math 925 correct, 3 sorties visibles ; MTP3 12.382 / 11.117 / 9.681 tok/s. Moyennes MTP2=10.992, MTP3=11.060, +0.61% MTP3 avec FR nettement plus lent ; MTP2 plus équilibré provisoirement. Pas de test de code exécuté ni 128K, ni vitesse full GPU historique comparable. Upstream b11844 MTP2 à nouveau arrêté par guardian durant load ; Atomic2 MTP1/adaptive refusés préflight IO PSI. Aucun changement de moteur en production. Ne pas arrêter LXC.

## 26 oct. reprise Protocole HOF-first
NE PAS repartir out-of-box : original Atomic1.6 b10269 c044dff24 retrouvé, et trois versions plus récentes. Même GGUF Pym fullGPU MTP2 f16, 8K, b1024/ub1024, poll100/0 avec script tools/qualification/moe_upstream_bakeoff.py et preset atomic16-mtp2-f16-fullgpu. Atomic1.6 3/3 mesures 27,8104/28,0922/23,9433tok/s, Atomic2 maths27,2461tok/s (-2,03%) et watchdog sur les deux autres ; pas encore de verdict moteur. 16K toutes versions sont bloquées par pression mémoire. ARC ZFS a été temporairement réduit à3GiB puis RESTAURÉ. Protocoles et preuves sous certification/PYM_ENGINE_HISTORICAL_FEATURE_PARITY_PROTOCOL.md ; ne jamais éteindre une LXC entière pour benchmarker. Tout gain doit conserver qualité.

## Alerte Vulkan 26 octobre : mode de chargement non-mmap
Parité Pym35B Q2 GPU99 MTP2 f16 testée avec seul changement natif -lm mmap -> -lm none : Atomic1.6 a reçu ErrorDeviceLost dans RADV (« Not enough memory for command submission »), Atomic2 a été refusé avant chargement. **NE PAS RETESTER cette variante sans enquête GPU**, interdiction anticipée native du banc vérifiée par test unitaire. En revanche baseline mmap 8K original Atomic1.6 maths27.8104/code28.0922/FR23.9433 tok/s ; Atomic2 même math27.2461 tok/s puis watchdog mémoire, comparaison finale non résolue. Pas d’arrêt de LXC, ARC ZFS originale4.5GiB restaurée, production saine. Source certification/PYM_ENGINE_HISTORICAL_FEATURE_PARITY_PROTOCOL.md.
