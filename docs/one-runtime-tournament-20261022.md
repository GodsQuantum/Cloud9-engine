# Cloud9 — moteur unique, modèles interchangeables (LAB, 22 octobre 2026)

Objectif: un seul moteur résident à la fois, pouvant servir plusieurs modèles selon usage via OmniRoute, pas trois moteurs permanents. Choisir qualité des actions, vitesse de génération et délai de première action correcte, puis contexte vraiment utile. La RAM hôte 96 Gio n'est pas de la VRAM supplémentaire: la limite CT410 et les services protégés restent des contraintes réelles.

Couples à qualifier: llama.cpp Cloud9 stable + Qwen3.6-35B Pym Q2 MTP (référence ~30,87 tok/s historique); Strata 0.2.2 + Qwen3.6-35B Q2 ou Flash-Next compatible et MTP, avec le profil des 5 noyaux Radeon780M; Magnitude 0.2.10 + Qwen3.6-35B Q2 et décodage MTP natif. Garder Gemma4 26B-A4B MTP et Qwen3.8-4B/9B comme candidats de repli si ils sont réellement meilleurs sur la qualité ou la latence. Pas de téléchargement massif automatique.

Pas de duel inutile MTP désactivé/activé: chaque candidat doit activer son meilleur chemin spéculatif supporté, et prouver un vrai taux de tokens draft acceptés. Les mesures native llama-bench/strata bench/Magnitude sont des preuves de débit, pas de qualité; la qualité doit être évaluée sur requêtes identiques d'outils, JSON, code et français, et le contexte sur plusieurs aiguilles aléatoires, avec tokens réellement ingérés.

Protocole minimal: au moins trois répétitions, GGUF SHA identique si comparaison des moteurs sur un même modèle, outils et JSON corrects, prefill, TG128 avec MTP, TTFT, temps jusqu'à la bonne action, contexte 8K puis 16K/32K/64K/128K et au-delà si admissible, cinq positions d'aiguilles, température, GPU/GTT, RAM et PSI. Une fenêtre 128K allouée sans 128K de tokens réellement ingérés et bien rappelés n'est pas un succès. Les GGUF différents sont des couples modèle-moteur distincts, non une preuve d'efficacité intrinsèque du moteur.

Exploiter tools/single_engine_rank.py en lui fournissant un JSON version 1 avec des preuves signées/citées de chaque couple. Le scoreur ne lance aucun serveur, n'utilise pas le GPU et refuse tout vainqueur en absence de MTP, de qualité, de contexte, ou de sécurité vérifiés. La frontière de Pareto n'est pas une autorisation de déploiement.

Cloud9 22 octobre 02:14: CPU ~75,5 C, mémoire disponible ~25 Gio, PSI non nul et PBS actif. Ne pas lancer d'essai GPU sous ces conditions. Compiler, vérifier les modèles supportés et préparer les tests dans Codespaces, sans toucher au routeur CT410. Promotion après garde officiel, watchdog, rollback et validation des clients OmniRoute.
