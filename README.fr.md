<p align="center"><img src="docs/assets/logo.svg" width="132" alt="Logo Cloud9 Engine"></p>
<h1 align="center">Cloud9 Engine</h1>
<p align="center"><strong>Un runtime llama.cpp adaptatif et optimisé pour AMD RDNA. On mesure d'abord, on promeut ensuite.</strong></p>
<p align="center"><a href="README.md">English</a> · <a href="README.fr.md">Français</a> · <a href="README.zh-CN.md">简体中文</a></p>

Cloud9 Engine est un runtime local pour AMD RDNA + Vulkan. Il suit **llama.cpp upstream** et **Atomic TurboQuant**, ajoute les optimisations Cloud9 encore absentes de l'upstream, autotune les paramètres RADV sur la machine réelle, puis ne promeut qu'un build qui passe les gates de correction et de performance.

## ☁️ Pourquoi Cloud9 Engine ?
- **Kernel Vulkan RDNA réellement optimisé** : une tuile `MUL_MAT_ID` 128×32 accélère le prefill des modèles MoE sur Phoenix/Hawk Point RDNA3 UMA.
- **Autotuning hardware** : batch/ubatch, polling, FlashAttention et placement mémoire sont choisis à partir de mesures RDNA, sans écraser tes flags explicites.
- **TurboQuant sur un llama.cpp récent** : TQ2/TQ3/TQ4 KV, `SET_ROWS` Vulkan, FlashAttention et benchmark plumbing restent disponibles sur l'upstream actuel.
- **Deux backends, une seule commande** : upstream+Cloud9 est le choix actuel ; Atomic reste suivi comme fallback et donor de features.
- **Mises à jour sans roulette russe** : chaque update devient candidate et doit repasser le gate hardware avant production.

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
Le mode `auto` utilise le backend élu par le gate local. Sur la Radeon 780M de référence, **upstream + Cloud9** gagne actuellement en général et en MTP. Atomic peut toujours être forcé avec `CLOUD9_ENGINE_BACKEND=atomic`.

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
GitHub surveille llama.cpp et Atomic, ouvre une mise à jour de `sources.lock`, CI vérifie que les patchs s'appliquent et compilent, puis le serveur reconstruit des candidats. **La production n'est promue qu'après le gate hardware.**

Voir aussi : [architecture](docs/architecture.md), [benchmarks](docs/benchmarks.md), [installation](docs/installation.md) et [procédure d'update](docs/updates.md).

## 📄 Licence
Les scripts et docs originaux Cloud9 Engine sont sous licence MIT. Les moteurs upstream conservent leurs licences respectives.
