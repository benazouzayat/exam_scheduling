-- Script de création de la base de données pour la plateforme d'optimisation des emplois du temps
-- SGBD: MySQL
-- Version: 1.0

-- Création de la base de données
CREATE DATABASE IF NOT EXISTS exam_scheduling CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE exam_scheduling;

-- Table des départements
CREATE TABLE departements (
    id INT AUTO_INCREMENT PRIMARY KEY,
    nom VARCHAR(100) NOT NULL UNIQUE,
    code VARCHAR(10) NOT NULL UNIQUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
) ENGINE=InnoDB;

-- Table des formations
CREATE TABLE formations (
    id INT AUTO_INCREMENT PRIMARY KEY,
    nom VARCHAR(200) NOT NULL,
    code VARCHAR(20) NOT NULL UNIQUE,
    dept_id INT NOT NULL,
    nb_modules INT NOT NULL DEFAULT 6,
    niveau VARCHAR(20) NOT NULL, -- Licence, Master, Doctorat
    annee INT NOT NULL, -- 1, 2, 3
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (dept_id) REFERENCES departements(id) ON DELETE CASCADE,
    INDEX idx_dept (dept_id)
) ENGINE=InnoDB;

-- Table des professeurs
CREATE TABLE professeurs (
    id INT AUTO_INCREMENT PRIMARY KEY,
    nom VARCHAR(100) NOT NULL,
    prenom VARCHAR(100) NOT NULL,
    email VARCHAR(150) NOT NULL UNIQUE,
    telephone VARCHAR(20),
    dept_id INT NOT NULL,
    specialite VARCHAR(200),
    grade VARCHAR(50), -- Professeur, Maître de conférences, etc.
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (dept_id) REFERENCES departements(id) ON DELETE CASCADE,
    INDEX idx_dept (dept_id),
    INDEX idx_nom_prenom (nom, prenom)
) ENGINE=InnoDB;

-- Table des modules
CREATE TABLE modules (
    id INT AUTO_INCREMENT PRIMARY KEY,
    nom VARCHAR(200) NOT NULL,
    code VARCHAR(20) NOT NULL UNIQUE,
    credits INT NOT NULL DEFAULT 3,
    formation_id INT NOT NULL,
    semestre INT NOT NULL, -- 1 ou 2
    pre_req_id INT NULL, -- Module prérequis (optionnel)
    prof_responsable_id INT NULL,
    duree_examen_minutes INT NOT NULL DEFAULT 120,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (formation_id) REFERENCES formations(id) ON DELETE CASCADE,
    FOREIGN KEY (pre_req_id) REFERENCES modules(id) ON DELETE SET NULL,
    FOREIGN KEY (prof_responsable_id) REFERENCES professeurs(id) ON DELETE SET NULL,
    INDEX idx_formation (formation_id),
    INDEX idx_code (code)
) ENGINE=InnoDB;

-- Table des étudiants
CREATE TABLE etudiants (
    id INT AUTO_INCREMENT PRIMARY KEY,
    nom VARCHAR(100) NOT NULL,
    prenom VARCHAR(100) NOT NULL,
    email VARCHAR(150) NOT NULL UNIQUE,
    numero_etudiant VARCHAR(20) NOT NULL UNIQUE,
    formation_id INT NOT NULL,
    annee_inscription INT NOT NULL, -- Année d'inscription (2020, 2021, etc.)
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (formation_id) REFERENCES formations(id) ON DELETE CASCADE,
    INDEX idx_formation (formation_id),
    INDEX idx_numero (numero_etudiant),
    INDEX idx_nom_prenom (nom, prenom)
) ENGINE=InnoDB;

-- Table des lieux d'examen (salles et amphis)
CREATE TABLE lieux_examen (
    id INT AUTO_INCREMENT PRIMARY KEY,
    nom VARCHAR(100) NOT NULL,
    capacite INT NOT NULL,
    type ENUM('amphi', 'salle') NOT NULL,
    batiment VARCHAR(50) NOT NULL,
    equipements TEXT, -- Projecteur, Ordinateurs, etc.
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_type (type),
    INDEX idx_capacite (capacite)
) ENGINE=InnoDB;

-- Table des inscriptions (relation étudiants-modules)
CREATE TABLE inscriptions (
    id INT AUTO_INCREMENT PRIMARY KEY,
    etudiant_id INT NOT NULL,
    module_id INT NOT NULL,
    annee_universitaire VARCHAR(20) NOT NULL, -- Ex: 2023-2024
    note DECIMAL(4,2) NULL,
    statut ENUM('inscrit', 'valide', 'echoue', 'absent') DEFAULT 'inscrit',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (etudiant_id) REFERENCES etudiants(id) ON DELETE CASCADE,
    FOREIGN KEY (module_id) REFERENCES modules(id) ON DELETE CASCADE,
    UNIQUE KEY unique_inscription (etudiant_id, module_id, annee_universitaire),
    INDEX idx_etudiant (etudiant_id),
    INDEX idx_module (module_id)
) ENGINE=InnoDB;

-- Table des examens
CREATE TABLE examens (
    id INT AUTO_INCREMENT PRIMARY KEY,
    module_id INT NOT NULL,
    lieu_id INT NOT NULL,
    date_examen DATE NOT NULL,
    heure_debut TIME NOT NULL,
    duree_minutes INT NOT NULL DEFAULT 120,
    session VARCHAR(20) NOT NULL, -- Normale, Rattrapage
    annee_universitaire VARCHAR(20) NOT NULL,
    statut ENUM('planifie', 'valide', 'termine', 'annule') DEFAULT 'planifie',
    nb_inscrits INT DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (module_id) REFERENCES modules(id) ON DELETE CASCADE,
    FOREIGN KEY (lieu_id) REFERENCES lieux_examen(id) ON DELETE CASCADE,
    INDEX idx_date (date_examen),
    INDEX idx_module (module_id),
    INDEX idx_lieu (lieu_id),
    INDEX idx_date_heure (date_examen, heure_debut)
) ENGINE=InnoDB;

-- Table des surveillances (relation professeurs-examens)
CREATE TABLE surveillances (
    id INT AUTO_INCREMENT PRIMARY KEY,
    examen_id INT NOT NULL,
    prof_id INT NOT NULL,
    role ENUM('principal', 'assistant') DEFAULT 'assistant',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (examen_id) REFERENCES examens(id) ON DELETE CASCADE,
    FOREIGN KEY (prof_id) REFERENCES professeurs(id) ON DELETE CASCADE,
    UNIQUE KEY unique_surveillance (examen_id, prof_id),
    INDEX idx_examen (examen_id),
    INDEX idx_prof (prof_id)
) ENGINE=InnoDB;

-- Table des conflits détectés
CREATE TABLE conflits (
    id INT AUTO_INCREMENT PRIMARY KEY,
    type_conflit ENUM('etudiant_multiple', 'prof_surcharge', 'salle_capacite', 'salle_double', 'autre') NOT NULL,
    description TEXT NOT NULL,
    severite ENUM('critique', 'elevee', 'moyenne', 'faible') NOT NULL,
    examen_id INT NULL,
    resolu BOOLEAN DEFAULT FALSE,
    date_detection TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    date_resolution TIMESTAMP NULL,
    FOREIGN KEY (examen_id) REFERENCES examens(id) ON DELETE CASCADE,
    INDEX idx_resolu (resolu),
    INDEX idx_type (type_conflit)
) ENGINE=InnoDB;

-- Table de logs pour tracer les opérations importantes
CREATE TABLE logs_operations (
    id INT AUTO_INCREMENT PRIMARY KEY,
    operation VARCHAR(100) NOT NULL,
    utilisateur VARCHAR(100),
    details TEXT,
    duree_ms INT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_operation (operation),
    INDEX idx_created (created_at)
) ENGINE=InnoDB;
