"""
Utilitaires de chiffrement symétrique (Fernet) pour les mots de passe.

La clé ENCRYPTION_KEY est lue depuis les variables d'environnement (.env).
IMPORTANT : Ne jamais changer la clé après la mise en production — tous les
mots de passe chiffrés deviendraient illisibles.
"""
from cryptography.fernet import Fernet, InvalidToken
from decouple import config

_fernet: Fernet | None = None


def _get_fernet() -> Fernet:
    global _fernet
    if _fernet is None:
        key = config('ENCRYPTION_KEY')
        _fernet = Fernet(key.encode())
    return _fernet


def encrypt_password(plain_text: str) -> str:
    """Chiffre un mot de passe en clair et retourne le texte chiffré (str)."""
    return _get_fernet().encrypt(plain_text.encode()).decode()


def decrypt_password(encrypted_text: str) -> str:
    """Déchiffre un texte chiffré et retourne le mot de passe en clair.

    Retourne '(indéchiffrable)' si la valeur stockée n'est pas un texte
    Fernet valide (ex. ancienne valeur en clair non migrée).
    """
    try:
        return _get_fernet().decrypt(encrypted_text.encode()).decode()
    except (InvalidToken, Exception):
        return '(indéchiffrable)'
