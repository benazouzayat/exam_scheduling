"""
Module d'analyse et de statistiques pour le dashboard
"""

from backend.database import execute_query
from datetime import datetime

class Analytics:
    """Génération de statistiques et KPIs"""
    
    @staticmethod
    def get_global_stats():
        """Statistiques globales de la faculté"""
        stats = {}
        
        # Nombre total d'étudiants
        result = execute_query("SELECT COUNT(*) as total FROM etudiants", dictionary=True)
        stats['nb_etudiants'] = result[0]['total']
        
        # Nombre de départements
        result = execute_query("SELECT COUNT(*) as total FROM departements", dictionary=True)
        stats['nb_departements'] = result[0]['total']
        
        # Nombre de formations
        result = execute_query("SELECT COUNT(*) as total FROM formations", dictionary=True)
        stats['nb_formations'] = result[0]['total']
        
        # Nombre de professeurs
        result = execute_query("SELECT COUNT(*) as total FROM professeurs", dictionary=True)
        stats['nb_professeurs'] = result[0]['total']
        
        # Nombre de modules
        result = execute_query("SELECT COUNT(*) as total FROM modules", dictionary=True)
        stats['nb_modules'] = result[0]['total']
        
        # Nombre de lieux d'examen
        result = execute_query("SELECT COUNT(*) as total FROM lieux_examen", dictionary=True)
        stats['nb_lieux'] = result[0]['total']
        
        # Capacité totale
        result = execute_query("SELECT SUM(capacite) as total FROM lieux_examen", dictionary=True)
        stats['capacite_totale'] = result[0]['total']
        
        return stats
    
    @staticmethod
    def get_occupation_stats(date_debut, date_fin):
        """Statistiques d'occupation des salles et amphis"""
        query = """
            SELECT 
                l.type,
                COUNT(DISTINCT e.id) as nb_examens_planifies,
                SUM(e.nb_inscrits) as nb_places_utilisees,
                (SELECT COUNT(*) FROM lieux_examen WHERE type = l.type) as nb_lieux_total,
                (SELECT SUM(capacite) FROM lieux_examen WHERE type = l.type) as capacite_totale
            FROM lieux_examen l
            LEFT JOIN examens e ON l.id = e.lieu_id 
                AND e.date_examen BETWEEN %s AND %s
            GROUP BY l.type
        """
        results = execute_query(query, (date_debut, date_fin), dictionary=True)
        
        stats = {}
        for row in results:
            type_lieu = row['type']
            stats[type_lieu] = {
                'nb_examens': row['nb_examens_planifies'] or 0,
                'nb_places_utilisees': row['nb_places_utilisees'] or 0,
                'nb_lieux_total': row['nb_lieux_total'],
                'capacite_totale': row['capacite_totale'],
                'taux_utilisation': (row['nb_places_utilisees'] / row['capacite_totale'] * 100) 
                                   if row['capacite_totale'] > 0 else 0
            }
        
        return stats
    
    @staticmethod
    def get_conflicts_by_type():
        """Statistiques des conflits par type"""
        query = """
            SELECT 
                type_conflit,
                severite,
                COUNT(*) as nb_conflits,
                SUM(CASE WHEN resolu = TRUE THEN 1 ELSE 0 END) as nb_resolus
            FROM conflits
            GROUP BY type_conflit, severite
            ORDER BY 
                FIELD(severite, 'critique', 'elevee', 'moyenne', 'faible'),
                nb_conflits DESC
        """
        return execute_query(query, dictionary=True)
    
    @staticmethod
    def get_department_stats():
        """Statistiques par département"""
        query = """
            SELECT 
                d.nom as departement,
                COUNT(DISTINCT f.id) as nb_formations,
                COUNT(DISTINCT e.id) as nb_etudiants,
                COUNT(DISTINCT p.id) as nb_professeurs,
                COUNT(DISTINCT m.id) as nb_modules,
                COUNT(DISTINCT ex.id) as nb_examens_planifies
            FROM departements d
            LEFT JOIN formations f ON d.id = f.dept_id
            LEFT JOIN etudiants e ON f.id = e.formation_id
            LEFT JOIN professeurs p ON d.id = p.dept_id
            LEFT JOIN modules m ON f.id = m.formation_id
            LEFT JOIN examens ex ON m.id = ex.module_id
            GROUP BY d.id, d.nom
            ORDER BY d.nom
        """
        return execute_query(query, dictionary=True)
    
    @staticmethod
    def get_professor_workload(date_debut, date_fin):
        """Charge de travail des professeurs (surveillances)"""
        query = """
            SELECT 
                p.nom,
                p.prenom,
                d.nom as departement,
                COUNT(s.id) as nb_surveillances,
                COUNT(DISTINCT DATE(e.date_examen)) as nb_jours
            FROM professeurs p
            LEFT JOIN surveillances s ON p.id = s.prof_id
            LEFT JOIN examens e ON s.examen_id = e.id 
                AND e.date_examen BETWEEN %s AND %s
            JOIN departements d ON p.dept_id = d.id
            GROUP BY p.id
            ORDER BY nb_surveillances DESC
            LIMIT 50
        """
        return execute_query(query, (date_debut, date_fin), dictionary=True)
    
    @staticmethod
    def get_daily_schedule(date_examen):
        """Emploi du temps détaillé pour une journée"""
        query = """
            SELECT 
                e.heure_debut,
                e.duree_minutes,
                m.nom as module_nom,
                m.code as module_code,
                f.nom as formation_nom,
                d.nom as departement_nom,
                l.nom as lieu_nom,
                l.type as lieu_type,
                e.nb_inscrits,
                l.capacite,
                GROUP_CONCAT(CONCAT(pr.nom, ' ', pr.prenom) SEPARATOR ', ') as surveillants
            FROM examens e
            JOIN modules m ON e.module_id = m.id
            JOIN formations f ON m.formation_id = f.id
            JOIN departements d ON f.dept_id = d.id
            JOIN lieux_examen l ON e.lieu_id = l.id
            LEFT JOIN surveillances s ON e.id = s.examen_id
            LEFT JOIN professeurs pr ON s.prof_id = pr.id
            WHERE e.date_examen = %s
            GROUP BY e.id
            ORDER BY e.heure_debut, l.nom
        """
        return execute_query(query, (date_examen,), dictionary=True)
