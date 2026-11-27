# Pistes d'amélioration

Ce document porte un regard critique sur l'application. On y regarde **deux choses** :

1. **Les réponses sont-elles justes ?** → c'est la **qualité** (partie 1).
2. **L'utilisateur attend-il trop longtemps ?** → c'est la **fluidité** (partie 2).

Chaque piste suit le même plan : **le problème**, **un exemple** (vu ou mesuré), **la solution**, et **comment vérifier** que l'amélioration fonctionne.

## Partie 1 : la qualité des réponses

### 1. L'IA ajoute des informations qui ne viennent pas des articles

**Le problème.** Les articles cités sont fiables : ils viennent de World News API, avec leur titre, leur date et leur lien. Mais dans les parties qu'elle écrit elle-même (« Synthèse », « Points clés »), l'IA ajoute parfois des chiffres, des dates ou des liens de cause à effet qui ne sont dans aucun article. L'utilisateur ne peut pas faire la différence.

**Un exemple.**

- Le 24/11/2026, dans une réponse sur les passoires thermiques, l'IA a écrit : « 9,54 milliards d'euros retirés du Livret A en 2026, reflétant une crise du pouvoir d'achat et des difficultés à investir dans la rénovation. » Ce chiffre n'est dans aucun des articles cités, et le lien avec la rénovation est inventé. Dans la même liste, l'autre chiffre (« 17,1 % des ménages d'Occitanie ») venait bien d'un article.
- Le 19/11/2026, l'IA a écrit que la location des logements classés G serait interdite en 2028 et celle des F en 2034. Le vrai calendrier de la loi Climat et Résilience est : G en 2025, F en 2028, E en 2034.

**La solution.** Donner une **sortie structurée** à l'agent du chat quand il présente des articles, comme pour la revue de presse : une liste d'articles d'un côté, et une synthèse qui ne peut s'appuyer que sur ces articles. Le frontend affiche alors clairement ce qui vient des sources.

**Les fichiers à modifier.**

- `schemas.py` : créer un nouveau formulaire pour les réponses du chat, avec le texte de la réponse et la liste des articles (en réutilisant `ArticleSummary`, déjà créé pour la revue).
- `agent.py` : `chat_agent` utilise ce formulaire (`output_type`), et le prompt précise que le texte ne doit utiliser que les articles de la liste.
- `routes/chat_routes.py` : renvoyer au frontend le texte et les articles séparément.
- `components/ChatWindow.js` : afficher le texte dans la bulle, et les articles dans des cartes en dessous (comme dans la page des revues).
- Pour vérifier : un nouveau fichier avec les 20 questions de test, et `tests/test_chats.py` à adapter.

**Comment vérifier.** Préparer 20 questions de test et relancer ces questions à chaque modification : objectif **0 chiffre ou date absent des articles**, contrôlé à la main ou par un second LLM « juge ».

## Partie 2 : la fluidité (le temps d'attente)

On a d'abord mesuré combien de temps l'utilisateur attend. Ces mesures servent ensuite d'exemples pour les pistes 2 à 4.

### Les mesures

Mesures faites le 24/11/2026 sur l'application en ligne (Vercel + Railway), avec l'onglet **Réseau** des outils du navigateur (touche F12), dans une seule discussion qui s'allonge.

| Action | Temps |
|---|---|
| Relire une discussion enregistrée (sans IA) | environ 0,2 s |
| Message 1 : « Quelles sont les principales actualités d'aujourd'hui ? » | 7,16 s |
| Message 2 : approfondir les passoires thermiques (avec recherche d'articles) | 11,14 s |
| Message 3 : articles sur MaPrimeRénov' | 10,63 s |
| Message 4 : rénovation des copropriétés | 12,16 s |
| Message 5 : aides pour les propriétaires bailleurs | 16,78 s |
| Revue de presse générée après 2 échanges | **8,52 s** |
| Revue de presse générée après 5 échanges | **15,40 s** |

Ce que montrent ces mesures :

- presque tout le temps d'attente vient du **LLM** : relire une discussion prend 0,2 s, obtenir une réponse de l'IA prend 7 à 17 s ;
- une **recherche d'articles** ajoute environ 4 secondes (l'IA appelle World News API, puis écrit sa réponse) ;
- **plus la discussion est longue, plus c'est lent**, pour les messages comme pour les revues : à chaque appel, on envoie au LLM tout l'historique, qui grossit ;
- le temps moyen de génération d'une revue est d'environ **12 secondes** (8,5 s et 15,4 s). Ce n'est **pas satisfaisant** : au-delà de quelques secondes, l'utilisateur ne sait pas si l'application fonctionne encore.

Les pistes ci-dessous proposent une solution pour chacun de ces problèmes.


### 2. Afficher la réponse au fur et à mesure (streaming)

**Le problème.** L'utilisateur voit « L'IA réfléchit… » jusqu'à ce que la réponse soit entièrement écrite. La plupart des applications de chat affichent la réponse pendant qu'elle s'écrit.

**Un exemple.** Une question simple fait attendre **7 secondes** ; une question avec recherche, **11 à 17 secondes**, sans rien voir apparaître.

**La solution.**

1. Backend : utiliser le streaming de PydanticAI (`chat_agent.run_stream`) dans la route `POST /chats/{chat_id}/messages`, et renvoyer la réponse morceau par morceau avec une `StreamingResponse` de FastAPI.
2. Frontend : lire la réponse au fur et à mesure avec `fetch`, et ajouter chaque morceau dans la bulle de l'IA.
3. Enregistrer l'historique dans la base une fois la réponse terminée.

**Les fichiers à modifier.**

- `routes/chat_routes.py` : la route des messages utilise `chat_agent.run_stream` et renvoie une `StreamingResponse`.
- `lib/api.js` : une version d'`apiFetch` qui lit la réponse au fur et à mesure.
- `components/ChatWindow.js` : la bulle de l'IA se remplit morceau par morceau.

**Comment vérifier.** Le premier mot s'affiche en **moins de 2 secondes** après l'envoi du message.

### 3. Accélérer la génération des revues de presse

**Le problème.** La revue de presse prend en moyenne **12 secondes**, et elle ralentit quand la discussion s'allonge, car l'agent reçoit **toute la discussion** : les questions, les longues réponses de l'IA et tous les articles.

**Un exemple.** **8,52 s** après 2 échanges, **15,40 s** après 5 échanges : presque **2 fois plus**.

**La solution.**

- Donner à l'agent revue de presse **seulement les articles** trouvés (résultats de l'outil et actualités du jour), sans les longues réponses de l'agent du chat. Le texte à lire est plus court, et la revue ne peut pas reprendre une erreur écrite par l'agent du chat (voir la piste 1).
- Pendant la génération, afficher une **barre de progression** ou un message plus précis que « Génération en cours… ».

**Les fichiers à modifier.**

- `review_agent.py` : une nouvelle fonction qui extrait seulement les articles de l'historique (à la place de `history_to_text`).
- `routes/review_routes.py` : donner à l'agent le thème et ces articles, au lieu de toute la discussion.
- `components/ReviewModal.js` : un message d'attente plus précis pendant la génération.

**Comment vérifier.** Génération en **moins de 8 secondes**, quelle que soit la longueur de la discussion.

### 4. Mesurer automatiquement avec MLflow

**Le problème.** Les mesures de ce document ont été faites **à la main** : ouvrir les outils du navigateur (F12), envoyer des messages, puis recopier les temps dans un tableau. Et on ne voit pas ce que l'IA a reçu : pour savoir d'où vient un chiffre (piste 1), il faut aller lire le prompt dans la base de données.

**Un exemple.** Les 8 mesures du tableau ci-dessus ont toutes été relevées et recopiées à la main.

**La solution.** Brancher **MLflow** sur les appels de PydanticAI. MLflow fonctionne comme un **cahier automatique** : à chaque réponse de l'IA, il note tout seul la question, la réponse, le temps de réponse et le nombre de tokens. Tout s'affiche ensuite dans une page web, sans F12.

**Les fichiers à modifier.**

- `pyproject.toml` : ajouter la librairie `mlflow` (avec `uv add mlflow`).
- `main.py` : activer le suivi MLflow au démarrage du backend, pour que chaque appel des agents soit enregistré.
- `.env` et Variables de Railway : l'adresse du serveur MLflow, qui affiche la page web des enregistrements.

**Comment vérifier.** 100 % des réponses de l'IA sont enregistrées dans MLflow, avec leur temps, sans aucune mesure à la main.

## Autres pistes, en bref

- Filtrer les actualités du jour : le 19/11, l'IA a cité l'horoscope comme une actualité.
- Mieux trier les résultats de recherche : le 24/11, un article sur l'état des lycées est sorti pour une question sur les passoires thermiques.

## Autres améliorations (hors IA)

- Permettre de **supprimer** une discussion (`DELETE /chats/{chat_id}`) et de garder **plusieurs revues** par discussion (table séparée).
- Ajouter une page d'**inscription** et le choix du pays des actualités.
