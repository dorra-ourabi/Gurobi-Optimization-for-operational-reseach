# test_debug.py
from config.config_manager import ConfigManager
from models.risk_calculator import ClientProfile, PretDemande, RiskCalculator

# 1. Charger config
config = ConfigManager("config/default_config.json")

# 2. Créer client test
client = ClientProfile(
    score_credit=720,
    revenu_mensuel=3500,
    charges_mensuelles=400,
    apport_personnel=20,
    anciennete_pro=3,
    nb_prets_existants=1,
    historique_paiement=0.9,
    type_contrat="CDI",
    segment="particulier_moyen",
    statut_client="fidele"
)

# 3. Créer prêt test
pret = PretDemande(
    montant=20000,
    duree=5,
    type_pret="automobile",
    apport=4000
)

# 4. Calculer PD
risk_calc = RiskCalculator(config)
PD = risk_calc.calculer_probabilite_defaut(client)
print(f"📊 PD calculée: {PD*100:.2f}%")

# 5. Vérifier la prime de risque
prime_ancienne = PD * 2.5 * 100
prime_nouvelle = PD * 0.35 * 100
print(f"⚠️  Prime risque ANCIENNE (×2.5): {prime_ancienne:.2f}%")
print(f"✅ Prime risque NOUVELLE (×0.35): {prime_nouvelle:.2f}%")

# 6. Calculer bornes
c_ref = config.get('couts_et_risques', 'cout_refinancement', default=2.7) / 100
m_min = config.get('couts_et_risques', 'marge_minimale', default=0.5) / 100

r_min_ancien = c_ref + m_min + (PD * 2.5)
r_min_nouveau = c_ref + m_min + (PD * 0.35)

print(f"\n🔧 Calcul des bornes:")
print(f"   Coût refinancement (c_ref): {c_ref*100:.2f}%")
print(f"   Marge minimale (m_min): {m_min*100:.2f}%")
print(f"   r_min ANCIEN: {r_min_ancien*100:.2f}%")
print(f"   r_min NOUVEAU: {r_min_nouveau*100:.2f}%")

# Taux usure auto (exemple)
print(f"   Taux usure auto estimé: ~6.39%")
print(f"\n🎯 CONCLUSION:")
if r_min_ancien > 0.0639:
    print(f"   ❌ ANCIEN: r_min ({r_min_ancien*100:.2f}%) > taux usure (6.39%) → IMPOSSIBLE")
if r_min_nouveau < 0.0639:
    print(f"   ✅ NOUVEAU: r_min ({r_min_nouveau*100:.2f}%) < taux usure (6.39%) → POSSIBLE")