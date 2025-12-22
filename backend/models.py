"""
Modèles et requêtes pour la gestion des données
"""

from datetime import datetime, timedelta, time
from backend.database import execute_query, execute_many

class DepartementModel:
    """Gestion des départements"""
    
    @staticmethod
    def get_all():
        """Récupère tous les départements"""
        query = "SELECT * FROM departements ORDER BY nom"
        return execute_query(query, dictionary=True)
    
    @staticmethod
    def get_by_id(dept_id):
        """Récupère un département par son ID"""
        query = "SELECT * FROM departements WHERE id = %s"
        results = execute_query(query, (dept_id,), dictionary=True)
        return results[0] if results else None
    
    @staticmethod
    def get_statistics(dept_id=None):
        """Statistiques d'un département"""
        if dept_id:
            query = """
                SELECT 
                    d.nom as departement,
                    COUNT(DISTINCT f.id) as nb_formations,
                    COUNT(DISTINCT e.id) as nb_etudiants,
                    COUNT(DISTINCT p.id) as nb_professeurs,
                    COUNT(DISTINCT m.id) as nb_modules
                FROM departements d
                LEFT JOIN formations f ON d.id = f.dept_id
                LEFT JOIN etudiants e ON f.id = e.formation_id
                LEFT JOIN professeurs p ON d.id = p.dept_id
                LEFT JOIN modules m ON f.id = m.formation_id
                WHERE d.id = %s
                GROUP BY d.id, d.nom
            """
            results = execute_query(query, (dept_id,), dictionary=True)
        else:
            query = """
                SELECT 
                    d.nom as departement,
                    COUNT(DISTINCT f.id) as nb_formations,
                    COUNT(DISTINCT e.id) as nb_etudiants,
                    COUNT(DISTINCT p.id) as nb_professeurs,
                    COUNT(DISTINCT m.id) as nb_modules
                FROM departements d
                LEFT JOIN formations f ON d.id = f.dept_id
                LEFT JOIN etudiants e ON f.id = e.formation_id
                LEFT JOIN professeurs p ON d.id = p.dept_id
                LEFT JOIN modules m ON f.id = m.formation_id
                GROUP BY d.id, d.nom
                ORDER BY d.nom
            """
            results = execute_query(query, dictionary=True)
        
        return results

class FormationModel:
    """Gestion des formations"""
    
    @staticmethod
    def get_all(dept_id=None):
        """Récupère toutes les formations, optionnellement filtrées par département"""
        if dept_id:
            query = """
                SELECT f.*, d.nom as departement_nom
                FROM formations f
                JOIN departements d ON f.dept_id = d.id
                WHERE f.dept_id = %s
                ORDER BY f.niveau, f.annee, f.nom
            """
            return execute_query(query, (dept_id,), dictionary=True)
        else:
            query = """
                SELECT f.*, d.nom as departement_nom
                FROM formations f
                JOIN departements d ON f.dept_id = d.id
                ORDER BY d.nom, f.niveau, f.annee
            """
            return execute_query(query, dictionary=True)
    
    @staticmethod
    def get_by_id(formation_id):
        """Récupère une formation par son ID"""
        query = """
            SELECT f.*, d.nom as departement_nom
            FROM formations f
            JOIN departements d ON f.dept_id = d.id
            WHERE f.id = %s
        """
        results = execute_query(query, (formation_id,), dictionary=True)
        return results[0] if results else None

class ModuleModel:
    """Gestion des modules"""
    
    @staticmethod
    def get_by_formation(formation_id):
        """Récupère tous les modules d'une formation"""
        query = """
            SELECT m.*, 
                   p.nom as prof_nom, 
                   p.prenom as prof_prenom,
                   COUNT(i.id) as nb_inscrits
            FROM modules m
            LEFT JOIN professeurs p ON m.prof_responsable_id = p.id
            LEFT JOIN inscriptions i ON m.id = i.module_id
            WHERE m.formation_id = %s
            GROUP BY m.id
            ORDER BY m.semestre, m.nom
        """
        return execute_query(query, (formation_id,), dictionary=True)
    
    @staticmethod
    def get_all_with_inscriptions():
        """Récupère tous les modules avec le nombre d'inscrits"""
        query = """
            SELECT m.*, 
                   f.nom as formation_nom,
                   f.code as formation_code,
                   d.nom as departement_nom,
                   COUNT(i.id) as nb_inscrits
            FROM modules m
            JOIN formations f ON m.formation_id = f.id
            JOIN departements d ON f.dept_id = d.id
            LEFT JOIN inscriptions i ON m.id = i.module_id
            GROUP BY m.id
            ORDER BY d.nom, f.nom, m.nom
        """
        return execute_query(query, dictionary=True)

class EtudiantModel:
    """Gestion des étudiants"""
    
    @staticmethod
    def get_by_formation(formation_id):
        """Récupère tous les étudiants d'une formation"""
        query = """
            SELECT e.*, f.nom as formation_nom
            FROM etudiants e
            JOIN formations f ON e.formation_id = f.id
            WHERE e.formation_id = %s
            ORDER BY e.nom, e.prenom
        """
        return execute_query(query, (formation_id,), dictionary=True)
    
    @staticmethod
    def get_inscriptions(etudiant_id):
        """Récupère toutes les inscriptions d'un étudiant"""
        query = """
            SELECT i.*, m.nom as module_nom, m.code as module_code
            FROM inscriptions i
            JOIN modules m ON i.module_id = m.id
            WHERE i.etudiant_id = %s
            ORDER BY m.semestre
        """
        return execute_query(query, (etudiant_id,), dictionary=True)

class ProfesseurModel:
    """Gestion des professeurs"""
    
    @staticmethod
    def get_all(dept_id=None):
        """Récupère tous les professeurs"""
        if dept_id:
            query = """
                SELECT p.*, d.nom as departement_nom
                FROM professeurs p
                JOIN departements d ON p.dept_id = d.id
                WHERE p.dept_id = %s
                ORDER BY p.nom, p.prenom
            """
            return execute_query(query, (dept_id,), dictionary=True)
        else:
            query = """
                SELECT p.*, d.nom as departement_nom
                FROM professeurs p
                JOIN departements d ON p.dept_id = d.id
                ORDER BY d.nom, p.nom, p.prenom
            """
            return execute_query(query, dictionary=True)
    
    @staticmethod
    def get_charge_surveillance(prof_id, date_debut, date_fin):
        """Récupère la charge de surveillance d'un professeur sur une période"""
        query = """
            SELECT COUNT(*) as nb_surveillances
            FROM surveillances s
            JOIN examens e ON s.examen_id = e.id
            WHERE s.prof_id = %s
            AND e.date_examen BETWEEN %s AND %s
        """
        results = execute_query(query, (prof_id, date_debut, date_fin), dictionary=True)
        return results[0]['nb_surveillances'] if results else 0

class LieuExamenModel:
    """Gestion des lieux d'examen"""
    
    @staticmethod
    def get_all(type_lieu=None):
        """Récupère tous les lieux d'examen"""
        if type_lieu:
            query = """
                SELECT * FROM lieux_examen 
                WHERE type = %s
                ORDER BY capacite DESC, nom
            """
            return execute_query(query, (type_lieu,), dictionary=True)
        else:
            query = "SELECT * FROM lieux_examen ORDER BY type, capacite DESC"
            return execute_query(query, dictionary=True)
    
    @staticmethod
    def get_disponibles(date_examen, heure_debut, duree_minutes):
        """Récupère les lieux disponibles à une date et heure données"""
        heure_fin = (datetime.combine(datetime.today(), heure_debut) + 
                     timedelta(minutes=duree_minutes)).time()
        
        query = """
            SELECT l.*
            FROM lieux_examen l
            WHERE l.id NOT IN (
                SELECT e.lieu_id
                FROM examens e
                WHERE e.date_examen = %s
                AND (
                    (e.heure_debut <= %s AND ADDTIME(e.heure_debut, SEC_TO_TIME(e.duree_minutes * 60)) > %s)
                    OR (e.heure_debut < %s AND ADDTIME(e.heure_debut, SEC_TO_TIME(e.duree_minutes * 60)) >= %s)
                )
            )
            ORDER BY l.type, l.capacite DESC
        """
        return execute_query(query, (date_examen, heure_debut, heure_debut, heure_fin, heure_fin), 
                           dictionary=True)

class ExamenModel:
    """Gestion des examens"""
    
    @staticmethod
    def create(module_id, lieu_id, date_examen, heure_debut, duree_minutes, session, annee_universitaire):
        """Crée un nouvel examen"""
        # Compter le nombre d'inscrits
        query_inscrits = """
            SELECT COUNT(*) as nb FROM inscriptions WHERE module_id = %s
        """
        nb_inscrits = execute_query(query_inscrits, (module_id,), dictionary=True)[0]['nb']
        
        query = """
            INSERT INTO examens 
            (module_id, lieu_id, date_examen, heure_debut, duree_minutes, 
             session, annee_universitaire, nb_inscrits)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """
        execute_query(query, (module_id, lieu_id, date_examen, heure_debut, 
                             duree_minutes, session, annee_universitaire, nb_inscrits), 
                     fetch=False)
        
        # Récupérer l'ID de l'examen créé
        return execute_query("SELECT LAST_INSERT_ID() as id", dictionary=True)[0]['id']
    
    @staticmethod
    def get_all(date_debut=None, date_fin=None):
        """Récupère tous les examens"""
        if date_debut and date_fin:
            query = """
                SELECT e.*, 
                       m.nom as module_nom, m.code as module_code,
                       f.nom as formation_nom,
                       d.nom as departement_nom,
                       l.nom as lieu_nom, l.capacite as lieu_capacite
                FROM examens e
                JOIN modules m ON e.module_id = m.id
                JOIN formations f ON m.formation_id = f.id
                JOIN departements d ON f.dept_id = d.id
                JOIN lieux_examen l ON e.lieu_id = l.id
                WHERE e.date_examen BETWEEN %s AND %s
                ORDER BY e.date_examen, e.heure_debut
            """
            return execute_query(query, (date_debut, date_fin), dictionary=True)
        else:
            query = """
                SELECT e.*, 
                       m.nom as module_nom, m.code as module_code,
                       f.nom as formation_nom,
                       d.nom as departement_nom,
                       l.nom as lieu_nom, l.capacite as lieu_capacite
                FROM examens e
                JOIN modules m ON e.module_id = m.id
                JOIN formations f ON m.formation_id = f.id
                JOIN departements d ON f.dept_id = d.id
                JOIN lieux_examen l ON e.lieu_id = l.id
                ORDER BY e.date_examen, e.heure_debut
            """
            return execute_query(query, dictionary=True)
    
    @staticmethod
    def delete(examen_id):
        """Supprime un examen"""
        query = "DELETE FROM examens WHERE id = %s"
        execute_query(query, (examen_id,), fetch=False)

class SurveillanceModel:
    """Gestion des surveillances"""
    
    @staticmethod
    def assign(examen_id, prof_id, role='assistant'):
        """Assigne un professeur à la surveillance d'un examen"""
        query = """
            INSERT INTO surveillances (examen_id, prof_id, role)
            VALUES (%s, %s, %s)
        """
        execute_query(query, (examen_id, prof_id, role), fetch=False)
    
    @staticmethod
    def get_by_examen(examen_id):
        """Récupère tous les surveillants d'un examen"""
        query = """
            SELECT s.*, p.nom, p.prenom, p.dept_id
            FROM surveillances s
            JOIN professeurs p ON s.prof_id = p.id
            WHERE s.examen_id = %s
        """
        return execute_query(query, (examen_id,), dictionary=True)

class ConflitModel:
    """Gestion des conflits"""
    
    @staticmethod
    def create(type_conflit, description, severite, examen_id=None):
        """Enregistre un nouveau conflit"""
        query = """
            INSERT INTO conflits (type_conflit, description, severite, examen_id)
            VALUES (%s, %s, %s, %s)
        """
        execute_query(query, (type_conflit, description, severite, examen_id), fetch=False)
    
    @staticmethod
    def get_all(resolu=None):
        """Récupère tous les conflits"""
        if resolu is not None:
            query = """
                SELECT c.*, 
                       e.date_examen, e.heure_debut,
                       m.nom as module_nom
                FROM conflits c
                LEFT JOIN examens e ON c.examen_id = e.id
                LEFT JOIN modules m ON e.module_id = m.id
                WHERE c.resolu = %s
                ORDER BY c.severite, c.date_detection DESC
            """
            return execute_query(query, (resolu,), dictionary=True)
        else:
            query = """
                SELECT c.*, 
                       e.date_examen, e.heure_debut,
                       m.nom as module_nom
                FROM conflits c
                LEFT JOIN examens e ON c.examen_id = e.id
                LEFT JOIN modules m ON e.module_id = m.id
                ORDER BY c.resolu, c.severite, c.date_detection DESC
            """
            return execute_query(query, dictionary=True)
    
    @staticmethod
    def mark_resolved(conflit_id):
        """Marque un conflit comme résolu"""
        query = """
            UPDATE conflits 
            SET resolu = TRUE, date_resolution = NOW()
            WHERE id = %s
        """
        execute_query(query, (conflit_id,), fetch=False)
