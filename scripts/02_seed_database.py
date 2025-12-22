"""
Script pour alimenter la base de données avec des données réalistes
Simule une faculté de 13,000 étudiants avec 7 départements
"""

import mysql.connector
import random
import string
from datetime import datetime, timedelta
from faker import Faker

# Configuration de la connexion
DB_CONFIG = {
    'host': 'localhost',
    'user': 'root',
    'password': 'your_password',  # À modifier
    'database': 'exam_scheduling'
}

fake = Faker('fr_FR')
random.seed(42)

def get_connection():
    """Établit une connexion à la base de données"""
    return mysql.connector.connect(**DB_CONFIG)

def clear_tables(cursor):
    """Vide toutes les tables dans le bon ordre"""
    print("Nettoyage des tables existantes...")
    tables = [
        'logs_operations', 'conflits', 'surveillances', 'examens',
        'inscriptions', 'etudiants', 'modules', 'professeurs',
        'lieux_examen', 'formations', 'departements'
    ]
    for table in tables:
        cursor.execute(f"DELETE FROM {table}")
        cursor.execute(f"ALTER TABLE {table} AUTO_INCREMENT = 1")
    print("✓ Tables nettoyées")

def seed_departements(cursor):
    """Insère 7 départements"""
    print("\n📚 Insertion des départements...")
    departements = [
        ('Informatique', 'INFO'),
        ('Mathématiques', 'MATH'),
        ('Physique', 'PHYS'),
        ('Chimie', 'CHIM'),
        ('Biologie', 'BIO'),
        ('Économie', 'ECO'),
        ('Droit', 'DROIT')
    ]
    
    cursor.executemany(
        "INSERT INTO departements (nom, code) VALUES (%s, %s)",
        departements
    )
    print(f"✓ {len(departements)} départements insérés")
    return list(range(1, len(departements) + 1))

def seed_formations(cursor, dept_ids):
    """Insère environ 200 formations"""
    print("\n🎓 Insertion des formations...")
    formations = []
    formation_id = 1
    
    niveaux = ['Licence', 'Master']
    annees_licence = [1, 2, 3]
    annees_master = [1, 2]
    
    specialites = {
        1: ['Systèmes Informatiques', 'Réseaux', 'Intelligence Artificielle', 'Génie Logiciel', 'Cybersécurité'],
        2: ['Algèbre', 'Analyse', 'Géométrie', 'Statistiques', 'Mathématiques Appliquées'],
        3: ['Mécanique', 'Électromagnétisme', 'Optique', 'Physique Quantique', 'Astrophysique'],
        4: ['Chimie Organique', 'Chimie Inorganique', 'Chimie Analytique', 'Biochimie'],
        5: ['Biologie Moléculaire', 'Écologie', 'Génétique', 'Microbiologie', 'Neurosciences'],
        6: ['Finance', 'Management', 'Marketing', 'Commerce International', 'Économétrie'],
        7: ['Droit Public', 'Droit Privé', 'Droit des Affaires', 'Droit International']
    }
    
    for dept_id in dept_ids:
        dept_specialites = specialites[dept_id]
        
        for spec in dept_specialites:
            # Licence (3 ans)
            for annee in annees_licence:
                nb_modules = random.randint(6, 9)
                code = f"L{annee}-{dept_id:02d}-{formation_id:03d}"
                formations.append((
                    f"Licence {spec} - Année {annee}",
                    code,
                    dept_id,
                    nb_modules,
                    'Licence',
                    annee
                ))
                formation_id += 1
            
            # Master (2 ans)
            for annee in annees_master:
                nb_modules = random.randint(6, 8)
                code = f"M{annee}-{dept_id:02d}-{formation_id:03d}"
                formations.append((
                    f"Master {spec} - Année {annee}",
                    code,
                    dept_id,
                    nb_modules,
                    'Master',
                    annee
                ))
                formation_id += 1
    
    cursor.executemany(
        """INSERT INTO formations (nom, code, dept_id, nb_modules, niveau, annee)
           VALUES (%s, %s, %s, %s, %s, %s)""",
        formations
    )
    print(f"✓ {len(formations)} formations insérées")
    return len(formations)

def seed_professeurs(cursor, dept_ids):
    """Insère des professeurs (environ 15 par département)"""
    print("\n👨‍🏫 Insertion des professeurs...")
    professeurs = []
    
    grades = ['Professeur', 'Maître de conférences A', 'Maître de conférences B', 'Assistant']
    
    for dept_id in dept_ids:
        nb_profs = random.randint(12, 18)
        for _ in range(nb_profs):
            nom = fake.last_name()
            prenom = fake.first_name()
            email = f"{prenom.lower()}.{nom.lower()}@univ.fr"
            telephone = fake.phone_number()
            grade = random.choice(grades)
            specialite = fake.job()
            
            professeurs.append((
                nom, prenom, email, telephone, dept_id, specialite, grade
            ))
    
    cursor.executemany(
        """INSERT INTO professeurs (nom, prenom, email, telephone, dept_id, specialite, grade)
           VALUES (%s, %s, %s, %s, %s, %s, %s)""",
        professeurs
    )
    print(f"✓ {len(professeurs)} professeurs insérés")

def seed_modules(cursor):
    """Insère les modules pour chaque formation"""
    print("\n📖 Insertion des modules...")
    
    # Récupérer toutes les formations
    cursor.execute("SELECT id, nb_modules, code, dept_id FROM formations")
    formations = cursor.fetchall()
    
    # Récupérer les professeurs par département
    cursor.execute("SELECT id, dept_id FROM professeurs")
    profs = cursor.fetchall()
    profs_by_dept = {}
    for prof_id, dept_id in profs:
        if dept_id not in profs_by_dept:
            profs_by_dept[dept_id] = []
        profs_by_dept[dept_id].append(prof_id)
    
    modules = []
    module_id = 1
    
    matieres_base = [
        'Introduction', 'Fondamentaux', 'Avancé', 'Théorie', 'Pratique',
        'Projet', 'Stage', 'Séminaire', 'Méthodologie', 'Analyse'
    ]
    
    for formation_id, nb_modules, formation_code, dept_id in formations:
        for i in range(nb_modules):
            matiere = random.choice(matieres_base)
            nom = f"{matiere} {i+1}"
            code = f"{formation_code}-M{i+1:02d}"
            credits = random.choice([3, 4, 5, 6])
            semestre = 1 if i < nb_modules // 2 else 2
            duree_examen = random.choice([90, 120, 150, 180])
            
            # Assigner un professeur du même département
            prof_responsable = random.choice(profs_by_dept.get(dept_id, [None]))
            
            modules.append((
                nom, code, credits, formation_id, semestre,
                prof_responsable, duree_examen
            ))
            module_id += 1
    
    cursor.executemany(
        """INSERT INTO modules (nom, code, credits, formation_id, semestre, 
           prof_responsable_id, duree_examen_minutes)
           VALUES (%s, %s, %s, %s, %s, %s, %s)""",
        modules
    )
    print(f"✓ {len(modules)} modules insérés")

def seed_lieux_examen(cursor):
    """Insère les salles et amphithéâtres"""
    print("\n🏛️ Insertion des lieux d'examen...")
    lieux = []
    
    # Amphithéâtres (grandes capacités)
    for i in range(1, 21):  # 20 amphis
        capacite = random.choice([150, 200, 250, 300, 350, 400, 500])
        batiment = f"Bâtiment {random.choice(['A', 'B', 'C', 'D', 'E'])}"
        equipements = "Projecteur, Sonorisation, Micros"
        lieux.append((f"Amphi {i}", capacite, 'amphi', batiment, equipements))
    
    # Salles (petites capacités, max 20 en période d'examen)
    for i in range(1, 151):  # 150 salles
        capacite = 20
        batiment = f"Bâtiment {random.choice(['A', 'B', 'C', 'D', 'E', 'F', 'G'])}"
        equipements = random.choice([
            "Tableau blanc",
            "Projecteur, Tableau blanc",
            "Ordinateurs, Projecteur",
            "Tableau blanc, Écran"
        ])
        lieux.append((f"Salle {i}", capacite, 'salle', batiment, equipements))
    
    cursor.executemany(
        """INSERT INTO lieux_examen (nom, capacite, type, batiment, equipements)
           VALUES (%s, %s, %s, %s, %s)""",
        lieux
    )
    print(f"✓ {len(lieux)} lieux d'examen insérés")

def seed_etudiants(cursor):
    """Insère environ 13,000 étudiants"""
    print("\n👨‍🎓 Insertion des étudiants...")
    
    # Récupérer toutes les formations
    cursor.execute("SELECT id FROM formations")
    formation_ids = [row[0] for row in cursor.fetchall()]
    
    etudiants = []
    numero_base = 20200000
    
    # Distribution réaliste: plus d'étudiants en Licence 1 qu'en Master 2
    nb_etudiants = 13000
    annees_inscription = [2020, 2021, 2022, 2023, 2024]
    
    for i in range(nb_etudiants):
        nom = fake.last_name()
        prenom = fake.first_name()
        numero_etudiant = f"E{numero_base + i}"
        email = f"{numero_etudiant}@etu.univ.fr"
        formation_id = random.choice(formation_ids)
        annee_inscription = random.choice(annees_inscription)
        
        etudiants.append((
            nom, prenom, email, numero_etudiant, formation_id, annee_inscription
        ))
        
        # Afficher la progression
        if (i + 1) % 1000 == 0:
            print(f"  → {i + 1}/{nb_etudiants} étudiants...")
    
    # Insertion par lots pour améliorer les performances
    batch_size = 1000
    for i in range(0, len(etudiants), batch_size):
        batch = etudiants[i:i + batch_size]
        cursor.executemany(
            """INSERT INTO etudiants (nom, prenom, email, numero_etudiant, 
               formation_id, annee_inscription)
               VALUES (%s, %s, %s, %s, %s, %s)""",
            batch
        )
    
    print(f"✓ {len(etudiants)} étudiants insérés")

def seed_inscriptions(cursor):
    """Insère les inscriptions (étudiants inscrits aux modules)"""
    print("\n📝 Insertion des inscriptions...")
    
    # Récupérer les étudiants avec leurs formations
    cursor.execute("""
        SELECT e.id, e.formation_id 
        FROM etudiants e
    """)
    etudiants = cursor.fetchall()
    
    # Récupérer les modules par formation
    cursor.execute("SELECT id, formation_id FROM modules")
    modules_data = cursor.fetchall()
    modules_by_formation = {}
    for module_id, formation_id in modules_data:
        if formation_id not in modules_by_formation:
            modules_by_formation[formation_id] = []
        modules_by_formation[formation_id].append(module_id)
    
    inscriptions = []
    annee_universitaire = "2024-2025"
    
    for idx, (etudiant_id, formation_id) in enumerate(etudiants):
        # Chaque étudiant s'inscrit à tous les modules de sa formation
        modules_formation = modules_by_formation.get(formation_id, [])
        for module_id in modules_formation:
            inscriptions.append((
                etudiant_id, module_id, annee_universitaire
            ))
        
        # Afficher la progression
        if (idx + 1) % 1000 == 0:
            print(f"  → {idx + 1}/{len(etudiants)} étudiants traités...")
    
    # Insertion par lots
    batch_size = 5000
    for i in range(0, len(inscriptions), batch_size):
        batch = inscriptions[i:i + batch_size]
        cursor.executemany(
            """INSERT INTO inscriptions (etudiant_id, module_id, annee_universitaire)
               VALUES (%s, %s, %s)""",
            batch
        )
        print(f"  → {min(i + batch_size, len(inscriptions))}/{len(inscriptions)} inscriptions...")
    
    print(f"✓ {len(inscriptions)} inscriptions insérées")

def main():
    """Fonction principale"""
    print("=" * 60)
    print("ALIMENTATION DE LA BASE DE DONNÉES")
    print("=" * 60)
    
    conn = get_connection()
    cursor = conn.cursor()
    
    try:
        # Nettoyer les tables existantes
        clear_tables(cursor)
        conn.commit()
        
        # Insérer les données
        dept_ids = seed_departements(cursor)
        conn.commit()
        
        seed_formations(cursor, dept_ids)
        conn.commit()
        
        seed_professeurs(cursor, dept_ids)
        conn.commit()
        
        seed_modules(cursor)
        conn.commit()
        
        seed_lieux_examen(cursor)
        conn.commit()
        
        seed_etudiants(cursor)
        conn.commit()
        
        seed_inscriptions(cursor)
        conn.commit()
        
        # Statistiques finales
        print("\n" + "=" * 60)
        print("STATISTIQUES FINALES")
        print("=" * 60)
        
        stats = [
            ('departements', 'Départements'),
            ('formations', 'Formations'),
            ('professeurs', 'Professeurs'),
            ('modules', 'Modules'),
            ('etudiants', 'Étudiants'),
            ('lieux_examen', 'Lieux d\'examen'),
            ('inscriptions', 'Inscriptions')
        ]
        
        for table, nom in stats:
            cursor.execute(f"SELECT COUNT(*) FROM {table}")
            count = cursor.fetchone()[0]
            print(f"✓ {nom}: {count:,}")
        
        print("\n✅ Base de données alimentée avec succès!")
        
    except Exception as e:
        print(f"\n❌ Erreur: {e}")
        conn.rollback()
        raise
    finally:
        cursor.close()
        conn.close()

if __name__ == "__main__":
    main()
