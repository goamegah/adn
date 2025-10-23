# Script pour inspecter et gérer vos corpus RAG Vertex AI

from google.auth import default
import vertexai
from vertexai.preview import rag
import os
from dotenv import load_dotenv
from datetime import datetime

load_dotenv()

PROJECT_ID = os.getenv("GOOGLE_CLOUD_PROJECT")
LOCATION = os.getenv("GOOGLE_CLOUD_LOCATION")


def initialize_vertex_ai():
    credentials, _ = default()
    vertexai.init(project=PROJECT_ID, location=LOCATION, credentials=credentials)


def list_all_corpora():
    """Liste tous les corpus disponibles."""
    print("\n" + "="*80)
    print("CORPUS DISPONIBLES")
    print("="*80 + "\n")
    
    corpora = list(rag.list_corpora())
    
    if not corpora:
        print("Aucun corpus trouvé.")
        return []
    
    for i, corpus in enumerate(corpora, 1):
        print(f"[{i}] {corpus.display_name}")
        print(f"    Name: {corpus.name}")
        print(f"    Description: {corpus.description}")
        print(f"    Embedding Model: {corpus.embedding_model_config.publisher_model}")
        print()
    
    return corpora


def inspect_corpus(corpus_name):
    """Affiche les détails d'un corpus spécifique."""
    print("\n" + "="*80)
    print(f"INSPECTION DU CORPUS: {corpus_name}")
    print("="*80 + "\n")
    
    try:
        # Lister tous les fichiers
        files = list(rag.list_files(corpus_name=corpus_name))
        
        print(f"Nombre total de fichiers: {len(files)}\n")
        
        if files:
            print("Liste des fichiers:")
            print("-" * 80)
            for i, file in enumerate(files, 1):
                print(f"\n[{i}] {file.display_name}")
                print(f"    Resource Name: {file.name}")
                print(f"    Description: {file.description}")
                
                # Informations supplémentaires si disponibles
                if hasattr(file, 'create_time'):
                    print(f"    Created: {file.create_time}")
                if hasattr(file, 'size_bytes'):
                    size_mb = file.size_bytes / (1024 * 1024)
                    print(f"    Size: {size_mb:.2f} MB")
        else:
            print("Aucun fichier trouvé dans ce corpus.")
            
    except Exception as e:
        print(f"Erreur lors de l'inspection: {e}")


def delete_file_from_corpus(corpus_name, file_name):
    """Supprime un fichier spécifique du corpus."""
    try:
        rag.delete_file(name=file_name)
        print(f"Fichier supprimé: {file_name}")
    except Exception as e:
        print(f"Erreur lors de la suppression: {e}")


def delete_corpus(corpus_name):
    """Supprime un corpus entier."""
    try:
        rag.delete_corpus(name=corpus_name)
        print(f"Corpus supprimé: {corpus_name}")
    except Exception as e:
        print(f"Erreur lors de la suppression: {e}")


def interactive_menu():
    """Menu interactif pour gérer les corpus."""
    initialize_vertex_ai()
    
    while True:
        print("\n" + "="*80)
        print("MENU PRINCIPAL - RAG CORPUS MANAGER")
        print("="*80)
        print("\n1. Lister tous les corpus")
        print("2. Inspecter un corpus spécifique")
        print("3. Supprimer un fichier d'un corpus")
        print("4. Supprimer un corpus entier")
        print("5. Quitter")
        
        choice = input("\nVotre choix (1-5): ").strip()
        
        if choice == "1":
            list_all_corpora()
            
        elif choice == "2":
            corpus_name = input("\nEntrez le nom complet du corpus: ").strip()
            if corpus_name:
                inspect_corpus(corpus_name)
            else:
                print("Nom de corpus invalide.")
                
        elif choice == "3":
            corpus_name = input("\nEntrez le nom du corpus: ").strip()
            if corpus_name:
                inspect_corpus(corpus_name)
                file_name = input("\nEntrez le nom complet du fichier à supprimer: ").strip()
                if file_name:
                    confirm = input(f"Confirmer la suppression de '{file_name}' ? (oui/non): ").strip().lower()
                    if confirm == "oui":
                        delete_file_from_corpus(corpus_name, file_name)
                else:
                    print("Nom de fichier invalide.")
            else:
                print("Nom de corpus invalide.")
                
        elif choice == "4":
            corpora = list_all_corpora()
            if corpora:
                corpus_name = input("\nEntrez le nom complet du corpus à supprimer: ").strip()
                if corpus_name:
                    confirm = input(f"ATTENTION: Supprimer le corpus '{corpus_name}' et TOUS ses fichiers ? (oui/non): ").strip().lower()
                    if confirm == "oui":
                        delete_corpus(corpus_name)
                else:
                    print("Nom de corpus invalide.")
                    
        elif choice == "5":
            print("\nAu revoir!")
            break
            
        else:
            print("Choix invalide. Veuillez choisir entre 1 et 5.")
        
        input("\nAppuyez sur Entrée pour continuer...")


def quick_inspect():
    """Inspection rapide du corpus configuré dans .env."""
    initialize_vertex_ai()
    
    corpus_name = os.getenv("RAG_CORPUS")
    
    if not corpus_name:
        print("Aucun corpus configuré dans RAG_CORPUS.")
        print("Listage de tous les corpus disponibles:\n")
        list_all_corpora()
    else:
        inspect_corpus(corpus_name)


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "--quick":
        # Mode inspection rapide
        quick_inspect()
    else:
        # Mode interactif
        interactive_menu()