"""
Script pour extraire les données de l'image fournie
"""
try:
    from PIL import Image
    import pytesseract
    HAS_OCR = True
except ImportError:
    HAS_OCR = False
    print("Modules OCR non disponibles. Installation: pip install pillow pytesseract")

def extraire_donnees_image(image_path):
    """Extrait les données de l'image en utilisant OCR"""
    if not HAS_OCR:
        print("OCR non disponible")
        return None
    
    try:
        image = Image.open(image_path)
        text = pytesseract.image_to_string(image, lang='fra')
        return text
    except Exception as e:
        print(f"Erreur lors de l'extraction: {e}")
        return None

if __name__ == "__main__":
    # Chemin de l'image
    image_path = r"C:\Users\pack2\.cursor\projects\x\assets\c__Users_pack2_AppData_Roaming_Cursor_User_workspaceStorage_7c88ec7ec04b75548b6d5372ab5c4782_images_image-eb835683-9a4b-447e-814c-7c858c1e554.png"
    
    print("Tentative d'extraction des données de l'image...")
    text = extraire_donnees_image(image_path)
    
    if text:
        print("\nTexte extrait:")
        print("=" * 80)
        print(text)
        print("=" * 80)
    else:
        print("\nImpossible d'extraire le texte. Veuillez fournir la liste manuellement.")
