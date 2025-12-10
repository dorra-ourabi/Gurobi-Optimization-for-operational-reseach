import json
import os
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime
import copy

class ConfigManager:
    """Gestionnaire de configuration centralisé avec sauvegarde persistante"""
    
    def __init__(self, default_config_path: str = "config/default_config.json", 
                 user_config_path: str = "config/user_config.json"):
        self.default_config_path = Path(default_config_path)
        self.user_config_path = Path(user_config_path)
        
        # Charger la configuration par défaut
        self.default_config = self._load_json(self.default_config_path)
        user_config_exists_and_not_empty = (self.user_config_path.exists() and 
        os.path.getsize(self.user_config_path) > 0 )
        
        if user_config_exists_and_not_empty:
            self.user_config = self._load_json(self.user_config_path)
            self.config = self._merge_configs(self.default_config, self.user_config)
        else:
            self.config = copy.deepcopy(self.default_config)
            self.user_config = {}
        
        # Historique des modifications
        self.history = []
        self.auto_save = True
    
    def _load_json(self, path: Path) -> Dict:
        """Charge un fichier JSON"""
        try:
            with open(path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"Erreur chargement {path}: {e}")
            return {}
    
    def _merge_configs(self, default: Dict, user: Dict) -> Dict:
        """Fusionne les configurations par défaut et utilisateur"""
        result = copy.deepcopy(default)
        
        def merge_recursive(default_dict, user_dict):
            for key, user_value in user_dict.items():
                if key in default_dict:
                    if isinstance(user_value, dict) and isinstance(default_dict[key], dict):
                        merge_recursive(default_dict[key], user_value)
                    else:
                        default_dict[key] = user_value
                else:
                    default_dict[key] = user_value
        
        merge_recursive(result, user)
        return result
    
    def get(self, *keys: str, default: Any = None) -> Any:
        """
        Récupère une valeur dans la configuration
        
        Args:
            *keys: Chemin vers la valeur (ex: 'parametres_macroeconomiques', 'taux_directeur_bce')
            default: Valeur par défaut si non trouvée
        
        Returns:
            La valeur trouvée ou la valeur par défaut
        """
        try:
            current = self.config
            for key in keys:
                if isinstance(current, dict):
                    current = current[key]
                else:
                    return default
            
            # Si c'est un dict avec 'valeur', retourner la valeur
            if isinstance(current, dict) and 'valeur' in current:
                return current['valeur']
            return current
            
        except (KeyError, TypeError, IndexError):
            return default
    
    def get_with_details(self, *keys: str) -> Dict:
        """
        Récupère une valeur avec tous ses métadonnées
        
        Returns:
            Dict avec valeur, min, max, unité, description, etc.
        """
        try:
            current = self.config
            for key in keys:
                current = current[key]
            
            # Si c'est une variable configurable structurée
            if isinstance(current, dict) and 'valeur' in current:
                return {
                    'valeur': current.get('valeur'),
                    'min': current.get('min'),
                    'max': current.get('max'),
                    'unite': current.get('unite', ''),
                    'description': current.get('description', ''),
                    'type': current.get('type', 'float'),
                    'categorie': keys[-2] if len(keys) >= 2 else '',
                    'nom_affichage': current.get('nom_affichage', keys[-1])
                }
            else:
                # Variable simple
                return {'valeur': current}
                
        except (KeyError, TypeError):
            return {}
    
    def set(self, *keys: str, value: Any, save: bool = True) -> bool:
        """
        Définit une valeur dans la configuration
        
        Args:
            *keys: Chemin vers la valeur
            value: Nouvelle valeur
            save: Sauvegarder automatiquement
        
        Returns:
            True si succès, False sinon
        """
        try:
            # Mettre à jour la configuration globale
            self._set_value_recursive(self.config, list(keys), value)
            
            # Mettre à jour la configuration utilisateur
            self._update_user_config(keys, value)
            
            # Enregistrer dans l'historique
            self.history.append({
                'timestamp': datetime.now().isoformat(),
                'path': '.'.join(keys),
                'value': value,
                'action': 'set'
            })
            
            # Limiter la taille de l'historique
            if len(self.history) > 100:
                self.history = self.history[-100:]
            
            # Sauvegarder automatiquement si demandé
            if save and self.auto_save:
                self.save_user_config()
            
            return True
            
        except Exception as e:
            print(f"Erreur modification configuration: {e}")
            return False
    
    def _set_value_recursive(self, data: Dict, keys: List[str], value: Any):
        """Met à jour récursivement une valeur"""
        if len(keys) == 1:
            key = keys[0]
            if isinstance(data.get(key), dict) and 'valeur' in data[key]:
                data[key]['valeur'] = value
            else:
                data[key] = value
        else:
            key = keys[0]
            if key not in data:
                data[key] = {}
            self._set_value_recursive(data[key], keys[1:], value)
    
    def _update_user_config(self, keys: List[str], value: Any):
        """Met à jour la configuration utilisateur"""
        current = self.user_config
        for i, key in enumerate(keys):
            if i == len(keys) - 1:
                # Dernière clé : mettre la valeur
                if isinstance(current.get(key), dict) and 'valeur' in current.get(key, {}):
                    current[key]['valeur'] = value
                else:
                    current[key] = value
            else:
                # Créer le niveau s'il n'existe pas
                if key not in current:
                    current[key] = {}
                current = current[key]
    
    def save_user_config(self):
        """Sauvegarde la configuration utilisateur sur le disque"""
        try:
            # Créer le dossier s'il n'existe pas
            self.user_config_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Ajouter des métadonnées
            config_to_save = {
                '_metadata': {
                    'last_modified': datetime.now().isoformat(),
                    'version': '1.0',
                    'default_config': str(self.default_config_path)
                },
                'config': self.user_config
            }
            
            # Sauvegarder
            with open(self.user_config_path, 'w', encoding='utf-8') as f:
                json.dump(config_to_save, f, indent=2, ensure_ascii=False)
            
            return True
            
        except Exception as e:
            print(f"Erreur sauvegarde configuration: {e}")
            return False
    
    def reset_to_default(self, *keys: str) -> bool:
        """
        Réinitialise une valeur ou toute la configuration aux valeurs par défaut
        
        Args:
            *keys: Chemin vers la valeur à réinitialiser (vide pour tout réinitialiser)
        
        Returns:
            True si succès
        """
        try:
            if not keys:
                # Réinitialiser toute la configuration
                self.config = copy.deepcopy(self.default_config)
                self.user_config = {}
                self.save_user_config()
                return True
            
            # Réinitialiser une valeur spécifique
            default_value = self._get_default_value(keys)
            if default_value is not None:
                return self.set(*keys, value=default_value, save=True)
            
            return False
            
        except Exception as e:
            print(f"Erreur réinitialisation: {e}")
            return False
    
    def _get_default_value(self, keys: List[str]) -> Any:
        """Récupère la valeur par défaut d'une clé"""
        try:
            current = self.default_config
            for key in keys:
                current = current[key]
            
            if isinstance(current, dict) and 'valeur' in current:
                return current['valeur']
            return current
            
        except (KeyError, TypeError):
            return None
    
    def get_all_variables(self) -> List[Dict]:
        """
        Retourne toutes les variables configurables
        
        Returns:
            Liste de dictionnaires avec toutes les informations des variables
        """
        variables = []
        
        def explore(path: List[str], data: Dict):
            if isinstance(data, dict):
                if 'valeur' in data:
                    # Variable configurable trouvée
                    var_info = {
                        'path': '.'.join(path),
                        'name': path[-1] if path else '',
                        'display_name': data.get('nom_affichage', path[-1]),
                        'value': data.get('valeur'),
                        'default_value': self._get_default_value(path),
                        'min': data.get('min'),
                        'max': data.get('max'),
                        'unit': data.get('unite', ''),
                        'description': data.get('description', ''),
                        'category': path[0] if path else '',
                        'type': data.get('type', 'float')
                    }
                    variables.append(var_info)
                else:
                    # Explorer récursivement
                    for key, value in data.items():
                        explore(path + [key], value)
        
        explore([], self.config)
        return variables
    
    def export_config(self, filepath: str) -> bool:
        """Exporte la configuration complète"""
        try:
            export_data = {
                'metadata': {
                    'export_date': datetime.now().isoformat(),
                    'version': '1.0'
                },
                'default_config': self.default_config,
                'user_config': self.user_config,
                'merged_config': self.config
            }
            
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, indent=2, ensure_ascii=False)
            
            return True
            
        except Exception as e:
            print(f"Erreur export: {e}")
            return False
    
    def import_config(self, filepath: str) -> bool:
        """Importe une configuration"""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                import_data = json.load(f)
            
            if 'user_config' in import_data:
                self.user_config = import_data['user_config']
                self.config = self._merge_configs(self.default_config, self.user_config)
                self.save_user_config()
                return True
            
            return False
            
        except Exception as e:
            print(f"Erreur import: {e}")
            return False
    
    def get_config_summary(self) -> Dict:
        """Retourne un résumé de la configuration"""
        return {
            'total_variables': len(self.get_all_variables()),
            'modified_variables': len([v for v in self.get_all_variables() if v['value'] != v['default_value']]),
            'last_modified': self.history[-1]['timestamp'] if self.history else None,
            'config_sizes': {
                'default': len(str(self.default_config)),
                'user': len(str(self.user_config))
            }
        }