# 🏦 Système de Tarification Optimale des Prêts

**Projet de Recherche Opérationnelle**  
Application de tarification optimale utilisant la programmation linéaire avec Gurobi

---

## 📋 Description

Ce projet implémente un **système d'optimisation de tarification** pour les prêts bancaires. Il utilise le solveur **Gurobi** pour calculer le taux d'intérêt optimal qui maximise le profit de la banque tout en respectant :
- Les contraintes réglementaires (taux d'usure, ratio d'endettement)
- Les conditions de marché (concurrence, élasticité)
- Le profil de risque du client (scoring de crédit)

---

## 🎯 Fonctionnalités

### ✅ Variables Intégrées (TOUTES !)

**Indices :**
- **Types de prêts (i)** : Immobilier, Automobile, Personnel, Professionnel, Étudiant
- **Segments clients (j)** : Particuliers (faible/moyen/élevé), Professionnels, Primo-accédants, Clients fidèles
- **Durées (k)** : Court terme (< 2 ans), Moyen terme (2-7 ans), Long terme (> 7 ans)

**Paramètres Macroéconomiques :**
- Taux directeur BCE (τ_BCE)
- Taux EURIBOR (τ_IB)
- Taux d'inflation (π_t)
- Croissance économique (g_eco)

**Caractéristiques Client :**
- Score de crédit (S_credit) ∈ [300, 850]
- Ratio d'endettement (D/R) ≤ 33%
- Revenus mensuels (R_mensuel)
- Apport personnel (A_p)
- Ancienneté professionnelle (A_prof)
- Nombre de prêts existants (N_prets)
- Historique de paiement (H_pay)

**Contraintes Réglementaires :**
- Taux d'usure légal (r_max^i)
- Ratio de solvabilité Bâle III (CAR ≥ 8%)
- Ratio de liquidité (LCR ≥ 100%)
- TAEG maximum

**Coûts et Risques :**
- Coût de refinancement (c_ref)
- Coûts opérationnels (c_op^i)
- Probabilité de défaut (PD_j)
- Perte en cas de défaut (LGD)
- Provisions pour risque (P_risk)

**Paramètres Concurrentiels :**
- Taux concurrent moyen (r̄_concurrent^{i,k})
- Part de marché visée (PM_target)
- Élasticité-prix de la demande (ε_{i,j,k})

---

## 🏗️ Architecture Modulaire

```
projet_tarification_optimale/
│
├── config/
│   ├── default_config.json          # Configuration complète (TOUTES les variables)
│   └── config_manager.py            # Gestionnaire de configuration
│
├── models/
│   ├── gurobi_optimizer.py          # Moteur d'optimisation Gurobi
│   ├── risk_calculator.py           # Calcul PD, scoring
│   ├── constraints_manager.py       # Gestion des contraintes
│   └── market_analyzer.py           # Analyse concurrentielle
│
├── ui/
│   └── (Intégré dans main.py)       # Interface PyQt5
│
├── data/
│   └── clients_historique.csv       # Base de données clients (optionnel)
│
├── main.py                          # Application principale
├── requirements.txt                 # Dépendances
└── README.md                        # Ce fichier
```

---

## 🚀 Installation

### 1. **Prérequis**
- Python 3.8 ou supérieur
- Gurobi Optimizer (licence académique gratuite)

### 2. **Installation de Gurobi**

#### Option A : Avec Conda (Recommandé)
```bash
# Créer un environnement
conda create -n tarification python=3.10
conda activate tarification

# Installer Gurobi
conda install -c gurobi gurobi
```

#### Option B : Avec pip
```bash
# Installer Gurobi
pip install gurobipy

# Télécharger et activer la licence
# 1. Créez un compte sur https://www.gurobi.com/academia/
# 2. Téléchargez votre clé de licence
# 3. Activez-la :
grbgetkey XXXXXXXX-XXXX-XXXX-XXXX-XXXXXXXXXXXX
```

### 3. **Installation des dépendances**
```bash
pip install -r requirements.txt
```

---

## ▶️ Utilisation

### Lancer l'application
```bash
python main.py
```

### Interface à onglets

#### **Onglet 1 : Configuration ⚙️**
- Configurer TOUS les paramètres globaux
- Paramètres macroéconomiques, coûts, contraintes réglementaires
- Paramètres de marché, scoring de risque, scénarios économiques
- Sauvegarder/Importer des configurations

#### **Onglet 2 : Nouveau Client 👤**
- Saisir les informations client (score, revenu, charges...)
- Définir la demande de prêt (type, montant, durée)
- Lancer l'optimisation
- Voir les résultats détaillés :
  - Taux optimal calculé
  - Mensualité, TAEG, coût total
  - Analyse de risque (PD, ratio endettement)
  - Profitabilité pour la banque
  - Comparaison avec le marché
  - Conformité réglementaire

#### **Onglet 3 : Analyse de Sensibilité 📊**
- Analyser l'impact d'un paramètre sur le taux optimal
- Variables analysables : Taux BCE, inflation, score crédit, durée...
- Visualisation des résultats

#### **Onglet 4 : Portefeuille 📁**
- Voir tous les dossiers traités
- Statistiques globales (volume, profit, taux moyen)
- Exporter en CSV
- Générer des rapports

---

## 📐 Modèle Mathématique

### **Fonction Objectif**
```
Max Z = D × [V × k × (r - c_ref) - c_op - V × PD × LGD - P_risk]
```

Où :
- **r** = Taux d'intérêt à optimiser (variable de décision)
- **D** = Demande (nombre de clients)
- **V** = Montant du prêt
- **k** = Durée du prêt
- **c_ref** = Coût de refinancement
- **c_op** = Coût opérationnel
- **PD** = Probabilité de défaut
- **LGD** = Loss Given Default
- **P_risk** = Provision pour risque

### **Contraintes Principales**

1. **Taux d'usure** :
   ```
   r ≤ r_usure^i
   ```

2. **Compétitivité** :
   ```
   r ≤ r̄_concurrent × (1 + α)
   ```

3. **Rentabilité minimale** :
   ```
   r ≥ c_ref + m_min + β × PD
   ```

4. **Ratio d'endettement** :
   ```
   (V × r) / (12 × k) + C_existantes ≤ 0.33 × R_mensuel
   ```

5. **Demande (élasticité)** :
   ```
   D = D_0 × [1 + ε × (r̄ - r)]
   ```

### **Calcul de la Probabilité de Défaut (PD)**

Fonction logistique composite :
```
z = w1×(1 - S_norm) + w2×(D/R) + w3×N_prets - w4×A_prof + w5×H_pay + w6×type_contrat

PD = 1 / (1 + e^(-z + z_offset))
```

Ajustements :
- Segment client (primo-accédant, PME, fidèle...)
- Scénario économique (normal, crise, expansion...)

---

## 🔧 Configuration Avancée

### Modifier les paramètres par défaut

Éditez le fichier `config/default_config.json` :

```json
{
  "parametres_macroeconomiques": {
    "taux_directeur_bce": {"valeur": 2.5},
    "taux_inflation": {"valeur": 3.2},
    ...
  },
  "couts_et_risques": {
    "cout_refinancement": {"valeur": 2.7},
    "marge_minimale": {"valeur": 0.5},
    ...
  },
  ...
}
```

### Scénarios économiques

Modifiez le scénario actif dans la configuration :

```json
"scenarios_economiques": {
  "scenario_actif": {"valeur": "crise"},
  ...
}
```

Options : `"normal"`, `"crise"`, `"expansion"`, `"recession"`, `"stagnation"`

---

## 📊 Exemple d'Utilisation

### Cas 1 : Prêt Automobile

**Client :**
- Score crédit : 720
- Revenu mensuel : 3500 €
- Charges mensuelles : 400 €
- Ancienneté : 3 ans
- Statut : Client fidèle

**Prêt :**
- Type : Automobile
- Montant : 20 000 €
- Durée : 5 ans
- Apport : 4 000 € (20%)

**Résultat :**
- ✅ **Taux optimal : 5.35%**
- Mensualité : 472.85 €
- Profit estimé : 947 €
- PD : 2.1%
- Conformité : ✅ Toutes les contraintes respectées

---

## 🛠️ Dépannage

### Erreur : "Gurobi not found"
```bash
# Vérifiez l'installation
python -c "import gurobipy; print(gurobipy.__version__)"

# Si erreur, réinstallez
pip install --upgrade gurobipy
```

### Erreur : "License error"
```bash
# Vérifiez la licence
gurobi_cl --license

# Réactivez si nécessaire
grbgetkey VOTRE-CLE
```

### Erreur : "Config file not found"
- Créez le dossier `config/`
- Copiez le fichier `default_config.json` dedans

---

## 📚 Références

### Documentation Gurobi
- [Guide officiel Gurobi](https://www.gurobi.com/documentation/)
- [Python API Reference](https://www.gurobi.com/documentation/current/refman/py_python_api_overview.html)

### Recherche Opérationnelle
- Hillier & Lieberman - *Introduction to Operations Research*
- Winston - *Operations Research: Applications and Algorithms*

### Réglementation Bancaire
- [Banque de France - Taux d'usure](https://www.banque-france.fr/statistiques/taux-et-cours/taux-dusure)
- [Bâle III - Capital Requirements](https://www.bis.org/bcbs/basel3.htm)

---

## 👥 Auteurs

Projet de Recherche Opérationnelle  
**Année universitaire 2024-2025**

---

## 📄 Licence

Ce projet est destiné à un usage académique uniquement.

---

## 💡 Améliorations Futures

- [ ] Visualisation graphique des analyses de sensibilité
- [ ] Export PDF des rapports
- [ ] Intégration d'une base de données SQL
- [ ] API REST pour utilisation externe
- [ ] Optimisation multi-objectifs (profit vs risque)
- [ ] Simulation de Monte Carlo pour le risque
- [ ] Dashboard temps réel du portefeuille

---

## 🆘 Support

Pour toute question ou problème :
1. Vérifiez la documentation Gurobi
2. Consultez les issues GitHub (si projet hébergé)
3. Contactez l'équipe pédagogique

---

**🚀 Bonne utilisation !**