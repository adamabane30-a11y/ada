import warnings
warnings.filterwarnings("ignore")

from pathlib import Path

import joblib
import pandas as pd
import streamlit as st

DOSSIER = Path(__file__).parent

st.set_page_config(page_title="Détection du cancer du sein", page_icon="🩺")


@st.cache_resource
def charger_modele():
    return joblib.load(DOSSIER / "modele_cancer_sein.joblib")


@st.cache_data
def charger_donnees():
    return pd.read_csv(DOSSIER / "Breast_cancer.csv")


modele = charger_modele()
df = charger_donnees()
FEATURES = list(modele.feature_names_in_)
MEDIANES = df[FEATURES].median()

# Dans le fichier : CLASS 0 = maligne, 1 = bénigne.
# Dans le modèle : la colonne 1 de predict_proba = "maligne".


def charger_exemple(classe):
    ligne = df[df["CLASS"] == classe].iloc[0]
    for f in FEATURES:
        st.session_state[f] = float(ligne[f])


def reinitialiser():
    for f in FEATURES:
        st.session_state[f] = float(MEDIANES[f])


for f in FEATURES:
    st.session_state.setdefault(f, float(MEDIANES[f]))

st.title("🩺 Détection du cancer du sein")
st.warning(
    "Exercice pédagogique : cet outil ne remplace en aucun cas un diagnostic "
    "médical. Seul un professionnel de santé peut poser un diagnostic."
)

st.write("Saisis les 30 mesures des cellules, ou charge un exemple :")
c1, c2, c3 = st.columns(3)
c1.button("Exemple maligne", on_click=charger_exemple, args=(0,))
c2.button("Exemple bénigne", on_click=charger_exemple, args=(1,))
c3.button("Valeurs moyennes", on_click=reinitialiser)

onglets = st.tabs(["Moyennes", "Erreurs", "Pires valeurs"])
groupes = [
    [f for f in FEATURES if f.startswith("mean ")],
    [f for f in FEATURES if f.endswith(" error")],
    [f for f in FEATURES if f.startswith("worst ")],
]
for onglet, colonnes in zip(onglets, groupes):
    with onglet:
        gauche, droite = st.columns(2)
        for i, f in enumerate(colonnes):
            (gauche if i % 2 == 0 else droite).number_input(
                f, key=f, format="%.5f", step=None
            )

st.divider()
if st.button("Prédire", type="primary"):
    cas = pd.DataFrame([{f: st.session_state[f] for f in FEATURES}])
    p_maligne = float(modele.predict_proba(cas)[0, 1])
    st.metric("Probabilité de tumeur maligne", f"{p_maligne:.1%}")
    st.progress(min(max(p_maligne, 0.0), 1.0))
    if p_maligne >= 0.5:
        st.error("Le modèle prédit : tumeur MALIGNE. À confirmer par un médecin.")
    else:
        st.success("Le modèle prédit : tumeur BÉNIGNE. À confirmer par un médecin.")
