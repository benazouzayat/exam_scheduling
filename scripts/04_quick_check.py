"""
Script de vérification rapide pour checker l'état de la base de données
Usage: python scripts/04_quick_check.py
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.database import execute_query

def quick_check():
    """Affiche un aperçu rapide de l'état de la base de données"""
    
    print("\n" + "="*60)
    print("  APERÇU RAPIDE DE LA BASE DE DONNÉES")
    print("="*60 + "\n")
    
    try:
        # Statistiques générales
        print("📊 STATISTIQUES GÉNÉRALES:\n")
        
        stats = {
            'Universités': 'SELECT COUNT(*) FROM universites',
            'Facultés': 'SELECT COUNT(*) FROM facultes',
            'Départements': 'SELECT COUNT(*) FROM departements',
            'Formations': 'SELECT COUNT(*) FROM formations',
            'Étudiants': 'SELECT COUNT(*) FROM etudiants',
            'Matières': 'SELECT COUNT(*) FROM matieres',
            'Enseignants': 'SELECT COUNT(*) FROM enseignants',
            'Salles': 'SELECT COUNT(*) FROM salles',
            'Inscriptions': 'SELECT COUNT(*) FROM inscriptions',
            'Examens planifiés': 'SELECT COUNT(*) FROM examens'
        }
        
        for label, query in stats.items():
            result = execute_query(query, fetch=True)
            count = result[0][0] if result else 0
            print(f"  {label:<20}: {count:>8,}")
        
        # Top 3 des départements par nombre d'étudiants
        print(f"\n{'='*60}")
        print("📈 TOP 3 DÉPARTEMENTS PAR NOMBRE D'ÉTUDIANTS:\n")
        
        query = """
            SELECT 
                d.nom as departement,
                COUNT(DISTINCT e.id) as nb_etudiants,
                COUNT(DISTINCT f.id) as nb_formations
            FROM departements d
            LEFT JOIN formations f ON d.id = f.departement_id
            LEFT JOIN etudiants e ON f.id = e.formation_id
            GROUP BY d.id, d.nom
            ORDER BY nb_etudiants DESC
            LIMIT 3
        """
        
        results = execute_query(query, fetch=True, dictionary=True)
        for i, row in enumerate(results, 1):
            print(f"  {i}. {row['departement']}")
            print(f"     Étudiants: {row['nb_etudiants']:,} | Formations: {row['nb_formations']}")
        
        # Répartition des salles par type
        print(f"\n{'='*60}")
        print("🏛️ RÉPARTITION DES SALLES PAR TYPE:\n")
        
        query = """
            SELECT 
                type_salle,
                COUNT(*) as nombre,
                SUM(capacite) as capacite_totale,
                AVG(capacite) as capacite_moyenne
            FROM salles
            GROUP BY type_salle
            ORDER BY nombre DESC
        """
        
        results = execute_query(query, fetch=True, dictionary=True)
        for row in results:
            print(f"  {row['type_salle']:<15}: {row['nombre']:>2} salles | "
                  f"Capacité totale: {int(row['capacite_totale']):>4} | "
                  f"Moyenne: {int(row['capacite_moyenne']):>3}")
        
        # Taux d'inscription moyen
        print(f"\n{'='*60}")
        print("📚 STATISTIQUES D'INSCRIPTIONS:\n")
        
        query = """
            SELECT 
                AVG(nb_inscriptions) as moy_inscriptions_par_etudiant,
                MAX(nb_inscriptions) as max_inscriptions,
                MIN(nb_inscriptions) as min_inscriptions
            FROM (
                SELECT etudiant_id, COUNT(*) as nb_inscriptions
                FROM inscriptions
                GROUP BY etudiant_id
            ) as sub
        """
        
        results = execute_query(query, fetch=True, dictionary=True)
        if results:
            row = results[0]
            print(f"  Moyenne d'inscriptions par étudiant: {row['moy_inscriptions_par_etudiant']:.1f}")
            print(f"  Maximum d'inscriptions: {row['max_inscriptions']}")
            print(f"  Minimum d'inscriptions: {row['min_inscriptions']}")
        
        # État de la planification des examens
        print(f"\n{'='*60}")
        print("📅 ÉTAT DE LA PLANIFICATION:\n")
        
        total_matieres = execute_query("SELECT COUNT(*) FROM matieres", fetch=True)[0][0]
        total_examens = execute_query("SELECT COUNT(*) FROM examens", fetch=True)[0][0]
        
        if total_examens > 0:
            taux = (total_examens / total_matieres * 100) if total_matieres > 0 else 0
            print(f"  Examens planifiés: {total_examens}/{total_matieres} ({taux:.1f}%)")
            
            # Répartition par statut
            query = "SELECT statut, COUNT(*) as nombre FROM examens GROUP BY statut"
            results = execute_query(query, fetch=True, dictionary=True)
            for row in results:
                print(f"    {row['statut']}: {row['nombre']}")
        else:
            print("  Aucun examen planifié pour le moment")
            print("  Utilisez la fonction optimize_schedule() pour générer l'emploi du temps")
        
        print(f"\n{'='*60}")
        print("✓ Vérification terminée avec succès!")
        print("="*60 + "\n")
        
    except Exception as e:
        print(f"\n✗ Erreur lors de la vérification: {str(e)}\n")
        exit(1)

if __name__ == "__main__":
    quick_check()
