Make.com — scénario (vue d'ensemble)

Déclencheur (quotidien, 07:00) ->
1) Générer 5–20 idées de requêtes long-tail (combinaison d'attributs) OU lire une table Notion 'Ideas' (statut=À faire).
2) Pour chaque idée:
   a) Appeler l'API HF Inference (ou l'LLM de votre choix) avec `prompts/article_prompt.txt`.
   b) Recevoir: SUMMARY, META_DESC, AFFILIATE_LINKS, HTML_CONTENT.
   c) Créer/mettre à jour un fichier `data/articles.csv` via GitHub API (append row).
3) (Optionnel) Créer un post Buffer/Twitter avec le titre et le lien.
4) (Optionnel) Envoyer 1 brouillon à Brevo si un seuil de qualité n'est pas atteint (contrôle humain).

Astuce: commencez à 5 pages/jour; augmentez si indexation/qualité OK.
