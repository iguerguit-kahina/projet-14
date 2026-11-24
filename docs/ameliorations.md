# Pistes d'amélioration

Ce document porte un regard critique sur l'application, sur deux points :

- la **qualité** des réponses données à l'utilisateur ;
- la **fluidité** : le temps que l'utilisateur attend.

Chaque piste suit le même plan : **le problème**, **un exemple** (vu ou mesuré), **la solution**, et **comment vérifier** que l'amélioration fonctionne.

## Les mesures

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

## Qualité des réponses

### 1. L'IA ajoute des informations qui ne viennent pas des articles

**Le problème.** Les articles cités sont fiables : ils viennent de World News API, avec leur titre, leur date et leur lien. Mais dans les parties qu'elle écrit elle-même (« Synthèse », « Points clés »), l'IA ajoute parfois des chiffres, des dates ou des liens de cause à effet qui ne sont dans aucun article. L'utilisateur ne peut pas faire la différence.

**Un exemple.**

- Le 24/11/2026, dans une réponse sur les passoires thermiques, l'IA a écrit : « 9,54 milliards d'euros retirés du Livret A en 2026, reflétant une crise du pouvoir d'achat et des difficultés à investir dans la rénovation. » Ce chiffre n'est dans aucun des articles cités, et le lien avec la rénovation est inventé. Dans la même liste, l'autre chiffre (« 17,1 % des ménages d'Occitanie ») venait bien d'un article.
- Le 19/11/2026, l'IA a écrit que la location des logements classés G serait interdite en 2028 et celle des F en 2034. Le vrai calendrier de la loi Climat et Résilience est : G en 2025, F en 2028, E en 2034.
- Le même test refait le 24/11 n'a pas reproduit l'erreur des dates : le comportement du LLM varie d'une fois à l'autre. Les règles ajoutées au prompt aident, mais pas à tous les coups.

**La solution.** Donner une **sortie structurée** à l'agent du chat quand il présente des articles, comme pour la revue de presse : une liste d'articles d'un côté, et une synthèse qui ne peut s'appuyer que sur ces articles. Le frontend affiche alors clairement ce qui vient des sources.

**Comment vérifier.** Préparer 20 questions de test et relancer ces questions à chaque modification : objectif **0 chiffre ou date absent des articles**, contrôlé à la main ou par un second LLM « juge ».

### 2. La recherche ramène parfois des articles hors sujet

**Le problème.** L'outil cherche par mots-clés : il peut ramener des articles qui contiennent les mots, mais qui ne traitent pas vraiment du sujet.

**Un exemple.** Le 24/11/2026, pour une question sur les passoires thermiques, l'IA a cité un article sur l'état des lycées de Strasbourg (fenêtres cassées, manque de WC). Elle a elle-même précisé qu'il était « centré sur l'état général des lycées ».

**La solution.** Demander plus de résultats à World News API (par exemple 10 au lieu de 5), puis demander au LLM de ne garder que les articles qui traitent vraiment du sujet.

**Comment vérifier.** Sur les 20 questions de test : au moins 9 articles pertinents sur 10.

### 3. Les actualités du jour contiennent des contenus qui ne sont pas de l'information

**Le problème.** Les gros titres de `/top-news` contiennent parfois des contenus qui ne sont pas des actualités, et l'IA les reprend.

**Un exemple.** Le 19/11/2026, l'IA a cité l'**horoscope du jour** dans sa liste des actualités.

**La solution.** Avant de fabriquer le prompt, filtrer les actualités : par mots-clés (horoscope, météo, programme télé…), ou en demandant au LLM de ne garder que les vraies actualités.

**Comment vérifier.** 0 horoscope ou programme télé dans les actualités du prompt, vérifié pendant 7 jours.

## Fluidité des interactions

### 4. Afficher la réponse au fur et à mesure (streaming)

**Le problème.** L'utilisateur voit « L'IA réfléchit… » jusqu'à ce que la réponse soit entièrement écrite. La plupart des applications de chat affichent la réponse pendant qu'elle s'écrit.

**Un exemple.** Une question simple fait attendre **7 secondes** ; une question avec recherche, **11 à 17 secondes**, sans rien voir apparaître.

**La solution.**

1. Backend : utiliser le streaming de PydanticAI (`chat_agent.run_stream`) dans la route `POST /chats/{chat_id}/messages`, et renvoyer la réponse morceau par morceau avec une `StreamingResponse` de FastAPI.
2. Frontend : lire la réponse au fur et à mesure avec `fetch`, et ajouter chaque morceau dans la bulle de l'IA.
3. Enregistrer l'historique dans la base une fois la réponse terminée.

**Comment vérifier.** Le premier mot s'affiche en **moins de 2 secondes** après l'envoi du message.

### 5. Accélérer la génération des revues de presse

**Le problème.** La revue de presse prend en moyenne **12 secondes**, et elle ralentit quand la discussion s'allonge, car l'agent reçoit **toute la discussion** : les questions, les longues réponses de l'IA et tous les articles.

**Un exemple.** **8,52 s** après 2 échanges, **15,40 s** après 5 échanges : presque **2 fois plus**.

**La solution.**

- Donner à l'agent revue de presse **seulement les articles** trouvés (résultats de l'outil et actualités du jour), sans les longues réponses de l'agent du chat. Le texte à lire est plus court, et la revue ne peut pas reprendre une erreur écrite par l'agent du chat (voir la piste 1).
- Pendant la génération, afficher une **barre de progression** ou un message plus précis que « Génération en cours… ».

**Comment vérifier.** Génération en **moins de 8 secondes**, quelle que soit la longueur de la discussion.

### 6. Limiter la taille de l'historique envoyé au LLM

**Le problème.** À chaque message, tout l'historique est renvoyé au LLM. Il grossit à chaque échange, surtout avec les articles trouvés par l'outil : les réponses ralentissent, et chaque appel coûte plus de tokens.

**Un exemple.** Dans la même discussion, les réponses passent de **7,16 s** (1er message) à **16,78 s** (5e message).

**La solution.** Envoyer au LLM seulement les derniers échanges, et un court résumé des plus anciens (fait par le LLM).

**Comment vérifier.** Un temps de réponse stable : moins de 10 secondes, même après 10 messages.

### 7. Mesurer automatiquement avec MLflow

**Le problème.** Les mesures de ce document ont été faites **à la main**, dans le navigateur. On ne voit pas non plus ce que l'IA reçoit vraiment : pour savoir d'où vient un chiffre (piste 1), il faut aller lire le prompt dans la base de données.

**La solution.** Brancher **MLflow** sur les appels de PydanticAI. Pour chaque réponse, il enregistre : le prompt reçu, les appels d'outils, la réponse, la durée et le nombre de tokens. On peut ainsi comparer deux versions du prompt, et suivre les temps de réponse dans le temps.

**Comment vérifier.** 100 % des appels au LLM enregistrés dans MLflow, et chaque nouvelle version du prompt comparée à la précédente avant d'être mise en ligne.

## Autres améliorations (hors IA)

- Utiliser **Alembic** pour les migrations de la base, au lieu des `ALTER TABLE` dans `init_db()`.
- Permettre de **supprimer** une discussion (`DELETE /chats/{chat_id}`) et de garder **plusieurs revues** par discussion (table séparée).
- Ajouter une page d'**inscription** et le choix du pays des actualités.
