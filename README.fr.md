<p align="center"><img src="docs/assets/logo.svg" width="132" alt="Logo Cloud9 Engine"></p>
<h1 align="center">Cloud9 Engine</h1>
<p align="center"><strong>Un runtime llama.cpp adaptatif pour AMD RDNA. On mesure d'abord, on promeut ensuite.</strong></p>
<p align="center"><a href="README.md">English</a> · <a href="README.fr.md">Français</a> · <a href="README.zh-CN.md">简体中文</a></p>

Cloud9 Engine est une petite couche de contrôle pour faire tourner des LLM locaux sur GPU AMD RDNA via Vulkan. Au lieu de dépendre éternellement d'un seul fork, il suit **llama.cpp upstream** et **Atomic TurboQuant**, compile les deux, ajoute les patchs Cloud9 RDNA encore absents de l'upstream, puis laisse la machine réelle décider quel backend mérite la production.

## ☁️ Pourquoi ?
- **Deux bons moteurs, une seule entrée stable** : upstream récent pour les nouveautés modèles/Vulkan, Atomic pour les chemins TurboQuant et spéculatifs matures.
- **Validation RDNA réelle** : la plateforme de référence utilise Radeon 780M / RADV, pas CUDA.
- **Promotion contrôlée par le hardware** : une update reste candidate tant qu'elle n'a pas chargé un vrai modèle et passé le benchmark local.
- **Mises à jour suivies automatiquement** : les nouveautés upstream deviennent des PR testées, jamais un `git pull` silencieux en production.
- **Commande compatible llama-server** : `cloud9-llama-server` choisit le backend promu puis transmet les arguments normalement.

## ⚡ Installation rapide
```bash
git clone https://github.com/GodsQuantum/cloud9-engine.git
cd cloud9-engine
./scripts/install.sh
cloud9-engine doctor
cloud9-engine build
cloud9-engine gate /chemin/vers/modele.gguf
cloud9-llama-server -m /chemin/vers/modele.gguf -ngl 99 -c 32768 -fa on
```

## 🧠 Routage
En mode `auto`, le build **upstream + Cloud9** sert de moteur général pour bénéficier des nouveautés llama.cpp. Les requêtes MTP/NextN peuvent utiliser **Atomic** lorsqu'il est meilleur sur le benchmark local. On peut toujours forcer `CLOUD9_ENGINE_BACKEND=upstream` ou `atomic`.

## 📊 Pourquoi ne pas garder seulement Atomic ?
Le 16 septembre 2026 sur Radeon 780M, Atomic gagnait notre test long MTP (~33,26 t/s), alors que le code upstream récent gagnait très nettement en prefill Vulkan (~335 t/s avec les patchs Cloud9 contre ~301 t/s Atomic). Il n'y avait donc pas un gagnant universel. Cloud9 Engine transforme cette réalité en fonctionnalité au lieu de la masquer.

## 🔄 Politique d'update
GitHub surveille llama.cpp et Atomic, ouvre une mise à jour de `sources.lock`, CI vérifie que les patchs s'appliquent et compilent, puis le serveur local reconstruit des candidats. **La production n'est promue qu'après le gate hardware.**

Voir aussi : [architecture](docs/architecture.md), [benchmarks](docs/benchmarks.md), [installation](docs/installation.md) et [procédure d'update](docs/updates.md).

## 📄 Licence
Les scripts et docs originaux Cloud9 Engine sont sous licence MIT. Les moteurs upstream conservent leurs licences respectives.
