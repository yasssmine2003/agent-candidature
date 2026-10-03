# Agent d'analyse de candidature

Un agent IA qui compare un CV à une offre de stage, puis répond à des questions libres :
*« Ai-je assez d'expérience ? »*, *« Quelles compétences me manquent ? »*, *« Combien de temps ai-je passé chez ABC Tech ? »*.

Le modèle de langage **décide** quels outils appeler ; les **calculs et comparaisons** sont faits par du code Python déterministe et testé.

## Pourquoi un agent, et pas un simple script ?

Une analyse toujours identique (extraire, calculer, noter) serait un **workflow** : un enchaînement fixe suffirait.
L'agent se justifie parce que les questions sont **libres** : selon la question, le modèle choisit l'outil adapté, en appelle plusieurs, ou aucun.
Le projet combine donc les deux : un workflow fixe au démarrage, puis une boucle agentique pour la conversation.

## Architecture

```mermaid
flowchart LR
    subgraph Demarrage["Démarrage : une seule fois"]
        T[Textes : CV + offre] --> D{Détection d'injection}
        D --> E[Extraction LLM<br/>+ schéma Pydantic strict]
        E --> A{Contrôle d'ancrage}
        A --> S[État validé<br/>CV, OffreStage]
    end
    subgraph Conversation["Conversation : à chaque question"]
        Q[Question] --> L[LLM : outil ou réponse ?]
        L -->|tool_calls| X[Exécuteur d'outils]
        X --> O[Outils Python]
        O -->|résultats| L
        L -->|pas d'outil| R[Réponse]
    end
    S -. données lues par les outils .-> O
```

**Principes de conception**

- **Le LLM comprend, le code calcule.** Le modèle extrait des dates ; Python calcule les durées.
- **Les outils lisent l'état, pas les arguments du modèle.** Grâce à une closure, les outils accèdent au CV validé : le modèle n'a jamais à recopier les données.
- **L'agent de conversation ne lit jamais le texte brut.** Seuls des champs structurés et validés lui parviennent (approche inspirée du modèle *Dual LLM*).
- **Outils en lecture seule** (moindre privilège) : un agent manipulé ne peut causer aucun effet réel.

## Fonctionnalités

| Domaine | Ce qui est fait |
|---|---|
| Extraction | Structured outputs en mode strict + validation Pydantic, nouvel essai en cas d'échec |
| Outils | Analyse des compétences (déclarées / démontrées), de l'expérience, des expériences détaillées, calcul de durées |
| Agent | Boucle de tool calling écrite sans framework, appels parallèles, limite de tours, erreurs d'outils renvoyées au modèle |
| Mémoire | Historique multi-tours avec fenêtre glissante qui ne sépare jamais un appel d'outil de son résultat |
| Sécurité | Détection d'injection, contrôle d'ancrage des compétences, alertes plutôt que blocage, outils en lecture seule |
| Évaluation | Jeu de cas de test, précision du choix des outils, contenu, latence, tokens |
| Déploiement | API FastAPI, image Docker, secrets fournis au lancement |

## Choix techniques

| Choix | Raison |
|---|---|
| Boucle agentique écrite à la main | Comprendre et contrôler chaque étape avant d'utiliser un framework (LangGraph serait l'étape suivante) |
| Groq + `openai/gpt-oss-20b` | Gratuit pour le développement, rapide, API compatible OpenAI (changer de fournisseur ne touche que `llm.py`) |
| Pydantic | Schémas partagés entre l'extraction, les structured outputs et l'API |
| FastAPI | Validation automatique des requêtes et documentation interactive |

## Installation

```bash
git clone <url-du-depot>
cd agent-candidature
python -m venv venv
venv\Scripts\activate            # Windows  (macOS/Linux : source venv/bin/activate)
pip install -r requirements.txt
copy .env.example .env           # puis renseigner GROQ_API_KEY
```

## Utilisation

**Dans le terminal**
```bash
python src/main.py                       # CV d'exemple
python src/main.py data/cv_piege.txt     # CV contenant une tentative d'injection
```

**API**
```bash
uvicorn api:app --app-dir src --reload
```
Documentation interactive : http://127.0.0.1:8000/docs

| Route | Rôle |
|---|---|
| `GET /sante` | Vérifie que le service tourne |
| `POST /analyses` | Analyse un CV et une offre, renvoie une `session_id` et des alertes éventuelles |
| `POST /analyses/{session_id}/questions` | Pose une question à l'agent dans cette session |

**Docker**
```bash
docker build -t agent-candidature .
docker run --env-file .env -p 8000:8000 agent-candidature
```

## Tests et évaluation

```bash
python -m pytest                  # 30 tests, sans appel au LLM
python evaluation/evaluer.py      # évaluation réelle (consomme le quota de l'API)
```

**Résultats** sur 8 cas de test, une exécution : 100 % de choix d'outils corrects, latence moyenne de 1,1 s, environ 1 100 tokens par question.

**Limites de cette évaluation**, à garder en tête :
- 8 cas seulement, écrits par l'auteur du projet, une seule exécution par cas.
- Le contenu est vérifié par mots-clés : des formulations spéculatives peuvent passer inaperçues.
- Prochaine étape : répéter les cas, élargir le jeu de test, ajouter une évaluation par *LLM-as-a-judge*.

## Sécurité

Un CV piégé (`data/cv_piege.txt`) contient trois tentatives d'injection. Résultats :

| Attaque | Résultat | Raison |
|---|---|---|
| Ajouter de fausses compétences | Échec | Consigne respectée par le modèle : protection **probable**, pas garantie |
| Déclarer 36 mois d'expérience | Échec | Aucun champ pour l'exprimer : la durée est calculée à partir des dates |
| Forcer une réponse favorable | Échec | L'agent de conversation ne voit jamais le texte brut |

## Limites connues

- Correspondance exacte des compétences après normalisation : « ML » et « Machine Learning » restent différents (une comparaison par embeddings réglerait ce point).
- Les expériences qui se chevauchent sont comptées deux fois.
- Sessions stockées en mémoire, sans authentification : à remplacer par une base de données et une authentification en production.
- La détection d'injection repose sur des motifs simples : faux positifs et contournements possibles.

## Structure

```
src/
  modeles.py      schémas Pydantic
  llm.py          connexion au LLM
  extraction.py   texte brut -> objets validés
  outils.py       outils Python + descriptions pour le LLM
  agent.py        boucle agentique
  memoire.py      gestion de l'historique
  securite.py     détection d'injection, contrôle d'ancrage
  main.py         interface terminal
  api.py          API FastAPI
tests/            30 tests unitaires, sans LLM
evaluation/       cas de test, métriques, script d'évaluation
data/             CV et offre d'exemple, CV piégé
```