# Guide de Test de la Base de Données

Ce document explique comment tester et vérifier le bon fonctionnement de votre base de données.

## Prérequis

Assurez-vous que :
1. MySQL est installé et en cours d'exécution
2. La base de données a été créée (`scripts/01_create_database.sql`)
3. Les données ont été chargées (`scripts/02_seed_database.py`)
4. Les dépendances Python sont installées (`pip install -r requirements.txt`)

## 1. Vérification Rapide

Pour un aperçu rapide de l'état de votre base de données :

```bash
python scripts/04_quick_check.py
```

Ce script affiche :
- Nombre total d'enregistrements par table
- Top 3 des départements par nombre d'étudiants
- Répartition des salles par type
- Statistiques d'inscriptions
- État de la planification des examens

**Temps d'exécution :** ~1-2 secondes

## 2. Tests Complets

Pour une vérification complète avec tous les tests :

```bash
python scripts/03_test_database.py
```

### Tests Effectués

#### Test 1 : Connexion
- Vérifie que la connexion à MySQL fonctionne
- Affiche la version de MySQL

#### Test 2 : Existence des Tables
Vérifie que toutes les tables requises existent :
- universites, facultes, departements, formations
- niveaux, etudiants, matieres, enseignants
- salles, examens, inscriptions, surveillances

#### Test 3 : Comptage des Données
Vérifie le nombre de lignes dans chaque table :
- Au moins 13,000 étudiants
- Au moins 130,000 inscriptions
- 7 départements exactement
- etc.

#### Test 4 : Intégrité des Clés Étrangères
Vérifie qu'il n'y a pas de lignes orphelines :
- Toutes les facultés pointent vers une université valide
- Tous les étudiants ont une formation valide
- Toutes les inscriptions pointent vers des étudiants et matières valides

#### Test 5 : Règles Métier
Vérifie les contraintes métier :
- Pas d'emails en double
- Capacités des salles > 0
- Notes entre 0 et 20

#### Test 6 : Requêtes Complexes
Teste des jointures complexes :
- Statistiques par département
- Jointures multi-tables
- Agrégations

#### Test 7 : Index
Vérifie l'existence des index pour les performances

#### Test 8 : Performance
Mesure le temps d'exécution de requêtes typiques :
- Doit être < 1 seconde pour un simple COUNT
- Doit être < 2 secondes pour une jointure complexe

**Temps d'exécution :** ~5-10 secondes

## 3. Tests Manuels avec MySQL

Vous pouvez aussi vous connecter directement à MySQL :

```bash
mysql -u root -p exam_scheduling
```

### Requêtes de Vérification Utiles

```sql
-- Voir toutes les tables
SHOW TABLES;

-- Compter les étudiants
SELECT COUNT(*) FROM etudiants;

-- Voir les 10 premiers étudiants avec leur formation
SELECT e.nom, e.prenom, f.nom as formation, d.nom as departement
FROM etudiants e
JOIN formations f ON e.formation_id = f.id
JOIN departements d ON f.departement_id = d.id
LIMIT 10;

-- Statistiques par département
SELECT 
    d.nom as departement,
    COUNT(DISTINCT f.id) as nb_formations,
    COUNT(DISTINCT e.id) as nb_etudiants
FROM departements d
LEFT JOIN formations f ON d.id = f.departement_id
LEFT JOIN etudiants e ON f.id = e.formation_id
GROUP BY d.id, d.nom
ORDER BY nb_etudiants DESC;

-- Vérifier les inscriptions
SELECT 
    e.nom,
    e.prenom,
    COUNT(*) as nb_matieres
FROM etudiants e
JOIN inscriptions i ON e.id = i.etudiant_id
GROUP BY e.id
LIMIT 10;
```

## 4. Vérification de l'Algorithme de Planification

Pour tester l'algorithme d'optimisation :

```python
# Dans un script Python ou console Python
from backend.scheduler import ExamScheduler

scheduler = ExamScheduler()
schedule = scheduler.optimize_schedule()

print(f"Examens planifiés: {schedule['stats']['total_examens']}")
print(f"Durée: {schedule['stats']['duree_generation']:.2f}s")
print(f"Conflits: {schedule['stats']['conflits']}")
```

## 5. Tableau de Bord de Santé

État attendu après l'installation complète :

| Élément | Valeur Attendue | Statut |
|---------|----------------|--------|
| Étudiants | ~13,000 | ✓ |
| Inscriptions | ~130,000 | ✓ |
| Formations | ~200 | ✓ |
| Matières | ~100 | ✓ |
| Enseignants | ~50 | ✓ |
| Salles | ~30 | ✓ |
| Départements | 7 | ✓ |
| Clés étrangères | 0 orphelins | ✓ |
| Performance COUNT | < 1s | ✓ |
| Performance JOIN | < 2s | ✓ |

## 6. Résolution de Problèmes

### La connexion échoue
```bash
# Vérifiez que MySQL est en cours d'exécution
sudo service mysql status

# Vérifiez les identifiants dans backend/database.py
```

### Données manquantes
```bash
# Re-exécutez le script de seed
python scripts/02_seed_database.py
```

### Performances lentes
```sql
-- Vérifiez les index
SHOW INDEX FROM etudiants;
SHOW INDEX FROM inscriptions;

-- Analysez une requête lente
EXPLAIN SELECT ...;
```

## 7. Tests Automatisés dans CI/CD

Pour intégrer les tests dans un pipeline CI/CD :

```bash
# Exécuter les tests et sortir avec code d'erreur si échec
python scripts/03_test_database.py
if [ $? -ne 0 ]; then
    echo "Tests échoués!"
    exit 1
fi
```

## Support

Si tous les tests passent avec succès, votre base de données est prête à être utilisée en production!
