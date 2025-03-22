"""
Module d'audit de sécurité pour Polyad
Fournit des fonctionnalités pour auditer et surveiller la sécurité du système
"""

import os
import json
import logging
import datetime
import hashlib
import socket
import platform
import psutil
import sqlite3
import asyncio
from pathlib import Path

# Configuration du logger
logger = logging.getLogger(__name__)

class SecurityAudit:
    """
    Classe pour gérer les audits de sécurité du système
    """
    
    def __init__(self, config=None):
        """
        Initialise l'auditeur de sécurité
        
        Args:
            config (dict, optional): Configuration de l'auditeur
        """
        self.config = config or {}
        self.audit_db_path = self.config.get('audit_db_path', 'data/security/audit.db')
        self.log_path = self.config.get('log_path', 'logs/security')
        self.audit_interval = self.config.get('audit_interval', 3600)  # 1 heure par défaut
        self.max_log_size = self.config.get('max_log_size', 10 * 1024 * 1024)  # 10 Mo par défaut
        self.max_log_files = self.config.get('max_log_files', 10)
        
        # Créer les répertoires nécessaires
        os.makedirs(os.path.dirname(self.audit_db_path), exist_ok=True)
        os.makedirs(self.log_path, exist_ok=True)
        
        # Initialiser la base de données d'audit
        self._init_db()
        
        # Flag pour le thread d'audit en cours
        self.is_running = False
        self.audit_task = None
    
    def _init_db(self):
        """
        Initialise la base de données d'audit
        """
        conn = sqlite3.connect(self.audit_db_path)
        cursor = conn.cursor()
        
        # Table des événements d'audit
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS audit_events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            event_type TEXT NOT NULL,
            severity TEXT NOT NULL,
            source TEXT NOT NULL,
            description TEXT NOT NULL,
            details TEXT,
            hash TEXT NOT NULL
        )
        ''')
        
        # Table des vulnérabilités détectées
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS vulnerabilities (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            name TEXT NOT NULL,
            severity TEXT NOT NULL,
            description TEXT NOT NULL,
            affected_component TEXT NOT NULL,
            status TEXT NOT NULL,
            remediation TEXT,
            details TEXT
        )
        ''')
        
        # Table des tentatives d'accès
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS access_attempts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            username TEXT NOT NULL,
            ip_address TEXT NOT NULL,
            user_agent TEXT,
            endpoint TEXT NOT NULL,
            method TEXT NOT NULL,
            status TEXT NOT NULL,
            details TEXT
        )
        ''')
        
        conn.commit()
        conn.close()
        
        logger.info("Base de données d'audit initialisée")
    
    async def start_audit_loop(self):
        """
        Démarre la boucle d'audit périodique
        """
        if self.is_running:
            logger.warning("La boucle d'audit est déjà en cours d'exécution")
            return
        
        self.is_running = True
        logger.info(f"Démarrage de la boucle d'audit (intervalle: {self.audit_interval}s)")
        
        self.audit_task = asyncio.create_task(self._audit_loop())
    
    async def stop_audit_loop(self):
        """
        Arrête la boucle d'audit périodique
        """
        if not self.is_running:
            logger.warning("La boucle d'audit n'est pas en cours d'exécution")
            return
        
        self.is_running = False
        if self.audit_task:
            self.audit_task.cancel()
            try:
                await self.audit_task
            except asyncio.CancelledError:
                pass
            self.audit_task = None
        
        logger.info("Arrêt de la boucle d'audit")
    
    async def _audit_loop(self):
        """
        Boucle d'audit périodique
        """
        try:
            while self.is_running:
                await self.perform_security_audit()
                await asyncio.sleep(self.audit_interval)
        except asyncio.CancelledError:
            logger.info("Boucle d'audit annulée")
        except Exception as e:
            logger.error(f"Erreur dans la boucle d'audit: {e}")
            self.is_running = False
    
    async def perform_security_audit(self):
        """
        Effectue un audit de sécurité complet du système
        
        Returns:
            dict: Résultats de l'audit
        """
        logger.info("Début de l'audit de sécurité")
        
        audit_results = {
            'timestamp': datetime.datetime.utcnow().isoformat(),
            'system_info': self._get_system_info(),
            'file_integrity': await self._check_file_integrity(),
            'permissions': await self._check_permissions(),
            'network': await self._check_network(),
            'dependencies': await self._check_dependencies(),
            'logs': await self._analyze_logs(),
            'vulnerabilities': []
        }
        
        # Enregistrer les résultats
        self._save_audit_results(audit_results)
        
        # Détecter les vulnérabilités
        vulnerabilities = self._detect_vulnerabilities(audit_results)
        audit_results['vulnerabilities'] = vulnerabilities
        
        # Journaliser les vulnérabilités
        for vuln in vulnerabilities:
            self.log_vulnerability(vuln)
        
        logger.info(f"Audit de sécurité terminé: {len(vulnerabilities)} vulnérabilités détectées")
        
        return audit_results
    
    def _get_system_info(self):
        """
        Récupère les informations système
        
        Returns:
            dict: Informations système
        """
        return {
            'hostname': socket.gethostname(),
            'platform': platform.platform(),
            'python_version': platform.python_version(),
            'cpu_count': psutil.cpu_count(),
            'memory_total': psutil.virtual_memory().total,
            'disk_usage': {path.mountpoint: psutil.disk_usage(path.mountpoint).percent 
                          for path in psutil.disk_partitions() if os.path.exists(path.mountpoint)},
            'users': [user.name for user in psutil.users()],
            'boot_time': datetime.datetime.fromtimestamp(psutil.boot_time()).isoformat()
        }
    
    async def _check_file_integrity(self):
        """
        Vérifie l'intégrité des fichiers critiques
        
        Returns:
            dict: Résultats de la vérification
        """
        critical_files = [
            'run_api.py',
            'run_dashboard.py',
            'api/app.py',
            'core/autonomous_agent.py',
            'core/security/encryption.py',
            'core/security/audit.py'
        ]
        
        results = {
            'checked_files': 0,
            'modified_files': []
        }
        
        # Charger les hachages précédents
        hashes_file = os.path.join(os.path.dirname(self.audit_db_path), 'file_hashes.json')
        previous_hashes = {}
        
        if os.path.exists(hashes_file):
            try:
                with open(hashes_file, 'r') as f:
                    previous_hashes = json.load(f)
            except Exception as e:
                logger.error(f"Erreur lors du chargement des hachages précédents: {e}")
        
        # Calculer les hachages actuels
        current_hashes = {}
        
        for file_path in critical_files:
            full_path = os.path.abspath(file_path)
            if os.path.exists(full_path):
                try:
                    with open(full_path, 'rb') as f:
                        file_hash = hashlib.sha256(f.read()).hexdigest()
                        current_hashes[file_path] = file_hash
                        
                        # Vérifier si le fichier a été modifié
                        if file_path in previous_hashes and previous_hashes[file_path] != file_hash:
                            results['modified_files'].append({
                                'path': file_path,
                                'previous_hash': previous_hashes[file_path],
                                'current_hash': file_hash
                            })
                        
                        results['checked_files'] += 1
                except Exception as e:
                    logger.error(f"Erreur lors du calcul du hachage pour {file_path}: {e}")
        
        # Sauvegarder les hachages actuels
        try:
            with open(hashes_file, 'w') as f:
                json.dump(current_hashes, f, indent=2)
        except Exception as e:
            logger.error(f"Erreur lors de la sauvegarde des hachages: {e}")
        
        return results
    
    async def _check_permissions(self):
        """
        Vérifie les permissions des fichiers et répertoires critiques
        
        Returns:
            dict: Résultats de la vérification
        """
        critical_paths = [
            'data',
            'config',
            'api/app.py',
            'core/autonomous_agent.py',
            'core/security'
        ]
        
        results = {
            'checked_paths': 0,
            'permission_issues': []
        }
        
        for path in critical_paths:
            full_path = os.path.abspath(path)
            if os.path.exists(full_path):
                try:
                    stat_info = os.stat(full_path)
                    mode = stat_info.st_mode
                    
                    # Vérifier les permissions trop ouvertes
                    if mode & 0o002:  # Écriture pour tous
                        results['permission_issues'].append({
                            'path': path,
                            'issue': 'world_writable',
                            'mode': oct(mode)
                        })
                    
                    results['checked_paths'] += 1
                except Exception as e:
                    logger.error(f"Erreur lors de la vérification des permissions pour {path}: {e}")
        
        return results
    
    async def _check_network(self):
        """
        Vérifie la sécurité réseau
        
        Returns:
            dict: Résultats de la vérification
        """
        results = {
            'open_ports': [],
            'active_connections': []
        }
        
        # Vérifier les ports ouverts
        try:
            for conn in psutil.net_connections(kind='inet'):
                if conn.status == 'LISTEN':
                    results['open_ports'].append({
                        'port': conn.laddr.port,
                        'address': conn.laddr.ip,
                        'pid': conn.pid,
                        'program': psutil.Process(conn.pid).name() if conn.pid else None
                    })
                elif conn.status == 'ESTABLISHED':
                    results['active_connections'].append({
                        'local_address': f"{conn.laddr.ip}:{conn.laddr.port}",
                        'remote_address': f"{conn.raddr.ip}:{conn.raddr.port}",
                        'status': conn.status,
                        'pid': conn.pid,
                        'program': psutil.Process(conn.pid).name() if conn.pid else None
                    })
        except Exception as e:
            logger.error(f"Erreur lors de la vérification réseau: {e}")
        
        return results
    
    async def _check_dependencies(self):
        """
        Vérifie les dépendances pour les vulnérabilités connues
        
        Returns:
            dict: Résultats de la vérification
        """
        results = {
            'checked_packages': 0,
            'vulnerable_packages': []
        }
        
        # Simuler une vérification des dépendances
        # Dans une implémentation réelle, cela pourrait utiliser une API comme safety ou snyk
        
        return results
    
    async def _analyze_logs(self):
        """
        Analyse les logs pour détecter des activités suspectes
        
        Returns:
            dict: Résultats de l'analyse
        """
        results = {
            'analyzed_logs': 0,
            'suspicious_activities': []
        }
        
        log_files = [
            os.path.join(self.log_path, f) for f in os.listdir(self.log_path)
            if os.path.isfile(os.path.join(self.log_path, f)) and f.endswith('.log')
        ]
        
        for log_file in log_files:
            try:
                with open(log_file, 'r') as f:
                    log_content = f.readlines()
                
                results['analyzed_logs'] += 1
                
                # Rechercher des motifs suspects
                for i, line in enumerate(log_content):
                    if "Failed login attempt" in line:
                        results['suspicious_activities'].append({
                            'log_file': os.path.basename(log_file),
                            'line_number': i + 1,
                            'type': 'failed_login',
                            'content': line.strip()
                        })
                    elif "Unauthorized access" in line:
                        results['suspicious_activities'].append({
                            'log_file': os.path.basename(log_file),
                            'line_number': i + 1,
                            'type': 'unauthorized_access',
                            'content': line.strip()
                        })
                    elif "SQL injection" in line or "XSS" in line or "CSRF" in line:
                        results['suspicious_activities'].append({
                            'log_file': os.path.basename(log_file),
                            'line_number': i + 1,
                            'type': 'attack_attempt',
                            'content': line.strip()
                        })
            except Exception as e:
                logger.error(f"Erreur lors de l'analyse du fichier de log {log_file}: {e}")
        
        return results
    
    def _detect_vulnerabilities(self, audit_results):
        """
        Détecte les vulnérabilités à partir des résultats d'audit
        
        Args:
            audit_results (dict): Résultats de l'audit
            
        Returns:
            list: Vulnérabilités détectées
        """
        vulnerabilities = []
        
        # Vérifier les fichiers modifiés
        for modified_file in audit_results['file_integrity']['modified_files']:
            vulnerabilities.append({
                'name': 'File Integrity Violation',
                'severity': 'high',
                'description': f"Le fichier {modified_file['path']} a été modifié de manière inattendue",
                'affected_component': modified_file['path'],
                'status': 'open',
                'remediation': 'Vérifier les modifications et restaurer le fichier si nécessaire'
            })
        
        # Vérifier les problèmes de permissions
        for issue in audit_results['permissions']['permission_issues']:
            vulnerabilities.append({
                'name': 'Insecure File Permissions',
                'severity': 'medium',
                'description': f"Le fichier {issue['path']} a des permissions trop ouvertes ({issue['mode']})",
                'affected_component': issue['path'],
                'status': 'open',
                'remediation': 'Restreindre les permissions du fichier'
            })
        
        # Vérifier les ports ouverts non nécessaires
        known_ports = [5000, 8080]  # Ports connus pour l'API et le dashboard
        for port_info in audit_results['network']['open_ports']:
            if port_info['port'] not in known_ports:
                vulnerabilities.append({
                    'name': 'Unexpected Open Port',
                    'severity': 'medium',
                    'description': f"Port inattendu ouvert: {port_info['port']} ({port_info['program']})",
                    'affected_component': 'network',
                    'status': 'open',
                    'remediation': 'Fermer le port ou vérifier le programme associé'
                })
        
        # Vérifier les activités suspectes dans les logs
        for activity in audit_results['logs']['suspicious_activities']:
            vulnerabilities.append({
                'name': 'Suspicious Activity',
                'severity': 'high' if activity['type'] == 'attack_attempt' else 'medium',
                'description': f"Activité suspecte détectée: {activity['type']}",
                'affected_component': 'security',
                'status': 'open',
                'remediation': 'Investiguer l\'activité et renforcer la sécurité',
                'details': activity['content']
            })
        
        return vulnerabilities
    
    def _save_audit_results(self, audit_results):
        """
        Sauvegarde les résultats d'audit
        
        Args:
            audit_results (dict): Résultats de l'audit
        """
        # Sauvegarder dans un fichier JSON
        timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
        audit_file = os.path.join(self.log_path, f'audit_{timestamp}.json')
        
        try:
            with open(audit_file, 'w') as f:
                json.dump(audit_results, f, indent=2)
            logger.info(f"Résultats d'audit sauvegardés dans {audit_file}")
        except Exception as e:
            logger.error(f"Erreur lors de la sauvegarde des résultats d'audit: {e}")
    
    def log_event(self, event_type, severity, source, description, details=None):
        """
        Journalise un événement d'audit
        
        Args:
            event_type (str): Type d'événement
            severity (str): Gravité (low, medium, high, critical)
            source (str): Source de l'événement
            description (str): Description de l'événement
            details (dict, optional): Détails supplémentaires
            
        Returns:
            int: ID de l'événement
        """
        timestamp = datetime.datetime.utcnow().isoformat()
        details_json = json.dumps(details) if details else None
        
        # Calculer un hachage pour l'intégrité
        hash_input = f"{timestamp}{event_type}{severity}{source}{description}{details_json}"
        event_hash = hashlib.sha256(hash_input.encode()).hexdigest()
        
        conn = sqlite3.connect(self.audit_db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
        INSERT INTO audit_events (timestamp, event_type, severity, source, description, details, hash)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (timestamp, event_type, severity, source, description, details_json, event_hash))
        
        event_id = cursor.lastrowid
        
        conn.commit()
        conn.close()
        
        logger.info(f"Événement d'audit enregistré: {event_type} ({severity}) - {description}")
        
        return event_id
    
    def log_vulnerability(self, vulnerability):
        """
        Journalise une vulnérabilité
        
        Args:
            vulnerability (dict): Informations sur la vulnérabilité
            
        Returns:
            int: ID de la vulnérabilité
        """
        timestamp = datetime.datetime.utcnow().isoformat()
        details = vulnerability.get('details')
        details_json = json.dumps(details) if details else None
        
        conn = sqlite3.connect(self.audit_db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
        INSERT INTO vulnerabilities (timestamp, name, severity, description, affected_component, status, remediation, details)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            timestamp,
            vulnerability['name'],
            vulnerability['severity'],
            vulnerability['description'],
            vulnerability['affected_component'],
            vulnerability['status'],
            vulnerability.get('remediation'),
            details_json
        ))
        
        vuln_id = cursor.lastrowid
        
        conn.commit()
        conn.close()
        
        logger.info(f"Vulnérabilité enregistrée: {vulnerability['name']} ({vulnerability['severity']}) - {vulnerability['description']}")
        
        return vuln_id
    
    def log_access_attempt(self, username, ip_address, endpoint, method, status, user_agent=None, details=None):
        """
        Journalise une tentative d'accès
        
        Args:
            username (str): Nom d'utilisateur
            ip_address (str): Adresse IP
            endpoint (str): Point de terminaison
            method (str): Méthode HTTP
            status (str): Statut (success, failure)
            user_agent (str, optional): Agent utilisateur
            details (dict, optional): Détails supplémentaires
            
        Returns:
            int: ID de la tentative d'accès
        """
        timestamp = datetime.datetime.utcnow().isoformat()
        details_json = json.dumps(details) if details else None
        
        conn = sqlite3.connect(self.audit_db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
        INSERT INTO access_attempts (timestamp, username, ip_address, user_agent, endpoint, method, status, details)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (timestamp, username, ip_address, user_agent, endpoint, method, status, details_json))
        
        attempt_id = cursor.lastrowid
        
        conn.commit()
        conn.close()
        
        log_level = logging.WARNING if status == 'failure' else logging.INFO
        logger.log(log_level, f"Tentative d'accès: {username}@{ip_address} {method} {endpoint} - {status}")
        
        # Si c'est un échec, enregistrer également un événement d'audit
        if status == 'failure':
            self.log_event(
                'access_failure',
                'medium',
                'authentication',
                f"Échec d'authentification pour {username} depuis {ip_address}",
                {
                    'endpoint': endpoint,
                    'method': method,
                    'user_agent': user_agent,
                    'details': details
                }
            )
        
        return attempt_id
    
    def get_recent_events(self, limit=100):
        """
        Récupère les événements récents
        
        Args:
            limit (int): Nombre maximum d'événements à récupérer
            
        Returns:
            list: Événements récents
        """
        conn = sqlite3.connect(self.audit_db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute('''
        SELECT * FROM audit_events
        ORDER BY timestamp DESC
        LIMIT ?
        ''', (limit,))
        
        events = [dict(row) for row in cursor.fetchall()]
        
        conn.close()
        
        return events
    
    def get_recent_vulnerabilities(self, limit=100):
        """
        Récupère les vulnérabilités récentes
        
        Args:
            limit (int): Nombre maximum de vulnérabilités à récupérer
            
        Returns:
            list: Vulnérabilités récentes
        """
        conn = sqlite3.connect(self.audit_db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute('''
        SELECT * FROM vulnerabilities
        ORDER BY timestamp DESC
        LIMIT ?
        ''', (limit,))
        
        vulnerabilities = [dict(row) for row in cursor.fetchall()]
        
        conn.close()
        
        return vulnerabilities
    
    def get_recent_access_attempts(self, limit=100):
        """
        Récupère les tentatives d'accès récentes
        
        Args:
            limit (int): Nombre maximum de tentatives à récupérer
            
        Returns:
            list: Tentatives d'accès récentes
        """
        conn = sqlite3.connect(self.audit_db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute('''
        SELECT * FROM access_attempts
        ORDER BY timestamp DESC
        LIMIT ?
        ''', (limit,))
        
        attempts = [dict(row) for row in cursor.fetchall()]
        
        conn.close()
        
        return attempts
    
    def rotate_logs(self):
        """
        Effectue une rotation des logs
        """
        log_files = [
            os.path.join(self.log_path, f) for f in os.listdir(self.log_path)
            if os.path.isfile(os.path.join(self.log_path, f)) and f.endswith('.log')
        ]
        
        # Trier par date de modification (plus ancien en premier)
        log_files.sort(key=lambda x: os.path.getmtime(x))
        
        # Supprimer les fichiers les plus anciens si nécessaire
        while len(log_files) > self.max_log_files:
            oldest_log = log_files.pop(0)
            try:
                os.remove(oldest_log)
                logger.info(f"Fichier de log supprimé lors de la rotation: {oldest_log}")
            except Exception as e:
                logger.error(f"Erreur lors de la suppression du fichier de log {oldest_log}: {e}")
        
        # Vérifier la taille des fichiers restants
        for log_file in log_files:
            try:
                if os.path.getsize(log_file) > self.max_log_size:
                    # Renommer le fichier avec un timestamp
                    timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
                    new_name = f"{log_file}.{timestamp}"
                    os.rename(log_file, new_name)
                    logger.info(f"Fichier de log archivé: {log_file} -> {new_name}")
            except Exception as e:
                logger.error(f"Erreur lors de la vérification du fichier de log {log_file}: {e}")
    
    def generate_security_report(self):
        """
        Génère un rapport de sécurité complet
        
        Returns:
            dict: Rapport de sécurité
        """
        # Récupérer les données
        events = self.get_recent_events(1000)
        vulnerabilities = self.get_recent_vulnerabilities()
        access_attempts = self.get_recent_access_attempts(1000)
        
        # Analyser les données
        report = {
            'timestamp': datetime.datetime.utcnow().isoformat(),
            'summary': {
                'total_events': len(events),
                'total_vulnerabilities': len(vulnerabilities),
                'total_access_attempts': len(access_attempts),
                'failed_access_attempts': sum(1 for a in access_attempts if a['status'] == 'failure'),
                'critical_vulnerabilities': sum(1 for v in vulnerabilities if v['severity'] == 'critical'),
                'high_vulnerabilities': sum(1 for v in vulnerabilities if v['severity'] == 'high'),
                'medium_vulnerabilities': sum(1 for v in vulnerabilities if v['severity'] == 'medium'),
                'low_vulnerabilities': sum(1 for v in vulnerabilities if v['severity'] == 'low')
            },
            'top_vulnerabilities': sorted(
                vulnerabilities,
                key=lambda v: {'critical': 4, 'high': 3, 'medium': 2, 'low': 1}.get(v['severity'], 0),
                reverse=True
            )[:10],
            'recent_events': events[:20],
            'recent_access_attempts': access_attempts[:20],
            'recommendations': []
        }
        
        # Générer des recommandations
        if report['summary']['critical_vulnerabilities'] > 0:
            report['recommendations'].append({
                'priority': 'critical',
                'description': 'Résoudre immédiatement les vulnérabilités critiques',
                'details': 'Des vulnérabilités critiques ont été détectées et nécessitent une attention immédiate.'
            })
        
        if report['summary']['failed_access_attempts'] > 10:
            report['recommendations'].append({
                'priority': 'high',
                'description': 'Renforcer l\'authentification',
                'details': 'Un nombre élevé de tentatives d\'accès échouées a été détecté. Envisagez de renforcer les mécanismes d\'authentification.'
            })
        
        if report['summary']['high_vulnerabilities'] > 0:
            report['recommendations'].append({
                'priority': 'high',
                'description': 'Résoudre les vulnérabilités de haute priorité',
                'details': 'Des vulnérabilités de haute priorité ont été détectées et devraient être résolues rapidement.'
            })
        
        return report
