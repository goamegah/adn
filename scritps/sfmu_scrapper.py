#!/usr/bin/env python3
"""
Scraper simple avec Selenium pour le Guide de Régulation Médicale
Clique sur chaque fiche et récupère le texte visible
"""

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import time
import os
import re
from datetime import datetime

class SimpleSeleniumScraper:
    def __init__(self, output_dir="guide_medical_textes"):
        """
        Initialise le scraper avec Selenium
        
        Args:
            output_dir: Dossier où sauvegarder les textes
        """
        self.output_dir = output_dir
        self.base_url = "https://www.guide-regulation-medicale.fr/index.php?module=Fiche&action=ListView"
        
        print("🚀 Démarrage du scraper...")
        print(f"📁 Les fichiers seront sauvegardés dans: {output_dir}/")
        
        # Créer le dossier principal
        os.makedirs(output_dir, exist_ok=True)
        
        # Configuration du navigateur
        self.setup_driver()
        
        # Compteurs
        self.total_fiches = 0
        self.fiches_scrapees = 0
        self.erreurs = 0
    
    def setup_driver(self):
        """Configure le navigateur Chrome/Firefox"""
        try:
            # Essayer Chrome d'abord
            options = webdriver.ChromeOptions()
            options.add_argument('--headless')  # Mode sans fenêtre
            options.add_argument('--no-sandbox')
            options.add_argument('--disable-dev-shm-usage')
            options.add_argument('--disable-gpu')
            options.add_argument('--window-size=1920,1080')
            options.add_experimental_option('excludeSwitches', ['enable-logging'])
            
            self.driver = webdriver.Chrome(options=options)
            print("✅ Chrome configuré en mode headless")
        except:
            try:
                # Si Chrome ne marche pas, essayer Firefox
                options = webdriver.FirefoxOptions()
                options.add_argument('--headless')
                self.driver = webdriver.Firefox(options=options)
                print("✅ Firefox configuré en mode headless")
            except Exception as e:
                print("❌ Erreur: Impossible de lancer le navigateur")
                print("Installez Chrome ou Firefox et leurs drivers:")
                print("  pip install selenium")
                print("  Chrome: télécharger chromedriver")
                print("  Firefox: télécharger geckodriver")
                raise e
    
    def nettoyer_nom_fichier(self, texte):
        """Nettoie un texte pour en faire un nom de fichier valide"""
        # Enlever les caractères spéciaux
        texte = re.sub(r'[<>:"/\\|?*]', '', texte)
        # Remplacer les espaces multiples
        texte = re.sub(r'\s+', ' ', texte)
        # Limiter la longueur
        texte = texte[:100]
        return texte.strip()
    
    def creer_dossier_categorie(self, titre):
        """Crée un sous-dossier basé sur la catégorie du titre"""
        # Déterminer la catégorie basée sur des mots-clés
        categories = {
            'cardio': ['cardiaque', 'cœur', 'palpitation', 'hypertens', 'thoracique'],
            'respiratoire': ['respiratoire', 'dyspnée', 'asthme', 'thorax'],
            'neurologie': ['neurolog', 'convulsion', 'céphalée', 'malaise', 'AVC'],
            'pediatrie': ['enfant', 'nourrisson', 'pédiatr', 'nouveau-né'],
            'traumato': ['trauma', 'chute', 'plaie', 'fracture', 'accident'],
            'psychiatrie': ['psychiatr', 'suicid', 'angoisse', 'agitation'],
            'obstetrique': ['grossesse', 'accouchement', 'obstétric', 'enceinte'],
            'intoxication': ['intoxic', 'poison', 'overdose', 'drogue'],
            'urgences': ['urgence', 'SMUR', 'SAMU', 'régulation'],
            'divers': []  # Catégorie par défaut
        }
        
        titre_lower = titre.lower()
        
        for categorie, mots_cles in categories.items():
            if categorie == 'divers':
                continue
            for mot in mots_cles:
                if mot in titre_lower:
                    path = os.path.join(self.output_dir, categorie)
                    os.makedirs(path, exist_ok=True)
                    return categorie
        
        # Si aucune catégorie trouvée, mettre dans divers
        path = os.path.join(self.output_dir, 'divers')
        os.makedirs(path, exist_ok=True)
        return 'divers'
    
    def scraper_toutes_les_fiches(self):
        """Parcourt et scrape toutes les fiches du site"""
        print(f"\n📋 Chargement de la page principale...")
        print(f"URL: {self.base_url}")
        
        # Aller sur la page de liste
        self.driver.get(self.base_url)
        time.sleep(3)  # Attendre le chargement
        
        # Trouver tous les liens des fiches
        print("\n🔍 Recherche des fiches...")
        try:
            # Attendre que la page se charge
            WebDriverWait(self.driver, 20).until(
                EC.presence_of_element_located((By.TAG_NAME, "a"))
            )
            
            # Récupérer tous les liens
            liens = self.driver.find_elements(By.XPATH, "//a[contains(@href, 'FrontDetailView')]")
            
            # Stocker les infos des fiches
            fiches = []
            for lien in liens:
                titre = lien.text.strip()
                url = lien.get_attribute('href')
                if titre and url:
                    fiches.append({
                        'titre': titre,
                        'url': url
                    })
            
            self.total_fiches = len(fiches)
            print(f"✅ {self.total_fiches} fiches trouvées!")
            
            # Créer un fichier index
            index_path = os.path.join(self.output_dir, '_INDEX.txt')
            with open(index_path, 'w', encoding='utf-8') as f:
                f.write(f"INDEX DES FICHES - Guide de Régulation Médicale\n")
                f.write(f"Généré le: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"Total: {self.total_fiches} fiches\n")
                f.write("=" * 80 + "\n\n")
                
                for i, fiche in enumerate(fiches, 1):
                    f.write(f"{i:3d}. {fiche['titre']}\n")
            
            # Scraper chaque fiche
            for i, fiche in enumerate(fiches, 1):
                self.scraper_une_fiche(fiche, i)
                
        except TimeoutException:
            print("❌ Timeout: La page met trop de temps à charger")
        except Exception as e:
            print(f"❌ Erreur lors de la récupération des liens: {e}")
    
    def scraper_une_fiche(self, fiche, numero):
        """Scrape une fiche individuelle"""
        titre = fiche['titre']
        url = fiche['url']
        
        print(f"\n📄 [{numero}/{self.total_fiches}] {titre[:50]}...")
        
        try:
            # Aller sur la page de la fiche
            self.driver.get(url)
            time.sleep(2)  # Attendre le chargement
            
            # Attendre que le contenu se charge
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            
            # Récupérer tout le texte visible de la page
            body = self.driver.find_element(By.TAG_NAME, "body")
            texte_complet = body.text
            
            if not texte_complet or len(texte_complet) < 50:
                print(f"   ⚠️ Peu ou pas de contenu trouvé")
                self.erreurs += 1
                return
            
            # Déterminer la catégorie et créer le dossier
            categorie = self.creer_dossier_categorie(titre)
            
            # Créer le nom du fichier
            nom_fichier = f"{numero:03d}_{self.nettoyer_nom_fichier(titre)}.txt"
            chemin_fichier = os.path.join(self.output_dir, categorie, nom_fichier)
            
            # Sauvegarder le texte
            with open(chemin_fichier, 'w', encoding='utf-8') as f:
                # En-tête du fichier
                f.write("=" * 80 + "\n")
                f.write(f"FICHE N°{numero}\n")
                f.write("=" * 80 + "\n\n")
                f.write(f"TITRE: {titre}\n")
                f.write(f"URL: {url}\n")
                f.write(f"DATE DE RÉCUPÉRATION: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"CATÉGORIE: {categorie.upper()}\n")
                f.write("\n" + "=" * 80 + "\n")
                f.write("CONTENU:\n")
                f.write("=" * 80 + "\n\n")
                
                # Le contenu
                f.write(texte_complet)
                
                # Pied de page
                f.write("\n\n" + "=" * 80 + "\n")
                f.write("FIN DU DOCUMENT\n")
                f.write("=" * 80 + "\n")
            
            self.fiches_scrapees += 1
            print(f"   ✅ Sauvegardé dans: {categorie}/{nom_fichier}")
            print(f"   📊 {len(texte_complet)} caractères récupérés")
            
        except TimeoutException:
            print(f"   ❌ Timeout sur cette fiche")
            self.erreurs += 1
        except Exception as e:
            print(f"   ❌ Erreur: {e}")
            self.erreurs += 1
    
    def generer_rapport(self):
        """Génère un rapport final du scraping"""
        rapport_path = os.path.join(self.output_dir, '_RAPPORT.txt')
        
        with open(rapport_path, 'w', encoding='utf-8') as f:
            f.write("RAPPORT DE SCRAPING\n")
            f.write("=" * 80 + "\n\n")
            f.write(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"Site: Guide de Régulation Médicale\n\n")
            f.write("STATISTIQUES:\n")
            f.write("-" * 40 + "\n")
            f.write(f"Fiches trouvées: {self.total_fiches}\n")
            f.write(f"Fiches récupérées avec succès: {self.fiches_scrapees}\n")
            f.write(f"Erreurs: {self.erreurs}\n")
            f.write(f"Taux de réussite: {(self.fiches_scrapees/max(self.total_fiches,1))*100:.1f}%\n\n")
            
            # Lister les catégories et leur contenu
            f.write("ORGANISATION DES FICHIERS:\n")
            f.write("-" * 40 + "\n")
            for categorie in os.listdir(self.output_dir):
                if categorie.startswith('_'):
                    continue
                path = os.path.join(self.output_dir, categorie)
                if os.path.isdir(path):
                    nb_fichiers = len([f for f in os.listdir(path) if f.endswith('.txt')])
                    f.write(f"  {categorie}/: {nb_fichiers} fiches\n")
        
        print(f"\n📊 Rapport sauvegardé: {rapport_path}")
    
    def run(self):
        """Lance le scraping complet"""
        try:
            print("\n" + "=" * 80)
            print("DÉBUT DU SCRAPING")
            print("=" * 80)
            
            # Scraper toutes les fiches
            self.scraper_toutes_les_fiches()
            
            # Générer le rapport
            self.generer_rapport()
            
            print("\n" + "=" * 80)
            print("SCRAPING TERMINÉ!")
            print("=" * 80)
            print(f"\n✅ Succès: {self.fiches_scrapees}/{self.total_fiches} fiches")
            print(f"❌ Erreurs: {self.erreurs}")
            print(f"📁 Fichiers sauvés dans: {self.output_dir}/")
            
        except KeyboardInterrupt:
            print("\n\n⚠️ Scraping interrompu par l'utilisateur")
        except Exception as e:
            print(f"\n❌ Erreur fatale: {e}")
        finally:
            # Fermer le navigateur
            if hasattr(self, 'driver'):
                self.driver.quit()
                print("\n🔒 Navigateur fermé")


def main():
    """Fonction principale"""
    import sys
    
    # Vérifier si un dossier de sortie est spécifié
    output_dir = sys.argv[1] if len(sys.argv) > 1 else "guide_medical_textes"
    
    print("🏥 SCRAPER - Guide de Régulation Médicale")
    print("=" * 80)
    print("Ce script va:")
    print("  1. Ouvrir un navigateur en mode invisible")
    print("  2. Aller sur chaque fiche médicale")
    print("  3. Récupérer tout le texte visible")
    print("  4. Organiser les fichiers par catégorie")
    print("=" * 80)
    
    # Demander confirmation
    reponse = input("\n▶️  Appuyez sur Entrée pour commencer (ou Ctrl+C pour annuler)...")
    
    # Lancer le scraper
    scraper = SimpleSeleniumScraper(output_dir=output_dir)
    scraper.run()


if __name__ == "__main__":
    main()