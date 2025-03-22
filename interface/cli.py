import asyncio
import cmd
import json
from datetime import datetime
from typing import Dict, Any, Optional
import sys
import os

from core.polyad import Polyad
from utils.logger import logger

class PolyadCLI(cmd.Cmd):
    """Interface CLI interactive pour Polyad"""
    
    intro = """
    === Polyad Agent Interface ===
    
    Commandes disponibles:
    - task     : Soumettre une tâche
    - status   : Voir l'état actuel
    - monitor  : Monitorer les performances
    - learn    : Observer l'apprentissage
    - resources: Gérer les ressources
    - plan     : Voir les tâches planifiées
    - help     : Aide détaillée
    - quit     : Quitter
    
    Tapez 'help <commande>' pour plus d'informations.
    """
    prompt = 'polyad> '
    
    def __init__(self):
        super().__init__()
        self.agent = None
        self.monitoring = False
        self.last_status = {}
        
    async def initialize(self):
        """Initialiser l'agent"""
        self.agent = Polyad()
        return await self.agent.initialize()
        
    def do_task(self, arg):
        """
        Soumettre une tâche à l'agent.
        Usage: task <type> <description>
        Types: text, vision, audio, system
        """
        try:
            args = arg.split()
            if not args:
                print("Erreur: Spécifiez le type de tâche")
                return
                
            task_type = args[0]
            description = ' '.join(args[1:])
            
            task = {
                'type': task_type,
                'description': description,
                'timestamp': datetime.now().isoformat()
            }
            
            # Exécuter la tâche de manière asynchrone
            asyncio.create_task(self._execute_task(task))
            
        except Exception as e:
            print(f"Erreur lors de la soumission de la tâche: {e}")
            
    async def _execute_task(self, task: Dict[str, Any]):
        """Exécuter une tâche"""
        try:
            print(f"\nExécution de la tâche: {task['description']}")
            result = await self.agent.process_task(task)
            
            if 'error' in result:
                print(f"Erreur: {result['error']}")
            else:
                print("\nRésultat:")
                print(json.dumps(result, indent=2))
                
        except Exception as e:
            print(f"Erreur d'exécution: {e}")
            
    def do_status(self, arg):
        """
        Afficher l'état actuel de l'agent.
        Usage: status [detail]
        """
        try:
            status = self.agent.capabilities
            if arg == "detail":
                print("\nÉtat détaillé:")
                print(json.dumps(status, indent=2))
            else:
                print("\nÉtat résumé:")
                print(f"Compétences: {len(status['skills'])}")
                print(f"Base de connaissances: {status['knowledge_size']} entrées")
                print(f"Performance moyenne: {status['performance']}")
                
        except Exception as e:
            print(f"Erreur lors de la récupération du status: {e}")
            
    def do_monitor(self, arg):
        """
        Monitorer les performances en temps réel.
        Usage: monitor [start|stop]
        """
        if arg == "start":
            if not self.monitoring:
                self.monitoring = True
                asyncio.create_task(self._monitor_performance())
                print("Monitoring démarré...")
        elif arg == "stop":
            self.monitoring = False
            print("Monitoring arrêté.")
        else:
            print("Usage: monitor [start|stop]")
            
    async def _monitor_performance(self):
        """Monitorer les performances en continu"""
        try:
            while self.monitoring:
                metrics = self.agent.resources.current_status()
                os.system('clear' if os.name == 'posix' else 'cls')
                print("\n=== Performance en temps réel ===")
                print(f"CPU: {metrics['cpu']['percent']}%")
                print(f"RAM: {metrics['memory']['ram']['percent']}%")
                print(f"Température: {metrics['temperature'].get('cpu', 'N/A')}°C")
                print(f"Réseau: ↑{metrics['network']['bytes_sent']/1024:.1f}KB/s "
                      f"↓{metrics['network']['bytes_recv']/1024:.1f}KB/s")
                await asyncio.sleep(1)
                
        except Exception as e:
            print(f"Erreur de monitoring: {e}")
            self.monitoring = False
            
    def do_learn(self, arg):
        """
        Observer l'apprentissage de l'agent.
        Usage: learn [history|skills|progress]
        """
        try:
            if arg == "history":
                history = self.agent.learning_state['learning_history']
                print("\nHistorique d'apprentissage:")
                for entry in history[-10:]:  # 10 dernières entrées
                    print(f"{entry['timestamp']}: {entry['skill']} - "
                          f"{'Succès' if entry['success'] else 'Échec'}")
                    
            elif arg == "skills":
                skills = self.agent.learning_state['skills']
                print("\nCompétences acquises:")
                for skill in sorted(skills):
                    print(f"- {skill}")
                    
            elif arg == "progress":
                metrics = self.agent.learning_state['performance_metrics']
                print("\nProgrès d'apprentissage:")
                for metric, values in metrics.items():
                    if values:
                        avg = sum(values) / len(values)
                        print(f"{metric}: {avg:.2f}")
                        
            else:
                print("Usage: learn [history|skills|progress]")
                
        except Exception as e:
            print(f"Erreur lors de la consultation de l'apprentissage: {e}")
            
    def do_resources(self, arg):
        """
        Gérer les ressources système.
        Usage: resources [status|optimize|limits]
        """
        try:
            if arg == "status":
                status = self.agent.resources.current_status()
                print("\nÉtat des ressources:")
                print(json.dumps(status, indent=2))
                
            elif arg == "optimize":
                asyncio.create_task(self._optimize_resources())
                
            elif arg == "limits":
                limits = self.agent.resources.thresholds
                print("\nLimites configurées:")
                print(json.dumps(limits, indent=2))
                
            else:
                print("Usage: resources [status|optimize|limits]")
                
        except Exception as e:
            print(f"Erreur lors de la gestion des ressources: {e}")
            
    async def _optimize_resources(self):
        """Optimiser l'utilisation des ressources"""
        try:
            print("Optimisation des ressources en cours...")
            metrics = await self.agent.resources.monitor()
            optimizations = self.agent.resources.optimize_resources(
                metrics['temperature'].get('cpu', 0),
                metrics['memory']['ram']['available']
            )
            print("\nOptimisations appliquées:")
            print(json.dumps(optimizations, indent=2))
            
        except Exception as e:
            print(f"Erreur lors de l'optimisation: {e}")
            
    def do_plan(self, arg):
        """
        Voir les tâches planifiées et leur état.
        Usage: plan [current|history|next]
        """
        try:
            if arg == "current":
                current_task = self.agent.processor.current_task
                if current_task:
                    print("\nTâche en cours:")
                    print(json.dumps(current_task, indent=2))
                else:
                    print("Aucune tâche en cours")
                    
            elif arg == "history":
                history = self.agent.processor.performance_history
                print("\nHistorique des tâches:")
                for task in history[-10:]:  # 10 dernières tâches
                    print(f"{task['timestamp']}: {task['task_type']} - "
                          f"{'Succès' if task['success'] else 'Échec'}")
                    
            elif arg == "next":
                next_tasks = self.agent.processor.pending_tasks
                if next_tasks:
                    print("\nTâches à venir:")
                    for task in next_tasks:
                        print(f"- {task['type']}: {task['description']}")
                else:
                    print("Aucune tâche en attente")
                    
            else:
                print("Usage: plan [current|history|next]")
                
        except Exception as e:
            print(f"Erreur lors de la consultation du plan: {e}")
            
    def do_quit(self, arg):
        """Quitter l'interface"""
        print("\nFermeture de Polyad...")
        asyncio.create_task(self._cleanup())
        return True
        
    async def _cleanup(self):
        """Nettoyer les ressources avant de quitter"""
        if self.agent:
            await self.agent.save_state()
            
    def default(self, line):
        """Gérer les commandes inconnues"""
        print(f"Commande inconnue: {line}")
        print("Tapez 'help' pour voir les commandes disponibles.")
        
async def main():
    """Point d'entrée principal"""
    try:
        cli = PolyadCLI()
        if not await cli.initialize():
            print("Erreur d'initialisation de Polyad")
            return 1
            
        # Démarrer l'interface
        while True:
            try:
                line = input(cli.prompt)
                if line == 'quit':
                    break
                await cli.onecmd(line)
            except KeyboardInterrupt:
                print("\nUtilisez 'quit' pour quitter proprement")
            except Exception as e:
                print(f"Erreur: {e}")
                
    except Exception as e:
        print(f"Erreur fatale: {e}")
        return 1
        
if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nFermeture forcée de Polyad")
    except Exception as e:
        print(f"Erreur fatale: {e}")
        sys.exit(1)
