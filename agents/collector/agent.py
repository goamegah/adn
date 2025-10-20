"""
Agent 1 : Collecteur de données MIMIC-III + Texte médical
Récupère et normalise les données patient
"""

import pandas as pd
import os
from typing import Dict, Any, Optional


class AgentCollecteur:
    """Agent 1 : Collecte les données patient depuis MIMIC-III ou texte"""
    
    def __init__(self, data_dir: str = "/home/bao/adn/data/MIMIC 3 DATASET"):
        self.data_dir = data_dir
        
    def _load_csv(self, name: str) -> pd.DataFrame:
        """Charge un fichier CSV"""
        path = os.path.join(self.data_dir, f"{name}.csv")
        return pd.read_csv(path, low_memory=False)
    
    def collecter_donnees_patient(self, subject_id: Optional[int] = None, texte_medical: Optional[str] = None) -> Dict[str, Any]:
        """
        Collecte les données patient depuis MIMIC-III OU depuis un texte médical
        
        Args:
            subject_id: ID patient MIMIC-III (optionnel)
            texte_medical: Texte libre du dossier médical (optionnel)
            
        Returns:
            Format normalisé compatible avec Agent 2
        """
        # Mode texte médical
        if texte_medical:
            return self._collecter_depuis_texte(texte_medical)
        
        # Mode MIMIC-III
        if subject_id is None:
            raise ValueError("Il faut fournir soit subject_id soit texte_medical")
        
        return self._collecter_depuis_mimic(subject_id)
    
    def _collecter_depuis_mimic(self, subject_id: int) -> Dict[str, Any]:
        """Collecte depuis MIMIC-III"""
        
        # Charger les tables
        patient = self._load_csv("PATIENTS").query(f"subject_id == {subject_id}").iloc[0]
        admissions = self._load_csv("ADMISSIONS").query(f"subject_id == {subject_id}")
        
        if len(admissions) == 0:
            raise ValueError(f"Aucune admission trouvée pour patient {subject_id}")
        
        admission = admissions.iloc[-1]
        hadm_id = admission['hadm_id']
        
        # Récupérer les autres données
        icustays = self._load_csv("ICUSTAYS").query(f"subject_id == {subject_id}")
        diagnoses = self._load_csv("DIAGNOSES_ICD").query(f"hadm_id == {hadm_id}")
        procedures = self._load_csv("PROCEDURES_ICD").query(f"hadm_id == {hadm_id}")
        prescriptions = self._load_csv("PRESCRIPTIONS").query(f"subject_id == {subject_id}")
        labevents = self._load_csv("LABEVENTS").query(f"subject_id == {subject_id}").tail(20)
        chartevents = self._load_csv("CHARTEVENTS").query(f"subject_id == {subject_id}").tail(50)
        microevents = self._load_csv("MICROBIOLOGYEVENTS").query(f"subject_id == {subject_id}")
        
        # Normaliser
        data_normalized = {
            "patient_normalized": {
                "id": str(subject_id),
                "source_type": "MIMIC_III_HOSPITAL",
                "age": self._calculate_age(patient['dob'], admission['admittime']),
                "sex": "homme" if patient['gender'] == 'M' else "femme",
                
                "admission": {
                    "type": admission['admission_type'],
                    "chief_complaint": admission['diagnosis'],
                    "date": admission['admittime'],
                    "location": admission['admission_location'],
                },
                
                "vitals_current": self._extract_vitals(chartevents),
                "labs": self._extract_labs(labevents),
                "cultures": self._extract_cultures(microevents),
                "diagnoses_icd": self._extract_diagnoses(diagnoses),
                "procedures_icd": self._extract_procedures(procedures),
                "medications_current": self._extract_medications(prescriptions),
                
                "medical_history": {
                    "known_conditions": self._extract_conditions(diagnoses),
                    "icu_stays": len(icustays),
                },
                
                "death_info": {
                    "expired": bool(patient['expire_flag']),
                    "dod": str(patient['dod']) if pd.notna(patient['dod']) else None,
                    "hospital_expire": bool(admission['hospital_expire_flag']),
                }
            }
        }
        
        return data_normalized
    
    def _collecter_depuis_texte(self, texte: str) -> Dict[str, Any]:
        """
        Convertit un texte médical libre en format normalisé
        SIMPLE : juste stocke le texte brut, Gemini l'analysera
        """
        return {
            "patient_normalized": {
                "id": "TEXT_INPUT",
                "source_type": "TEXTE_MEDICAL",
                "texte_brut": texte,
                "age": None,
                "sex": None,
                "admission": {
                    "type": "TEXTE_LIBRE",
                    "chief_complaint": "Voir texte brut",
                    "date": None,
                },
                "vitals_current": {},
                "labs": [],
                "cultures": [],
                "diagnoses_icd": [],
                "procedures_icd": [],
                "medications_current": [],
                "medical_history": {
                    "known_conditions": [],
                },
            }
        }
    
    def _calculate_age(self, dob, admittime):
        """Calcule l'âge au moment de l'admission"""
        try:
            dob = pd.to_datetime(dob)
            admit = pd.to_datetime(admittime)
            age = (admit - dob).days // 365
            return max(0, age)
        except:
            return None
    
    def _extract_vitals(self, chartevents: pd.DataFrame) -> Dict:
        """Extrait les derniers signes vitaux"""
        vitals = {}
        
        vital_mapping = {
            220045: "heart_rate",
            220179: "systolic_bp",
            220180: "diastolic_bp",
            220210: "respiratory_rate",
            223761: "temperature",
            220277: "spo2"
        }
        
        for _, row in chartevents.iterrows():
            item_id = row['itemid']
            if item_id in vital_mapping:
                name = vital_mapping[item_id]
                try:
                    value = float(row['valuenum']) if pd.notna(row['valuenum']) else None
                    if value:
                        vitals[name] = {
                            "value": value,
                            "unit": row.get('valueuom', ''),
                            "charttime": str(row['charttime'])
                        }
                except:
                    pass
        
        return vitals
    
    def _extract_labs(self, labevents: pd.DataFrame) -> list:
        """Extrait les résultats de laboratoire"""
        labs = []
        
        for _, row in labevents.iterrows():
            try:
                lab = {
                    "itemid": int(row['itemid']),
                    "charttime": str(row['charttime']),
                    "value": str(row['value']),
                    "valuenum": float(row['valuenum']) if pd.notna(row['valuenum']) else None,
                    "valueuom": str(row['valueuom']) if pd.notna(row['valueuom']) else None,
                    "flag": str(row['flag']) if pd.notna(row['flag']) else None,
                }
                labs.append(lab)
            except:
                pass
        
        return labs
    
    def _extract_cultures(self, microevents: pd.DataFrame) -> list:
        """Extrait les cultures microbiologiques"""
        cultures = []
        
        for _, row in microevents.iterrows():
            try:
                culture = {
                    "charttime": str(row['charttime']),
                    "spec_type": str(row['spec_type_desc']),
                    "organism": str(row['org_name']) if pd.notna(row['org_name']) else None,
                    "status": "POSITIVE" if pd.notna(row['org_name']) else "NEGATIVE",
                    "antibiotic": str(row['ab_name']) if pd.notna(row['ab_name']) else None,
                    "interpretation": str(row['interpretation']) if pd.notna(row['interpretation']) else None,
                }
                cultures.append(culture)
            except:
                pass
        
        return cultures
    
    def _extract_diagnoses(self, diagnoses: pd.DataFrame) -> list:
        """Extrait les diagnostics ICD-9"""
        dx_list = []
        
        for _, row in diagnoses.iterrows():
            dx_list.append({
                "icd9_code": str(row['icd9_code']),
                "seq_num": int(row['seq_num'])
            })
        
        return dx_list
    
    def _extract_procedures(self, procedures: pd.DataFrame) -> list:
        """Extrait les procédures ICD-9"""
        proc_list = []
        
        for _, row in procedures.iterrows():
            proc_list.append({
                "icd9_code": str(row['icd9_code']),
                "seq_num": int(row['seq_num'])
            })
        
        return proc_list
    
    def _extract_medications(self, prescriptions: pd.DataFrame) -> list:
        """Extrait les médicaments prescrits"""
        meds = []
        
        for _, row in prescriptions.tail(10).iterrows():
            try:
                meds.append({
                    "drug": str(row['drug']),
                    "dose": str(row['dose_val_rx']) if pd.notna(row['dose_val_rx']) else None,
                    "route": str(row['route']) if pd.notna(row['route']) else None,
                    "startdate": str(row['startdate']) if pd.notna(row['startdate']) else None,
                })
            except:
                pass
        
        return meds
    
    def _extract_conditions(self, diagnoses: pd.DataFrame) -> list:
        """Extrait les conditions connues"""
        try:
            icd_diag = self._load_csv("D_ICD_DIAGNOSES")
            
            conditions = []
            for _, row in diagnoses.iterrows():
                match = icd_diag[icd_diag['icd9_code'] == row['icd9_code']]
                if len(match) > 0:
                    conditions.append(match.iloc[0]['short_title'])
            
            return conditions[:5]
        except:
            return []


if __name__ == "__main__":
    agent1 = AgentCollecteur()
    
    # TEST 1 : Patient MIMIC-III
    print("="*80)
    print("TEST 1 : Patient MIMIC-III 10006")
    print("="*80)
    
    data = agent1.collecter_donnees_patient(subject_id=10006)
    print(f"✅ Age: {data['patient_normalized']['age']} ans")
    print(f"✅ Sexe: {data['patient_normalized']['sex']}")
    
    # TEST 2 : Texte médical
    print("\n" + "="*80)
    print("TEST 2 : Texte médical")
    print("="*80)
    
    texte = "Patient 65 ans, douleur thoracique, TA: 160/95"
    data_texte = agent1.collecter_donnees_patient(texte_medical=texte)
    print(f"✅ Source: {data_texte['patient_normalized']['source_type']}")
    print(f"✅ Texte: {data_texte['patient_normalized']['texte_brut'][:50]}...")