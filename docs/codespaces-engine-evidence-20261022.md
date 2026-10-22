# Cloud9 Radeon 780M — candidats reproductibles, 22 octobre 2026

## Règles immuables
GitHub Codespace Harbor, espace isolé `/workspaces/.cloud9-engines-20261022`, uniquement pour builds/qualifications sans GPU. Accès Cloud9 exclusivement **SentinelX**, sans Remote Desktop Commander. Pas d'installation de pilote ni de noyau sur Cloud9 ou ses LXC. Aucun arrêt PBS/CT400/CT410, aucune réduction des seuils de sécurité ou promotion production. Le GPU Radeon 780M gfx1103 n'existe **pas** dans Codespaces : tous les tests d'inférence GPU y sont matériellement impossibles.

## Magnitude 0.2.10 (20 octobre)
- Git source exact `magnitudedev/magnitude`, release `@magnitudedev/cli@0.2.10`, commit `940e51bd3c16b4b98935d04e855fe8685031ae90`.
- `cargo check --locked -p magnitude-service-server -p magnitude-engine-cli -j2` **PASS**.
- Tests `magnitude-family-qwen35 --test interpretation` **13/13 PASS**.
- Tests `magnitude-generation --test generation` **46/46 PASS** (transactions de décodage MTP).
- Analyse en-tête du GGUF **réel** de Cloud9 `Qwen3.6-35B-A3B-Pym-Q2-MTP.gguf` : 13 222 476 000 octets locaux, version GGUF 3, 753 tenseurs, architecture `qwen35moe`, `block_count=41`, `nextn_predict_layers=1`, contexte **annoncé** 262144 (pas prouvé exploitable).
- Seules les métadonnées de ce fichier (96 253 octets, SHA-256 `2e559ac0b829cbe3880cbeebc5d2041c05d5275b1eb827a47d0f0a4fd9c4f4fd`) ont été copiées vers Codespaces. Aucun poids GGUF, aucun secret, aucune donnée d'utilisateur transférés. Test Rust `cloud9_pym_header_20261022.rs` : **1/1 PASS**, reconnaît le modèle MoE et sa couche MTP.
- Build debug service et CLI **PASS** ; SHA-256 `magnitude-inference` debug `463363b9eb811419878116208603a94a5c383c6210d6d15c6a0b54fca31f969a` et CLI debug `ff9bd505c5f097e47424bdda89050b798dcc8a3e9e53252599841d4b8357008e`.
- Build Release **`magnitude-engine` PASS**, SHA-256 `70a18a1fc909490cf7930bbee4d33e7f512b2f17401e0784c101d77166cd5ac8`, et commande `--help` PASS ; option native `--method mtp --mtp-proposals N --device vulkan --context-tokens N`.
- **PAS encore prouvé** : chargement complet du Pym 13,2Go, GPU Vulkan 780M, taux accepté MTP, JSON/outils, vitesse et contexte effectivement utile. Le build Release n'est pas une mesure de latence.
- Fichiers binaires et journal uniquement dans Codespace ; pour conserver à long terme la reproductibilité, les sources/SHAs/docs/tests dans la branche GitHub Cloud9-engine, ne pas mettre un binaire volumineux sous contrôle Git.

## Strata 0.2.2, HIP gfx1103
- Source amont exact `Niko1221/Strata`, tag `v0.2.2`, SHA `011c9e600a93bbc9fd451c563501b5831c32bbca`. Les cinq commutateurs Radeon780M du profil automatique `STRATA_IGPU_PROMPT_SET` sont présents.
- Test C++ sans GPU `src/core/arch_defaults_test.cpp`, compilé dans Codespaces `g++ -std=c++20` : **PASS** ; préremplissage WMMA gfx1103 sélectionné, n'affecte pas les GPU discrets ; ne mesure aucun tok/s.
- Branche Cloud9 existante `GodsQuantum/Strata` `lab/cloud9-gfx1103-qwen35-mtp2-20261022` SHA `11bdbc30e61fd28e18fd1fb64ad87c591b1e7d41` (ancienne base v0.1.45, optimisation bulk MTP). CPU CI du 22 octobre **PASS**, MTP2 GPU non prouvé.
- ROCm HIP10.1 est nécessaire pour compiler réellement gfx1103 ; Codespace Ubuntu24.04 dispose d'un dépôt ROCm officiel AMD. Seuls outils AMD dans espace isolé, **aucun** kernel, driver, DKMS ou upgrade libc. Si le compilateur portable ne fonctionne pas, le statut reste BLOCKED_TOOLCHAIN, pas PASS.

## llama.cpp, référence mesurée
- Qwen3.6-35B Pym Q2 MTP avec Cloud9 llama.cpp stable : **30,87 tokens/s historique** (protocole différent). Ce n'est pas une démonstration de supériorité globale ni de contexte >8K.
- Même petit GGUF Qwen3.8-4B Heretic IQ4 XS sur RADV 780M, 3 répétitions, PP64/TG16 : b11798 **460,68 / 22,47 tok/s** ; S1 **421,86 / 20,26** ; variante b11798+Phoenix RDNA3 compilée avec succès, mesure GPU en attente. Ne pas comparer ces mesures courtes au Qwen35 MTP.

## Conditions mémoire mesurées et décisions
Le 22 octobre vers **03:05 Europe/Paris**, CT410 garde officiel `CHECK exclusive 14.5` REFUSED : GTT sûrs disponibles **7,496 GiB**. `CHECK coexist-light 8.0` REFUSED : **7,491 GiB**. RAM hôte disponible environ 25,15GiB, swap ~11,57GiB utilisé, réserve hôte 18GiB, CT410 limité à 64GiB par cgroup, autres services (embedding, Speaches, etc.) intacts. Le benchmark Qwen35 requiert au moins 14,5GiB de budget sûr et ne doit **pas** être déclenché tant que le garde refuse. « Un seul moteur LLM » libère de la mémoire de façon opérationnelle uniquement si les autres consommateurs n'en ont plus besoin ; cela ne transforme pas la totalité des 96Go physiques en GTT libre à cet instant.

## Qualification attendue (aucun duel MTP OFF inutile)
1. Couple moteur+modèle+quant SHA + MTP effectif, draft accepté mesuré (Strata, Magnitude, llama.cpp).
2. Qualité : JSON, tools réels en mode simulé sans side-effect, code, français. Le temps jusqu'à la bonne action compte davantage que TPS isolé.
3. Prefill multi-tailles, génération soutenue TG128, TTFT, mémoire/GTT, Tctl, stabilité.
4. Contexte utile **réellement ingéré** et rappel multi-position, 8K→16K→32K→64K→128K→plus haut si sûr ; contexte indiqué dans GGUF (`262144`) ne prouve pas 262K utile.
5. Un seul serveur LLM résident expérimental par essai ; accès agent via OmniRoute seulement après qualification et rollback.
6. Scoreur `tools/single_engine_rank.py` + `tests/single_engine_rank_test.py` : **8/8 tests unitaires PASS**, preuve insuffisante => refuse de déclarer gagnant ; comparer une frontière de Pareto, puis choisir un seul runtime avec plusieurs modèles interchangeables.

**Statut final de ce document : candidats Codespace qualifiés partiellement, aucun nouveau champion GPU certifié, production inchangée.**
