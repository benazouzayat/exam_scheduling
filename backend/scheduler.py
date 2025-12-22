"""
Module d'optimisation et de génération automatique des emplois du temps d'examens
"""

import time
from datetime import datetime, timedelta, time as dt_time
from backend.models import (
    ModuleModel, LieuExamenModel, ExamenModel, ProfesseurModel,
    SurveillanceModel, ConflitModel, DepartementModel
)
from backend.database import execute_query

class ExamScheduler:
    """Générateur automatique d'emplois du temps d'examens"""
    
    def __init__(self, date_debut, date_fin, session="Normale", annee_universitaire="2024-2025"):
        self.date_debut = date_debut
        self.date_fin = date_fin
        self.session = session
        self.annee_universitaire = annee_universitaire
        self.conflits = []
        
        # Horaires des examens (créneaux possibles)
        self.creneaux = [
            dt_time(8, 0),   # 8h00
            dt_time(10, 30), # 10h30
            dt_time(14, 0),  # 14h00
        ]
    
    def generate_schedule(self):
        """
        Génère un emploi du temps complet pour tous les modules
        Retourne le temps d'exécution et le nombre d'examens planifiés
        """
        start_time = time.time()
        
        print("\n🚀 Démarrage de la génération automatique...")
        
        # 1. Nettoyer les examens existants pour la période
        self._clean_existing_exams()
        
        # 2. Récupérer tous les modules à planifier
        modules = ModuleModel.get_all_with_inscriptions()
        print(f"📚 {len(modules)} modules à planifier")
        
        # 3. Trier les modules par priorité (nb d'inscrits décroissant)
        modules_sorted = sorted(modules, key=lambda m: m['nb_inscrits'], reverse=True)
        
        # 4. Planifier chaque module
        examens_planifies = 0
        dates_disponibles = self._get_dates_disponibles()
        
        for module in modules_sorted:
            success = self._schedule_module(module, dates_disponibles)
            if success:
                examens_planifies += 1
            
            # Afficher la progression
            if examens_planifies % 50 == 0:
                print(f"  ✓ {examens_planifies}/{len(modules)} examens planifiés...")
        
        # 5. Détecter les conflits
        self._detect_conflicts()
        
        # 6. Assigner les surveillances
        self._assign_surveillances()
        
        execution_time = time.time() - start_time
        
        print(f"\n✅ Génération terminée en {execution_time:.2f} secondes")
        print(f"📊 {examens_planifies} examens planifiés")
        print(f"⚠️  {len(self.conflits)} conflits détectés")
        
        return {
            'execution_time': execution_time,
            'nb_examens': examens_planifies,
            'nb_conflits': len(self.conflits),
            'success': execution_time < 45  # Objectif: < 45 secondes
        }
    
    def _clean_existing_exams(self):
        """Supprime les examens existants pour la période"""
        query = """
            DELETE FROM examens 
            WHERE date_examen BETWEEN %s AND %s
            AND session = %s
        """
        execute_query(query, (self.date_debut, self.date_fin, self.session), fetch=False)
        print("🧹 Examens existants nettoyés")
    
    def _get_dates_disponibles(self):
        """Génère la liste des dates disponibles (excluant weekends)"""
        dates = []
        current_date = self.date_debut
        
        while current_date <= self.date_fin:
            # Exclure les weekends (5 = samedi, 6 = dimanche)
            if current_date.weekday() < 5:
                dates.append(current_date)
            current_date += timedelta(days=1)
        
        return dates
    
    def _schedule_module(self, module, dates_disponibles):
        """
        Planifie un module spécifique
        Retourne True si la planification a réussi
        """
        module_id = module['id']
        nb_inscrits = module['nb_inscrits']
        duree = module['duree_examen_minutes']
        
        # Essayer chaque date et chaque créneau
        for date_exam in dates_disponibles:
            for creneau in self.creneaux:
                # Vérifier si des étudiants ont déjà un examen ce jour-là
                if self._check_student_conflict(module_id, date_exam):
                    continue
                
                # Trouver un lieu disponible avec capacité suffisante
                lieu = self._find_available_lieu(date_exam, creneau, duree, nb_inscrits)
                
                if lieu:
                    # Créer l'examen
                    ExamenModel.create(
                        module_id=module_id,
                        lieu_id=lieu['id'],
                        date_examen=date_exam,
                        heure_debut=creneau,
                        duree_minutes=duree,
                        session=self.session,
                        annee_universitaire=self.annee_universitaire
                    )
                    return True
        
        # Impossible de planifier ce module
        ConflitModel.create(
            type_conflit='autre',
            description=f"Impossible de planifier le module {module['code']} - {module['nom']}",
            severite='critique'
        )
        self.conflits.append(f"Module {module['code']} non planifié")
        return False
    
    def _check_student_conflict(self, module_id, date_exam):
        """
        Vérifie si des étudiants inscrits au module ont déjà un examen ce jour-là
        Contrainte: Maximum 1 examen par jour par étudiant
        """
        query = """
            SELECT COUNT(*) as nb_conflicts
            FROM inscriptions i1
            JOIN inscriptions i2 ON i1.etudiant_id = i2.etudiant_id
            JOIN examens e ON i2.module_id = e.module_id
            WHERE i1.module_id = %s
            AND e.date_examen = %s
            AND i2.module_id != %s
        """
        result = execute_query(query, (module_id, date_exam, module_id), dictionary=True)
        return result[0]['nb_conflicts'] > 0
    
    def _find_available_lieu(self, date_exam, heure_debut, duree_minutes, nb_inscrits):
        """
        Trouve un lieu disponible avec une capacité suffisante
        Priorité: amphis pour grands groupes, salles pour petits groupes
        """
        lieux_disponibles = LieuExamenModel.get_disponibles(
            date_exam, heure_debut, duree_minutes
        )
        
        # Filtrer par capacité suffisante
        lieux_adequats = [l for l in lieux_disponibles if l['capacite'] >= nb_inscrits]
        
        if not lieux_adequats:
            return None
        
        # Choisir le lieu le plus adapté (capacité la plus proche du besoin)
        lieu_optimal = min(lieux_adequats, key=lambda l: l['capacite'] - nb_inscrits)
        return lieu_optimal
    
    def _detect_conflicts(self):
        """Détecte tous les types de conflits dans le planning généré"""
        print("\n🔍 Détection des conflits...")
        
        # Conflits de capacité des salles
        self._detect_capacity_conflicts()
        
        # Conflits d'occupation des salles
        self._detect_room_double_booking()
        
        # Conflits étudiants (plusieurs examens le même jour)
        self._detect_student_conflicts()
    
    def _detect_capacity_conflicts(self):
        """Détecte les examens où le lieu est trop petit"""
        query = """
            SELECT e.id, e.nb_inscrits, l.capacite, l.nom as lieu_nom,
                   m.nom as module_nom, e.date_examen
            FROM examens e
            JOIN lieux_examen l ON e.lieu_id = l.id
            JOIN modules m ON e.module_id = m.id
            WHERE e.nb_inscrits > l.capacite
            AND e.date_examen BETWEEN %s AND %s
        """
        conflits = execute_query(query, (self.date_debut, self.date_fin), dictionary=True)
        
        for conflit in conflits:
            description = (f"Capacité insuffisante pour {conflit['module_nom']} "
                         f"le {conflit['date_examen']}: "
                         f"{conflit['nb_inscrits']} inscrits pour {conflit['capacite']} places "
                         f"dans {conflit['lieu_nom']}")
            
            ConflitModel.create(
                type_conflit='salle_capacite',
                description=description,
                severite='critique',
                examen_id=conflit['id']
            )
            self.conflits.append(description)
    
    def _detect_room_double_booking(self):
        """Détecte les salles réservées pour plusieurs examens simultanés"""
        query = """
            SELECT l.nom, e1.date_examen, e1.heure_debut,
                   COUNT(*) as nb_examens
            FROM examens e1
            JOIN examens e2 ON e1.lieu_id = e2.lieu_id 
                AND e1.date_examen = e2.date_examen
                AND e1.id != e2.id
            JOIN lieux_examen l ON e1.lieu_id = l.id
            WHERE e1.date_examen BETWEEN %s AND %s
            AND (
                (e1.heure_debut <= e2.heure_debut 
                 AND ADDTIME(e1.heure_debut, SEC_TO_TIME(e1.duree_minutes * 60)) > e2.heure_debut)
                OR (e2.heure_debut <= e1.heure_debut 
                    AND ADDTIME(e2.heure_debut, SEC_TO_TIME(e2.duree_minutes * 60)) > e1.heure_debut)
            )
            GROUP BY l.id, e1.date_examen, e1.heure_debut
            HAVING COUNT(*) > 1
        """
        conflits = execute_query(query, (self.date_debut, self.date_fin), dictionary=True)
        
        for conflit in conflits:
            description = (f"Salle {conflit['nom']} réservée pour {conflit['nb_examens']} "
                         f"examens simultanés le {conflit['date_examen']} à {conflit['heure_debut']}")
            
            ConflitModel.create(
                type_conflit='salle_double',
                description=description,
                severite='critique'
            )
            self.conflits.append(description)
    
    def _detect_student_conflicts(self):
        """Détecte les étudiants avec plusieurs examens le même jour"""
        query = """
            SELECT e1.id, et.nom, et.prenom, e1.date_examen,
                   COUNT(DISTINCT e2.id) as nb_examens
            FROM etudiants et
            JOIN inscriptions i1 ON et.id = i1.etudiant_id
            JOIN examens e1 ON i1.module_id = e1.module_id
            JOIN inscriptions i2 ON et.id = i2.etudiant_id
            JOIN examens e2 ON i2.module_id = e2.module_id
            WHERE e1.date_examen = e2.date_examen
            AND e1.id != e2.id
            AND e1.date_examen BETWEEN %s AND %s
            GROUP BY et.id, e1.date_examen
            HAVING COUNT(DISTINCT e2.id) > 1
            LIMIT 100
        """
        conflits = execute_query(query, (self.date_debut, self.date_fin), dictionary=True)
        
        for conflit in conflits:
            description = (f"Étudiant {conflit['nom']} {conflit['prenom']} "
                         f"a {conflit['nb_examens']} examens le {conflit['date_examen']}")
            
            ConflitModel.create(
                type_conflit='etudiant_multiple',
                description=description,
                severite='elevee',
                examen_id=conflit['id']
            )
            self.conflits.append(description)
    
    def _assign_surveillances(self):
        """
        Assigne les surveillances aux professeurs
        Contraintes:
        - Maximum 3 examens par jour par professeur
        - Priorité au département
        - Équilibrage de la charge
        """
        print("\n👮 Attribution des surveillances...")
        
        # Récupérer tous les examens planifiés
        examens = ExamenModel.get_all(self.date_debut, self.date_fin)
        
        # Récupérer tous les professeurs par département
        departements = DepartementModel.get_all()
        profs_by_dept = {}
        for dept in departements:
            profs_by_dept[dept['id']] = ProfesseurModel.get_all(dept['id'])
        
        # Pour chaque examen, assigner 2 surveillants
        surveillances_assigned = 0
        
        for examen in examens:
            dept_id = self._get_dept_id_from_exam(examen['id'])
            
            # Trouver 2 professeurs disponibles (priorité au département)
            profs_dept = profs_by_dept.get(dept_id, [])
            profs_autres = [p for dept_profs in profs_by_dept.values() 
                           for p in dept_profs if p['dept_id'] != dept_id]
            
            assigned_profs = []
            
            # Essayer d'abord les profs du département
            for prof in profs_dept:
                if len(assigned_profs) >= 2:
                    break
                if self._can_assign_prof(prof['id'], examen['date_examen']):
                    SurveillanceModel.assign(
                        examen['id'], 
                        prof['id'],
                        'principal' if len(assigned_profs) == 0 else 'assistant'
                    )
                    assigned_profs.append(prof['id'])
                    surveillances_assigned += 1
            
            # Si pas assez de profs du département, chercher dans les autres
            if len(assigned_profs) < 2:
                for prof in profs_autres:
                    if len(assigned_profs) >= 2:
                        break
                    if self._can_assign_prof(prof['id'], examen['date_examen']):
                        SurveillanceModel.assign(
                            examen['id'],
                            prof['id'],
                            'assistant'
                        )
                        assigned_profs.append(prof['id'])
                        surveillances_assigned += 1
        
        print(f"✓ {surveillances_assigned} surveillances attribuées")
    
    def _get_dept_id_from_exam(self, examen_id):
        """Récupère l'ID du département d'un examen"""
        query = """
            SELECT d.id
            FROM examens e
            JOIN modules m ON e.module_id = m.id
            JOIN formations f ON m.formation_id = f.id
            JOIN departements d ON f.dept_id = d.id
            WHERE e.id = %s
        """
        result = execute_query(query, (examen_id,), dictionary=True)
        return result[0]['id'] if result else None
    
    def _can_assign_prof(self, prof_id, date_examen):
        """
        Vérifie si un professeur peut être assigné à un examen
        Contrainte: Maximum 3 examens par jour
        """
        nb_surveillances = ProfesseurModel.get_charge_surveillance(
            prof_id, date_examen, date_examen
        )
        return nb_surveillances < 3

def optimize_schedule(date_debut, date_fin):
    """
    Fonction principale pour optimiser un emploi du temps
    """
    scheduler = ExamScheduler(date_debut, date_fin)
    return scheduler.generate_schedule()
