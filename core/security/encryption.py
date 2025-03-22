"""
Module de chiffrement pour Polyad
Fournit des fonctionnalités de chiffrement et déchiffrement des données sensibles
"""

from typing import Optional, Tuple
import os
import base64
import hashlib
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.primitives import serialization
import logging

logger = logging.getLogger('polyad.security')

class EncryptionManager:
    def __init__(self, key: Optional[str] = None, salt: Optional[bytes] = None):
        """Initialise le gestionnaire de chiffrement
        
        Args:
            key (str, optional): Clé de chiffrement. Si non fournie, une clé sera générée
            salt (bytes, optional): Sel pour la dérivation de clé. Si non fourni, un sel sera généré
        """
        self.key = key
        self.salt = salt if salt is not None else os.urandom(16)
        self._derived_key = None
        self._private_key = None
        self._public_key = None
        
        # Générer les clés RSA si nécessaire
        if not self.key:
            self._generate_rsa_keys()
            self._derive_key()
        else:
            self._derive_key()

    def _generate_rsa_keys(self) -> None:
        """Génère une paire de clés RSA"""
        self._private_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=2048
        )
        self._public_key = self._private_key.public_key()

    def _derive_key(self) -> None:
        """Dérive une clé de chiffrement à partir de la clé principale"""
        if self.key:
            kdf = PBKDF2HMAC(
                algorithm=hashes.SHA256(),
                length=32,
                salt=self.salt,
                iterations=100000
            )
            self._derived_key = kdf.derive(self.key.encode())

    def encrypt(self, data: str) -> str:
        """Chiffre les données
        
        Args:
            data (str): Données à chiffrer
            
        Returns:
            str: Données chiffrées encodées en base64
        """
        if not self._derived_key:
            raise ValueError("Clé de chiffrement non initialisée")
            
        # Générer un IV aléatoire
        iv = os.urandom(16)
        
        # Chiffrer les données
        cipher = Cipher(algorithms.AES(self._derived_key), modes.CBC(iv))
        encryptor = cipher.encryptor()
        
        # Padding pour AES
        padded_data = self._pad(data.encode())
        encrypted = encryptor.update(padded_data) + encryptor.finalize()
        
        # Retourner IV + données chiffrées encodées en base64
        return base64.b64encode(iv + encrypted).decode()

    def decrypt(self, encrypted_data: str) -> str:
        """Déchiffre les données
        
        Args:
            encrypted_data (str): Données chiffrées encodées en base64
            
        Returns:
            str: Données déchiffrées
        """
        if not self._derived_key:
            raise ValueError("Clé de chiffrement non initialisée")
            
        try:
            # Décoder et extraire IV
            data = base64.b64decode(encrypted_data)
            iv = data[:16]
            encrypted = data[16:]
            
            # Déchiffrer
            cipher = Cipher(algorithms.AES(self._derived_key), modes.CBC(iv))
            decryptor = cipher.decryptor()
            decrypted = decryptor.update(encrypted) + decryptor.finalize()
            
            # Retirer le padding
            return self._unpad(decrypted).decode()
            
        except Exception as e:
            logger.error(f"Erreur lors du déchiffrement: {e}")
            raise

    def _pad(self, s: bytes) -> bytes:
        """Ajoute le padding PKCS7"""
        padding_size = 16 - (len(s) % 16)
        return s + bytes([padding_size] * padding_size)

    def _unpad(self, s: bytes) -> bytes:
        """Retire le padding PKCS7"""
        return s[:-s[-1]]

    def encrypt_rsa(self, data: str) -> str:
        """Chiffre les données avec RSA
        
        Args:
            data (str): Données à chiffrer
            
        Returns:
            str: Données chiffrées encodées en base64
        """
        if not self._public_key:
            raise ValueError("Clé publique non initialisée")
            
        encrypted = self._public_key.encrypt(
            data.encode(),
            padding.OAEP(
                mgf=padding.MGF1(algorithm=hashes.SHA256()),
                algorithm=hashes.SHA256(),
                label=None
            )
        )
        return base64.b64encode(encrypted).decode()

    def decrypt_rsa(self, encrypted_data: str) -> str:
        """Déchiffre les données avec RSA
        
        Args:
            encrypted_data (str): Données chiffrées encodées en base64
            
        Returns:
            str: Données déchiffrées
        """
        if not self._private_key:
            raise ValueError("Clé privée non initialisée")
            
        try:
            encrypted = base64.b64decode(encrypted_data)
            decrypted = self._private_key.decrypt(
                encrypted,
                padding.OAEP(
                    mgf=padding.MGF1(algorithm=hashes.SHA256()),
                    algorithm=hashes.SHA256(),
                    label=None
                )
            )
            return decrypted.decode()
            
        except Exception as e:
            logger.error(f"Erreur lors du déchiffrement RSA: {e}")
            raise

    def export_keys(self) -> Tuple[str, str]:
        """Exporte les clés publique et privée
        
        Returns:
            Tuple[str, str]: (clé publique encodée, clé privée encodée)
        """
        if not self._private_key or not self._public_key:
            raise ValueError("Clés non initialisées")
            
        public_pem = self._public_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
        )
        
        private_pem = self._private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption()
        )
        
        return (public_pem.decode(), private_pem.decode())
