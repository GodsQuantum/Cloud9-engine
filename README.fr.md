<p align="center"><img src="docs/assets/logo.svg" width="132" alt="Logo Cloud9 Engine"></p>
<h1 align="center">Cloud9 Engine</h1>
<p align="center"><strong>Un runtime llama.cpp adaptatif et optimisé pour AMD RDNA. On mesure d'abord, on promeut ensuite.</strong></p>
<p align="center"><a href="README.md">English</a> · <a href="README.fr.md">Français</a> · <a href="README.zh-CN.md">简体中文</a></p>

Cloud9 Engine est un runtime local pour AMD RDNA + Vulkan. La production repose sur **llama.cpp upstream + les optimisations Cloud9**, avec plusieurs révisions upstream validées conservées lorsque des familles de modèles différentes gagnent sur des commits différents. **Prism** sert uniquement aux modèles ternaires/PTQ. **Atomic TurboQuant** reste suivi en laboratoire/donor, mais n'est jamais sélectionné automatiquement sur la Radeon 780M de référence après les erreurs Vulkan reproduites avec Atomic 1.7.

## ☁️ Pourquoi Cloud9 Engine ?
- **Kernel Vulkan RDNA réellement optimisé** : une tuile `MUL_MAT_ID` 128×32 accélère le prefill des modèles MoE sur Phoenix/Hawk Point RDNA3 UMA.
- **Autotuning hardware** : batch/ubatch, polling, FlashAttention et placement mémoire sont choisis à partir de mesures RDNA, sans écraser tes flags explicites.
- **Union des features sans verrouillage sur un fork** : le runtime récent conserve les nouveautés llama.cpp tandis que des révisions upstream plus rapides peuvent rester sélectionnées pour certaines familles.
- **Une seule API, plusieurs runtimes internes** : le routeur choisit `upstream-pym`, `upstream-fast`, `upstream-next`, `upstream-latest` ou Prism selon le modèle. Atomic reste laboratoire uniquement sur la 780M.
- **Mises à jour sans roulette russe** : chaque update devient candidate et doit repasser le gate hardware avant production.
- **Fusible modèles géants** : les fichiers modèle >40 Gio sont refusés par défaut sur la 780M de référence après qu'un smoke Flash-Next a saturé le GTT ; un override explicite de laboratoire est requis.
- **Multi-machine prêt pour USB4/LAN** : les builds upstream Cloud9 incluent le backend RPC de llama.cpp. Un second nœud peut lancer `cloud9-engine rpc-worker`; le coordinateur utilise `layer` par défaut et n'active `tensor` qu'explicitement après benchmark. Le worker reste bindé sur loopback tant qu'un accès privé distant n'est pas explicitement autorisé.

## ⚡ Installation rapide
```bash
git clone https://github.com/GodsQuantum/cloud9-engine.git
cd cloud9-engine
./scripts/install.sh
cloud9-engine doctor
cloud9-engine build
cloud9-engine gate /chemin/vers/modele.gguf
cloud9-llama-server -m /chemin/vers/modele.gguf -ngl 99 -c 32768
```

## 🧠 Routage et profils
Le trafic de production passe par `cloud9-model-router`, qui choisit pour chaque modèle le runtime, le contexte et le profil MTP/DSpark validés. Le wrapper direct garde un mode `auto` dont le fallback générique est `upstream-fast`. Atomic ne peut être utilisé que par override explicite de laboratoire (`CLOUD9_ENGINE_BACKEND=atomic`).

Le profil RDNA `balanced` est injecté uniquement sur AMD/RADV et uniquement pour les options non précisées par l'utilisateur. Pour un workload d'ingestion massif : `CLOUD9_ENGINE_RDNA_PROFILE=prefill`. Pour désactiver tout tuning : `CLOUD9_ENGINE_RDNA_TUNING=off`.

## 📊 Mesures Radeon 780M
Plateforme de référence : Ryzen 7 8845HS / Radeon 780M RADV, Qwen3.6-35B-A3B Pym Q2 + MTP2, 16 septembre 2026. Ce ne sont **pas** des promesses universelles.

| Test | Avant → Cloud9 | Gain |
|---|---:|---:|
| MTP 3×256, Atomic tuné → Cloud9 tuné | 32,99 → **34,40 t/s** | **+4,3 %** |
| MoE pp512, A/B inverse 5 runs | 342,4 → **362,5 t/s** | **+5,9 %** |
| MoE pp2048, A/B inverse 5 runs | 378,8 → **391,6 t/s** | **+3,4 %** |
| MoE pp512, profil chat production | 337,1 → **397,5 t/s** | **+17,9 %** |

Le kernel passe **921/921 tests `MUL_MAT_ID` Vulkan** et le decode seul reste neutre (22,50 → 22,63 t/s). Détails : [benchmarks](docs/benchmarks.md).

## 🔄 Politique d'update
GitHub surveille llama.cpp, Atomic et Prism. Une nouvelle révision reste candidate tant que le patchset déclaré, la compilation Vulkan et les gates matériels/modèles n'ont pas passé. **Aucun refresh de source ne remplace directement un runtime connu comme bon.**

Voir aussi : [architecture](docs/architecture.md), [benchmarks](docs/benchmarks.md), [installation](docs/installation.md), [multi-machine](docs/distributed.md) et [procédure d'update](docs/updates.md).

## 📄 Licence
Les scripts et docs originaux Cloud9 Engine sont sous licence MIT. Les moteurs upstream conservent leurs licences respectives.
