"""
Script de test complet pour vérifier le bon fonctionnement de la base de données
Exécute une série de tests pour valider la structure, les données et les requêtes
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.database import get_db_cursor, execute_query
from datetime import datetime

class DatabaseTester:
    def __init__(self):
        self.tests_passed = 0
        self.tests_failed = 0
        self.errors = []
    
    def print_header(self, text):
        """Affiche un en-tête formaté"""
        print(f"\n{'='*60}")
        print(f"  {text}")
        print(f"{'='*60}\n")
    
    def print_success(self, message):
        """Affiche un message de succès"""
        print(f"✓ {message}")
        self.tests_passed += 1
    
    def print_error(self, message, error=None):
        """Affiche un message d'erreur"""
        error_msg = f"✗ {message}"
        if error:
            error_msg += f"\n  Erreur: {str(error)}"
        print(error_msg)
        self.tests_failed += 1
        self.errors.append(error_msg)
    
    def test_connection(self):
        """Test 1: Vérifier la connexion à la base de données"""
        self.print_header("TEST 1: Connexion à la base de données")
        try:
            with get_db_cursor() as cursor:
                cursor.execute("SELECT VERSION()")
                version = cursor.fetchone()[0]
                self.print_success(f"Connexion réussie - MySQL version: {version}")
        except Exception as e:
            self.print_error("Échec de connexion à la base de données", e)
    
    def test_tables_existence(self):
        """Test 2: Vérifier l'existence de toutes les tables"""
        self.print_header("TEST 2: Vérification des tables")
        
        required_tables = [
            'universites', 'facultes', 'departements', 'formations',
            'niveaux', 'etudiants', 'matieres', 'enseignants',
            'salles', 'examens', 'inscriptions', 'surveillances'
        ]
        
        try:
            with get_db_cursor(dictionary=True) as cursor:
                cursor.execute("SHOW TABLES")
                existing_tables = [list(row.values())[0] for row in cursor.fetchall()]
                
                for table in required_tables:
                    if table in existing_tables:
                        self.print_success(f"Table '{table}' existe")
                    else:
                        self.print_error(f"Table '{table}' manquante")
        except Exception as e:
            self.print_error("Échec de vérification des tables", e)
    
    def test_data_counts(self):
        """Test 3: Vérifier le nombre de lignes dans chaque table"""
        self.print_header("TEST 3: Comptage des données")
        
        tables = [
            ('universites', 1, 1),
            ('facultes', 1, 1),
            ('departements', 7, 7),
            ('formations', 200, None),
            ('niveaux', 5, 5),
            ('etudiants', 10000, None),
            ('matieres', 100, None),
            ('enseignants', 50, None),
            ('salles', 30, None),
            ('examens', 0, None),
            ('inscriptions', 100000, None),
            ('surveillances', 0, None)
        ]
        
        try:
            for table, min_expected, exact_expected in tables:
                with get_db_cursor() as cursor:
                    cursor.execute(f"SELECT COUNT(*) FROM {table}")
                    count = cursor.fetchone()[0]
                    
                    if exact_expected is not None:
                        if count == exact_expected:
                            self.print_success(f"Table '{table}': {count} lignes (attendu: {exact_expected})")
                        else:
                            self.print_error(f"Table '{table}': {count} lignes (attendu: {exact_expected})")
                    else:
                        if count >= min_expected:
                            self.print_success(f"Table '{table}': {count} lignes (min: {min_expected})")
                        else:
                            self.print_error(f"Table '{table}': {count} lignes (min: {min_expected})")
        except Exception as e:
            self.print_error("Échec du comptage des données", e)
    
    def test_foreign_keys(self):
        """Test 4: Vérifier l'intégrité des clés étrangères"""
        self.print_header("TEST 4: Intégrité des clés étrangères")
        
        checks = [
            ("Facultés → Universités", 
             "SELECT COUNT(*) FROM facultes f LEFT JOIN universites u ON f.universite_id = u.id WHERE u.id IS NULL"),
            ("Départements → Facultés",
             "SELECT COUNT(*) FROM departements d LEFT JOIN facultes f ON d.faculte_id = f.id WHERE f.id IS NULL"),
            ("Formations → Départements",
             "SELECT COUNT(*) FROM formations f LEFT JOIN departements d ON f.departement_id = d.id WHERE d.id IS NULL"),
            ("Étudiants → Formations",
             "SELECT COUNT(*) FROM etudiants e LEFT JOIN formations f ON e.formation_id = f.id WHERE f.id IS NULL"),
            ("Inscriptions → Étudiants",
             "SELECT COUNT(*) FROM inscriptions i LEFT JOIN etudiants e ON i.etudiant_id = e.id WHERE e.id IS NULL"),
            ("Inscriptions → Matières",
             "SELECT COUNT(*) FROM inscriptions i LEFT JOIN matieres m ON i.matiere_id = m.id WHERE m.id IS NULL")
        ]
        
        try:
            for check_name, query in checks:
                with get_db_cursor() as cursor:
                    cursor.execute(query)
                    orphans = cursor.fetchone()[0]
                    
                    if orphans == 0:
                        self.print_success(f"{check_name}: Aucune ligne orpheline")
                    else:
                        self.print_error(f"{check_name}: {orphans} lignes orphelines détectées")
        except Exception as e:
            self.print_error("Échec de vérification des clés étrangères", e)
    
    def test_business_rules(self):
        """Test 5: Vérifier les règles métier"""
        self.print_header("TEST 5: Règles métier")
        
        try:
            # Vérifier qu'il n'y a pas d'emails en double
            with get_db_cursor() as cursor:
                cursor.execute("SELECT email, COUNT(*) as cnt FROM etudiants GROUP BY email HAVING cnt > 1")
                duplicates = cursor.fetchall()
                
                if len(duplicates) == 0:
                    self.print_success("Pas d'emails d'étudiants en double")
                else:
                    self.print_error(f"{len(duplicates)} emails d'étudiants en double détectés")
            
            # Vérifier que les capacités des salles sont positives
            with get_db_cursor() as cursor:
                cursor.execute("SELECT COUNT(*) FROM salles WHERE capacite <= 0")
                invalid = cursor.fetchone()[0]
                
                if invalid == 0:
                    self.print_success("Toutes les salles ont une capacité valide")
                else:
                    self.print_error(f"{invalid} salles avec capacité invalide")
            
            # Vérifier que les notes sont entre 0 et 20
            with get_db_cursor() as cursor:
                cursor.execute("SELECT COUNT(*) FROM inscriptions WHERE note < 0 OR note > 20")
                invalid = cursor.fetchone()[0]
                
                if invalid == 0:
                    self.print_success("Toutes les notes sont dans la plage valide (0-20)")
                else:
                    self.print_error(f"{invalid} notes invalides détectées")
            
        except Exception as e:
            self.print_error("Échec de vérification des règles métier", e)
    
    def test_complex_queries(self):
        """Test 6: Vérifier que les requêtes complexes fonctionnent"""
        self.print_header("TEST 6: Requêtes complexes")
        
        try:
            # Query 1: Statistiques par département
            with get_db_cursor(dictionary=True) as cursor:
                cursor.execute("""
                    SELECT 
                        d.nom as departement,
                        COUNT(DISTINCT f.id) as nb_formations,
                        COUNT(DISTINCT e.id) as nb_etudiants
                    FROM departements d
                    LEFT JOIN formations f ON d.id = f.departement_id
                    LEFT JOIN etudiants e ON f.id = e.formation_id
                    GROUP BY d.id, d.nom
                """)
                results = cursor.fetchall()
                
                if len(results) > 0:
                    self.print_success(f"Statistiques par département: {len(results)} départements analysés")
                else:
                    self.print_error("Aucune statistique générée pour les départements")
            
            # Query 2: Étudiants avec leurs inscriptions
            with get_db_cursor() as cursor:
                cursor.execute("""
                    SELECT COUNT(DISTINCT e.id)
                    FROM etudiants e
                    INNER JOIN inscriptions i ON e.id = i.etudiant_id
                """)
                count = cursor.fetchone()[0]
                
                if count > 0:
                    self.print_success(f"Jointure étudiants-inscriptions: {count} étudiants avec inscriptions")
                else:
                    self.print_error("Aucun étudiant avec inscriptions trouvé")
            
            # Query 3: Matières par formation avec enseignants
            with get_db_cursor() as cursor:
                cursor.execute("""
                    SELECT COUNT(*)
                    FROM matieres m
                    INNER JOIN formations f ON m.formation_id = f.id
                    LEFT JOIN enseignants ens ON m.enseignant_id = ens.id
                """)
                count = cursor.fetchone()[0]
                
                if count > 0:
                    self.print_success(f"Jointure matières-formations-enseignants: {count} lignes")
                else:
                    self.print_error("Échec de la jointure matières-formations-enseignants")
                    
        except Exception as e:
            self.print_error("Échec d'exécution des requêtes complexes", e)
    
    def test_indexes(self):
        """Test 7: Vérifier l'existence des index importants"""
        self.print_header("TEST 7: Vérification des index")
        
        try:
            with get_db_cursor(dictionary=True) as cursor:
                # Vérifier les index sur la table étudiants
                cursor.execute("SHOW INDEX FROM etudiants")
                indexes = cursor.fetchall()
                index_names = [idx['Key_name'] for idx in indexes]
                
                if 'PRIMARY' in index_names:
                    self.print_success("Index PRIMARY sur table étudiants")
                else:
                    self.print_error("Index PRIMARY manquant sur table étudiants")
                
                # Vérifier les index sur la table inscriptions
                cursor.execute("SHOW INDEX FROM inscriptions")
                indexes = cursor.fetchall()
                
                if len(indexes) > 0:
                    self.print_success(f"Table inscriptions: {len(indexes)} index trouvés")
                else:
                    self.print_error("Aucun index sur table inscriptions")
                    
        except Exception as e:
            self.print_error("Échec de vérification des index", e)
    
    def test_performance(self):
        """Test 8: Vérifier les performances basiques"""
        self.print_header("TEST 8: Tests de performance")
        
        try:
            # Test 1: Compter tous les étudiants
            start = datetime.now()
            with get_db_cursor() as cursor:
                cursor.execute("SELECT COUNT(*) FROM etudiants")
                count = cursor.fetchone()[0]
            duration = (datetime.now() - start).total_seconds()
            
            if duration < 1.0:
                self.print_success(f"Comptage étudiants ({count} lignes): {duration:.3f}s")
            else:
                self.print_error(f"Comptage étudiants trop lent: {duration:.3f}s")
            
            # Test 2: Recherche avec jointure
            start = datetime.now()
            with get_db_cursor() as cursor:
                cursor.execute("""
                    SELECT e.nom, f.nom, d.nom
                    FROM etudiants e
                    JOIN formations f ON e.formation_id = f.id
                    JOIN departements d ON f.departement_id = d.id
                    LIMIT 100
                """)
                results = cursor.fetchall()
            duration = (datetime.now() - start).total_seconds()
            
            if duration < 2.0:
                self.print_success(f"Jointure complexe (100 lignes): {duration:.3f}s")
            else:
                self.print_error(f"Jointure complexe trop lente: {duration:.3f}s")
                
        except Exception as e:
            self.print_error("Échec des tests de performance", e)
    
    def run_all_tests(self):
        """Exécute tous les tests"""
        print("\n" + "="*60)
        print("  TEST COMPLET DE LA BASE DE DONNÉES")
        print("="*60)
        
        self.test_connection()
        self.test_tables_existence()
        self.test_data_counts()
        self.test_foreign_keys()
        self.test_business_rules()
        self.test_complex_queries()
        self.test_indexes()
        self.test_performance()
        
        # Résumé final
        self.print_header("RÉSUMÉ DES TESTS")
        total = self.tests_passed + self.tests_failed
        success_rate = (self.tests_passed / total * 100) if total > 0 else 0
        
        print(f"Tests réussis:  {self.tests_passed}")
        print(f"Tests échoués:  {self.tests_failed}")
        print(f"Taux de succès: {success_rate:.1f}%\n")
        
        if self.tests_failed > 0:
            print("\nERREURS DÉTECTÉES:")
            for error in self.errors:
                print(f"  - {error}")
        
        return self.tests_failed == 0

if __name__ == "__main__":
    tester = DatabaseTester()
    success = tester.run_all_tests()
    
    if success:
        print("\n✓ Tous les tests sont passés avec succès!")
        exit(0)
    else:
        print(f"\n✗ {tester.tests_failed} test(s) ont échoué")
        exit(1)
