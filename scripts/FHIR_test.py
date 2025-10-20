import requests
import json
from datetime import datetime

class FHIRClient:
    """Client pour interroger des serveurs FHIR de démonstration"""
    
    def __init__(self, base_url="https://hapi.fhir.org/baseR4"):
        """
        Initialise le client FHIR
        
        Args:
            base_url: URL de base du serveur FHIR
        """
        self.base_url = base_url.rstrip('/')
        self.headers = {
            'Accept': 'application/fhir+json',
            'Content-Type': 'application/fhir+json'
        }
    
    def _make_request(self, endpoint, params=None):
        """
        Effectue une requête GET vers le serveur FHIR
        
        Args:
            endpoint: Point de terminaison (ex: /Patient)
            params: Paramètres de recherche (dict)
            
        Returns:
            dict: Réponse JSON du serveur
        """
        url = f"{self.base_url}{endpoint}"
        try:
            response = requests.get(url, headers=self.headers, params=params, timeout=10)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"❌ Erreur lors de la requête: {e}")
            return None
    
    def search_patient(self, name=None, birthdate=None, identifier=None):
        """
        Recherche des patients
        
        Args:
            name: Nom du patient
            birthdate: Date de naissance (format: YYYY-MM-DD)
            identifier: Identifiant du patient
            
        Returns:
            dict: Bundle de résultats
        """
        params = {}
        if name:
            params['name'] = name
        if birthdate:
            params['birthdate'] = birthdate
        if identifier:
            params['identifier'] = identifier
            
        print(f"🔍 Recherche de patients avec: {params}")
        return self._make_request('/Patient', params)
    
    def get_patient(self, patient_id):
        """
        Récupère un patient par son ID
        
        Args:
            patient_id: ID du patient
            
        Returns:
            dict: Ressource Patient
        """
        print(f"📋 Récupération du patient ID: {patient_id}")
        return self._make_request(f'/Patient/{patient_id}')
    
    def search_observations(self, patient_id, code=None, category=None, sort='-date'):
        """
        Recherche des observations pour un patient
        
        Args:
            patient_id: ID du patient
            code: Code LOINC de l'observation
            category: Catégorie (vital-signs, laboratory, etc.)
            sort: Tri des résultats (-date pour décroissant)
            
        Returns:
            dict: Bundle d'observations
        """
        params = {'patient': patient_id}
        if code:
            params['code'] = code
        if category:
            params['category'] = category
        if sort:
            params['_sort'] = sort
            
        print(f"🩺 Recherche d'observations pour le patient {patient_id}")
        return self._make_request('/Observation', params)
    
    def search_allergies(self, patient_id):
        """
        Recherche les allergies d'un patient
        
        Args:
            patient_id: ID du patient
            
        Returns:
            dict: Bundle d'allergies
        """
        params = {'patient': patient_id}
        print(f"⚠️  Recherche d'allergies pour le patient {patient_id}")
        return self._make_request('/AllergyIntolerance', params)
    
    def search_conditions(self, patient_id):
        """
        Recherche les conditions/diagnostics d'un patient
        
        Args:
            patient_id: ID du patient
            
        Returns:
            dict: Bundle de conditions
        """
        params = {'patient': patient_id}
        print(f"🏥 Recherche de conditions pour le patient {patient_id}")
        return self._make_request('/Condition', params)
    
    def search_medications(self, patient_id):
        """
        Recherche les prescriptions médicamenteuses d'un patient
        
        Args:
            patient_id: ID du patient
            
        Returns:
            dict: Bundle de prescriptions
        """
        params = {'patient': patient_id}
        print(f"💊 Recherche de médications pour le patient {patient_id}")
        return self._make_request('/MedicationRequest', params)
    
    def display_bundle_summary(self, bundle):
        """
        Affiche un résumé d'un Bundle FHIR
        
        Args:
            bundle: Bundle FHIR à afficher
        """
        if not bundle:
            print("❌ Aucune donnée à afficher")
            return
        
        if bundle.get('resourceType') != 'Bundle':
            # Ressource unique
            print(f"\n📄 Ressource: {bundle.get('resourceType')}")
            print(json.dumps(bundle, indent=2, ensure_ascii=False))
            return
        
        total = bundle.get('total', 0)
        entries = bundle.get('entry', [])
        
        print(f"\n✅ {total} résultat(s) trouvé(s)")
        print(f"📦 {len(entries)} entrée(s) dans ce bundle")
        
        for i, entry in enumerate(entries, 1):
            resource = entry.get('resource', {})
            resource_type = resource.get('resourceType', 'Unknown')
            resource_id = resource.get('id', 'N/A')
            
            print(f"\n--- Entrée {i} ---")
            print(f"Type: {resource_type}")
            print(f"ID: {resource_id}")
            
            # Affichage spécifique selon le type de ressource
            if resource_type == 'Patient':
                names = resource.get('name', [])
                if names:
                    name = names[0]
                    given = ' '.join(name.get('given', []))
                    family = name.get('family', '')
                    print(f"Nom: {given} {family}")
                birthdate = resource.get('birthDate', 'N/A')
                print(f"Date de naissance: {birthdate}")
                
            elif resource_type == 'Observation':
                code = resource.get('code', {}).get('text', 'N/A')
                value = resource.get('valueQuantity', {})
                print(f"Observation: {code}")
                if value:
                    print(f"Valeur: {value.get('value')} {value.get('unit', '')}")
                date = resource.get('effectiveDateTime', 'N/A')
                print(f"Date: {date}")
                
            elif resource_type == 'AllergyIntolerance':
                code = resource.get('code', {}).get('text', 'N/A')
                print(f"Allergie: {code}")
                criticality = resource.get('criticality', 'N/A')
                print(f"Criticité: {criticality}")


def demo_complete():
    """Démonstration complète du client FHIR"""
    
    print("=" * 60)
    print("🔬 DÉMONSTRATION CLIENT FHIR")
    print("=" * 60)
    
    # Initialisation avec le serveur HAPI
    client = FHIRClient("https://hapi.fhir.org/baseR4")
    
    # 1. Recherche de patients par nom
    print("\n" + "=" * 60)
    print("1️⃣  RECHERCHE DE PATIENTS PAR NOM")
    print("=" * 60)
    result = client.search_patient(name="Smith")
    client.display_bundle_summary(result)
    
    # 2. Récupération d'un patient spécifique
    if result and result.get('entry'):
        patient_id = result['entry'][0]['resource']['id']
        
        print("\n" + "=" * 60)
        print("2️⃣  RÉCUPÉRATION D'UN PATIENT SPÉCIFIQUE")
        print("=" * 60)
        patient = client.get_patient(patient_id)
        client.display_bundle_summary(patient)
        
        # 3. Recherche des observations du patient
        print("\n" + "=" * 60)
        print("3️⃣  OBSERVATIONS DU PATIENT")
        print("=" * 60)
        observations = client.search_observations(patient_id)
        client.display_bundle_summary(observations)
        
        # 4. Recherche des allergies
        print("\n" + "=" * 60)
        print("4️⃣  ALLERGIES DU PATIENT")
        print("=" * 60)
        allergies = client.search_allergies(patient_id)
        client.display_bundle_summary(allergies)
        
        # 5. Recherche des conditions
        print("\n" + "=" * 60)
        print("5️⃣  CONDITIONS/DIAGNOSTICS DU PATIENT")
        print("=" * 60)
        conditions = client.search_conditions(patient_id)
        client.display_bundle_summary(conditions)


def demo_simple():
    """Démonstration simple et rapide"""
    
    print("🔬 Démonstration simple du client FHIR\n")
    
    client = FHIRClient()
    
    # Recherche simple
    result = client.search_patient(name="Williams")
    
    if result and result.get('entry'):
        print(f"\n✅ {len(result['entry'])} patient(s) trouvé(s)")
        
        # Affiche le premier patient
        first_patient = result['entry'][0]['resource']
        print(f"\nPremier patient:")
        print(f"  ID: {first_patient.get('id')}")
        
        names = first_patient.get('name', [])
        if names:
            name = names[0]
            print(f"  Nom: {' '.join(name.get('given', []))} {name.get('family', '')}")


if __name__ == "__main__":
    # Choisis le mode de démonstration
    print("Choisissez le mode:")
    print("1. Démonstration complète")
    print("2. Démonstration simple")
    
    choice = input("\nVotre choix (1 ou 2): ").strip()
    
    if choice == "1":
        demo_complete()
    else:
        demo_simple()