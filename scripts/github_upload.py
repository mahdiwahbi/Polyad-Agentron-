#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script pour initialiser et téléverser le projet Polyad sur GitHub
"""
import os
import sys
import subprocess
import argparse
from pathlib import Path

def run_command(command, cwd=None):
    """Exécute une commande shell et affiche le résultat"""
    print(f"Exécution: {command}")
    try:
        result = subprocess.run(
            command, 
            shell=True, 
            check=True, 
            text=True, 
            capture_output=True,
            cwd=cwd
        )
        if result.stdout:
            print(result.stdout)
        return True
    except subprocess.CalledProcessError as e:
        print(f"Erreur: {e}")
        if e.stderr:
            print(e.stderr)
        return False

def init_repo(project_path, repo_name, description):
    """Initialise un dépôt Git local"""
    # Vérifier si .git existe déjà
    git_dir = os.path.join(project_path, ".git")
    if os.path.exists(git_dir):
        print(f"Le dépôt Git existe déjà dans {project_path}")
        choice = input("Voulez-vous réinitialiser le dépôt? (o/n): ").lower()
        if choice == 'o':
            run_command(f"rm -rf {git_dir}", project_path)
        else:
            return True
    
    # Initialiser le dépôt
    return run_command("git init", project_path)

def create_github_repo(repo_name, description, private=False):
    """Crée un nouveau dépôt sur GitHub via l'API"""
    visibility = "--private" if private else "--public"
    return run_command(f"gh repo create {repo_name} {visibility} --description \"{description}\"")

def add_and_commit(project_path, message="Initial commit"):
    """Ajoute tous les fichiers et crée un commit"""
    if not run_command("git add .", project_path):
        return False
    return run_command(f"git commit -m \"{message}\"", project_path)

def add_remote_and_push(project_path, repo_name, username):
    """Ajoute le dépôt distant et pousse les changements"""
    remote_url = f"https://github.com/{username}/{repo_name}.git"
    if not run_command(f"git remote add origin {remote_url}", project_path):
        return False
    return run_command("git push -u origin main", project_path)

def check_github_cli():
    """Vérifie si GitHub CLI est installé et authentifié"""
    try:
        result = subprocess.run(
            "gh auth status", 
            shell=True, 
            text=True, 
            capture_output=True
        )
        return result.returncode == 0
    except:
        return False

def main():
    parser = argparse.ArgumentParser(description="Téléverser Polyad sur GitHub")
    parser.add_argument("--username", help="Nom d'utilisateur GitHub")
    parser.add_argument("--repo", default="polyad", help="Nom du dépôt (défaut: polyad)")
    parser.add_argument("--description", default="Agent Autonome Polyvalent", 
                        help="Description du dépôt")
    parser.add_argument("--private", action="store_true", help="Rendre le dépôt privé")
    args = parser.parse_args()
    
    # Chemin du projet
    script_dir = Path(__file__).parent.absolute()
    project_path = script_dir.parent
    
    print(f"Préparation du téléversement de {project_path} vers GitHub...")
    
    # Vérifier GitHub CLI
    if not check_github_cli():
        print("GitHub CLI (gh) n'est pas installé ou vous n'êtes pas authentifié.")
        print("Installez GitHub CLI avec: brew install gh")
        print("Puis authentifiez-vous avec: gh auth login")
        return False
    
    # Demander le nom d'utilisateur si non fourni
    username = args.username
    if not username:
        username = input("Entrez votre nom d'utilisateur GitHub: ")
    
    # Initialiser le dépôt Git local
    if not init_repo(project_path, args.repo, args.description):
        return False
    
    # Ajouter et commiter les fichiers
    if not add_and_commit(project_path):
        return False
    
    # Créer le dépôt sur GitHub
    if not create_github_repo(args.repo, args.description, args.private):
        return False
    
    # Ajouter le dépôt distant et pousser
    if not add_remote_and_push(project_path, args.repo, username):
        return False
    
    print(f"\nSuccès! Votre projet est maintenant disponible sur:")
    print(f"https://github.com/{username}/{args.repo}")
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
