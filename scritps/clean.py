#!/usr/bin/env python3
"""
Script pour nettoyer les fichiers texte du Guide de Régulation Médicale
Supprime les éléments de navigation, les répétitions et garde seulement le contenu médical
"""

import os
import re
from datetime import datetime

class NettoyeurFichiersMedicaux:
    def __init__(self, dossier_source="guide_medical_textes", dossier_sortie="fiches_medicales_clean"):
        """
        Initialise le nettoyeur
        
        Args:
            dossier_source: Dossier contenant les fichiers à nettoyer
            dossier_sortie: Dossier où sauvegarder les fichiers nettoyés
        """
        self.dossier_source = dossier_source
        self.dossier_sortie = dossier_sortie
        
        # Créer le dossier de sortie
        os.makedirs(dossier_sortie, exist_ok=True)
        
        # Compteurs
        self.fichiers_traites = 0
        self.fichiers_ignores = 0
        
        # Éléments à supprimer (navigation du site)
        self.elements_inutiles = [
            "Accès à la version ebook",
            "Annuaire",
            "SOMMAIRE",
            "GENERALITES",
            "MOTIFS DE RECOURS",
            "TRIAGE",
            "CARDIO-VASCULAIRE", 
            "RESPIRATOIRE",
            "NEUROLOGIE",
            "PSYCHIATRIE",
            "TRAUMATOLOGIE",
            "BRULURES ET FUMEES",
            "MORSURES ET PIQURES",
            "TOXICOLOGIE",
            "GYNECO OBST - NEONAT",
            "PEDIATRIE",
            "HEPATO GASTRO ENTEROLOGIE",
            "INFECTIOLOGIE",
            "ORL, STOMATO, OPHTALMO",
            "AUTRES PATHOLOGIES",
            "PATH CIRCONSTANCIELLES",
            "RISQUES SANITAIRES",
            "MALADIES RARES",
            "ORGANISATION",
            "DERNIERE PARTIE",
            "COUVERTURES",
            "DERNIÈRES MAJ",
            "Server response time:",
            "Tout déplier | Tout replier",
            "Date de mise à jour :"
        ]
    
    def nettoyer_texte(self, contenu):
        """
        Nettoie le contenu d'un fichier
        
        Args:
            contenu: Le texte à nettoyer
            
        Returns:
            Le texte nettoyé
        """
        lignes = contenu.split('\n')
        lignes_propres = []
        
        # Variables pour tracker où on est dans le fichier
        dans_header = True
        dans_contenu = False
        contenu_medical_commence = False
        
        for ligne in lignes:
            ligne_strip = ligne.strip()
            
            # Détecter le début du contenu médical
            if "CONTENU:" in ligne:
                dans_header = False
                dans_contenu = True
                continue
            
            # Détecter la fin du document
            if "FIN DU DOCUMENT" in ligne:
                break
            
            # Si on est dans le header, garder certaines infos
            if dans_header:
                if ligne.startswith("TITRE:") or ligne.startswith("URL:") or ligne.startswith("CATÉGORIE:"):
                    lignes_propres.append(ligne)
                continue
            
            # Si on est dans le contenu
            if dans_contenu:
                # Ignorer les lignes vides multiples
                if not ligne_strip and lignes_propres and not lignes_propres[-1].strip():
                    continue
                
                # Ignorer les éléments de navigation
                if any(elem in ligne for elem in self.elements_inutiles):
                    continue
                
                # Ignorer les lignes de séparation excessives
                if ligne_strip and all(c in '=-' for c in ligne_strip):
                    if len(ligne_strip) > 20:
                        continue
                
                # Détecter le vrai début du contenu médical (après la navigation)
                if not contenu_medical_commence:
                    # Le contenu médical commence souvent par "Introduction", "ARM" ou le titre en majuscules
                    if ligne_strip.startswith("Introduction") or ligne_strip == "ARM" or (ligne_strip.isupper() and len(ligne_strip) > 5):
                        contenu_medical_commence = True
                
                # Si le contenu médical a commencé, garder la ligne
                if contenu_medical_commence:
                    lignes_propres.append(ligne)
        
        return '\n'.join(lignes_propres)
    
    def extraire_contenu_medical(self, contenu):
        """
        Extrait uniquement le contenu médical structuré
        
        Args:
            contenu: Le texte complet du fichier
            
        Returns:
            Dictionnaire avec le contenu médical structuré
        """
        sections = {
            'titre': '',
            'categorie': '',
            'introduction': '',
            'arm': {
                'priorite': '',
                'savoir': '',
                'conseils': '',
                'adaptation': ''
            },
            'medecin_regulateur': '',
            'autres': []
        }
        
        lignes = contenu.split('\n')
        section_actuelle = None
        sous_section_arm = None
        buffer = []
        
        for ligne in lignes:
            ligne_strip = ligne.strip()
            
            # Extraire le titre
            if ligne.startswith("TITRE:"):
                sections['titre'] = ligne.replace("TITRE:", "").strip()
                continue
            
            # Extraire la catégorie
            if ligne.startswith("CATÉGORIE:"):
                sections['categorie'] = ligne.replace("CATÉGORIE:", "").strip()
                continue
            
            # Détecter les sections
            if ligne_strip == "Introduction":
                section_actuelle = 'introduction'
                buffer = []
                continue
            elif ligne_strip == "ARM":
                section_actuelle = 'arm'
                sous_section_arm = None
                buffer = []
                continue
            elif "Médecin régulateur" in ligne_strip:
                section_actuelle = 'medecin_regulateur'
                buffer = []
                continue
            
            # Dans la section ARM, détecter les sous-sections
            if section_actuelle == 'arm':
                if "déterminer le niveau de priorité" in ligne_strip:
                    sous_section_arm = 'priorite'
                    buffer = []
                    continue
                elif "chercher à savoir" in ligne_strip:
                    sous_section_arm = 'savoir'
                    buffer = []
                    continue
                elif "conseiller en attendant" in ligne_strip:
                    sous_section_arm = 'conseils'
                    buffer = []
                    continue
                elif "adapter la décision" in ligne_strip:
                    sous_section_arm = 'adaptation'
                    buffer = []
                    continue
            
            # Ajouter le contenu au buffer approprié
            if ligne_strip and section_actuelle:
                buffer.append(ligne_strip)
                
                # Sauvegarder le buffer dans la bonne section
                if section_actuelle == 'introduction':
                    sections['introduction'] = ' '.join(buffer)
                elif section_actuelle == 'arm' and sous_section_arm:
                    sections['arm'][sous_section_arm] = '\n'.join(buffer)
                elif section_actuelle == 'medecin_regulateur':
                    sections['medecin_regulateur'] = '\n'.join(buffer)
        
        return sections
    
    def formater_fiche_propre(self, sections):
        """
        Formate le contenu médical de manière claire et structurée
        
        Args:
            sections: Dictionnaire avec le contenu structuré
            
        Returns:
            Texte formaté proprement
        """
        output = []
        
        # Titre et catégorie
        if sections['titre']:
            output.append(f"# {sections['titre'].upper()}\n")
        if sections['categorie']:
            output.append(f"Catégorie: {sections['categorie']}\n")
        
        # Introduction
        if sections['introduction']:
            output.append("\n## INTRODUCTION\n")
            output.append(sections['introduction'])
        
        # Section ARM
        if any(sections['arm'].values()):
            output.append("\n\n## ASSISTANT DE RÉGULATION MÉDICALE (ARM)\n")
            
            if sections['arm']['priorite']:
                output.append("\n### Niveau de priorité")
                output.append(sections['arm']['priorite'])
            
            if sections['arm']['savoir']:
                output.append("\n### Éléments à rechercher")
                output.append(sections['arm']['savoir'])
            
            if sections['arm']['conseils']:
                output.append("\n### Conseils en attendant les secours")
                output.append(sections['arm']['conseils'])
            
            if sections['arm']['adaptation']:
                output.append("\n### Adaptation si régulation différée")
                output.append(sections['arm']['adaptation'])
        
        # Section Médecin régulateur
        if sections['medecin_regulateur']:
            output.append("\n\n## MÉDECIN RÉGULATEUR\n")
            output.append(sections['medecin_regulateur'])
        
        return '\n'.join(output)
    
    def traiter_fichier(self, chemin_fichier):
        """
        Traite un fichier individuel
        
        Args:
            chemin_fichier: Chemin complet du fichier à traiter
            
        Returns:
            True si le fichier a été traité avec succès
        """
        try:
            # Lire le fichier
            with open(chemin_fichier, 'r', encoding='utf-8') as f:
                contenu = f.read()
            
            # Nettoyer le contenu
            contenu_nettoye = self.nettoyer_texte(contenu)
            
            # Extraire et structurer le contenu médical
            sections = self.extraire_contenu_medical(contenu_nettoye)
            
            # Formater proprement
            contenu_final = self.formater_fiche_propre(sections)
            
            # Déterminer le nom du fichier de sortie
            nom_fichier = os.path.basename(chemin_fichier)
            
            # Créer la structure de dossiers dans la sortie
            chemin_relatif = os.path.relpath(chemin_fichier, self.dossier_source)
            dossier_parent = os.path.dirname(chemin_relatif)
            
            if dossier_parent:
                dossier_sortie_complet = os.path.join(self.dossier_sortie, dossier_parent)
                os.makedirs(dossier_sortie_complet, exist_ok=True)
            else:
                dossier_sortie_complet = self.dossier_sortie
            
            # Sauvegarder le fichier nettoyé
            chemin_sortie = os.path.join(dossier_sortie_complet, nom_fichier)
            with open(chemin_sortie, 'w', encoding='utf-8') as f:
                f.write(contenu_final)
            
            print(f"✅ Nettoyé: {nom_fichier}")
            return True
            
        except Exception as e:
            print(f"❌ Erreur sur {chemin_fichier}: {e}")
            return False
    
    def nettoyer_tous_les_fichiers(self):
        """
        Nettoie tous les fichiers du dossier source
        """
        print(f"\n🧹 NETTOYAGE DES FICHIERS MÉDICAUX")
        print(f"{'=' * 60}")
        print(f"📂 Dossier source: {self.dossier_source}")
        print(f"📂 Dossier sortie: {self.dossier_sortie}")
        print(f"{'=' * 60}\n")
        
        # Parcourir tous les fichiers
        for root, dirs, files in os.walk(self.dossier_source):
            # Ignorer les fichiers système
            files = [f for f in files if not f.startswith('_')]
            
            for fichier in files:
                if fichier.endswith('.txt'):
                    chemin_complet = os.path.join(root, fichier)
                    
                    if self.traiter_fichier(chemin_complet):
                        self.fichiers_traites += 1
                    else:
                        self.fichiers_ignores += 1
        
        # Rapport final
        print(f"\n{'=' * 60}")
        print(f"📊 RAPPORT DE NETTOYAGE")
        print(f"{'=' * 60}")
        print(f"✅ Fichiers nettoyés: {self.fichiers_traites}")
        print(f"⚠️  Fichiers ignorés: {self.fichiers_ignores}")
        print(f"📁 Fichiers propres dans: {self.dossier_sortie}/")
        print(f"{'=' * 60}\n")


def main():
    """Fonction principale"""
    import sys
    
    # Vérifier les arguments
    dossier_source = sys.argv[1] if len(sys.argv) > 1 else "guide_medical_textes"
    dossier_sortie = sys.argv[2] if len(sys.argv) > 2 else "fiches_medicales_clean"
    
    print("🏥 NETTOYEUR DE FICHES MÉDICALES")
    print("=" * 60)
    print("Ce script va:")
    print("  1. Lire tous les fichiers .txt du dossier source")
    print("  2. Supprimer la navigation et éléments inutiles")
    print("  3. Structurer le contenu médical")
    print("  4. Sauvegarder les fichiers propres")
    print("=" * 60)
    
    # Vérifier que le dossier source existe
    if not os.path.exists(dossier_source):
        print(f"\n❌ Erreur: Le dossier '{dossier_source}' n'existe pas!")
        print("Vérifiez le chemin ou lancez d'abord le scraper.")
        return
    
    # Demander confirmation
    input("\n▶️  Appuyez sur Entrée pour nettoyer les fichiers...")
    
    # Lancer le nettoyage
    nettoyeur = NettoyeurFichiersMedicaux(dossier_source, dossier_sortie)
    nettoyeur.nettoyer_tous_les_fichiers()


if __name__ == "__main__":
    main()