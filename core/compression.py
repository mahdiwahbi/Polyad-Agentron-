import zlib
import bz2
import lzma
import logging
from typing import Dict, Any, Optional, Union
from utils.logger import logger

class CompressionManager:
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.logger = logging.getLogger('polyad.compression')
        
        # Configuration de compression
        self.compression_config = config.get('compression', {
            'default_method': 'zlib',
            'methods': {
                'zlib': {
                    'level': 9,
                    'window_bits': 15
                },
                'bz2': {
                    'level': 9,
                    'compresslevel': 9
                },
                'lzma': {
                    'level': 9,
                    'preset': 9
                }
            },
            'chunk_size': 65536,
            'parallel_compression': True,
            'max_parallel_tasks': 4
        })
        
        # Statistiques de compression
        self.compression_stats = {
            'total_compressed': 0,
            'total_uncompressed': 0,
            'compression_ratio': 0.0,
            'methods_used': {
                'zlib': 0,
                'bz2': 0,
                'lzma': 0
            }
        }

    def compress_data(self, data: Union[str, bytes], method: Optional[str] = None) -> bytes:
        """Compresse les données avec la méthode spécifiée"""
        if isinstance(data, str):
            data = data.encode('utf-8')
            
        method = method or self.compression_config['default_method']
        
        if method not in self.compression_config['methods']:
            raise ValueError(f"Méthode de compression non supportée: {method}")
            
        config = self.compression_config['methods'][method]
        
        if method == 'zlib':
            compressed = zlib.compress(
                data,
                level=config['level'],
                wbits=config['window_bits']
            )
        elif method == 'bz2':
            compressed = bz2.compress(
                data,
                compresslevel=config['level']
            )
        elif method == 'lzma':
            compressed = lzma.compress(
                data,
                preset=config['preset']
            )
            
        # Mettre à jour les statistiques
        self._update_stats(len(data), len(compressed), method)
        
        return compressed

    def decompress_data(self, data: bytes, method: Optional[str] = None) -> bytes:
        """Décompresse les données avec la méthode spécifiée"""
        method = method or self.compression_config['default_method']
        
        if method not in self.compression_config['methods']:
            raise ValueError(f"Méthode de compression non supportée: {method}")
            
        if method == 'zlib':
            decompressed = zlib.decompress(data)
        elif method == 'bz2':
            decompressed = bz2.decompress(data)
        elif method == 'lzma':
            decompressed = lzma.decompress(data)
            
        return decompressed

    def _update_stats(self, original_size: int, compressed_size: int, method: str) -> None:
        """Met à jour les statistiques de compression"""
        self.compression_stats['total_compressed'] += compressed_size
        self.compression_stats['total_uncompressed'] += original_size
        self.compression_stats['compression_ratio'] = (
            self.compression_stats['total_compressed'] / 
            self.compression_stats['total_uncompressed']
        )
        self.compression_stats['methods_used'][method] += 1

    def get_compression_stats(self) -> Dict[str, Any]:
        """Obtient les statistiques de compression"""
        return {
            'total_compressed': self.compression_stats['total_compressed'],
            'total_uncompressed': self.compression_stats['total_uncompressed'],
            'compression_ratio': self.compression_stats['compression_ratio'],
            'methods_used': self.compression_stats['methods_used'],
            'method_efficiency': {
                method: {
                    'count': count,
                    'ratio': (
                        self.compression_stats['methods_used'][method] / 
                        sum(self.compression_stats['methods_used'].values())
                    ) if sum(self.compression_stats['methods_used'].values()) > 0 else 0
                }
                for method, count in self.compression_stats['methods_used'].items()
            }
        }

    def get_best_compression_method(self, sample_data: bytes) -> str:
        """Détermine la meilleure méthode de compression pour les données"""
        results = {}
        
        for method in self.compression_config['methods']:
            compressed = self.compress_data(sample_data, method)
            ratio = len(compressed) / len(sample_data)
            results[method] = {
                'size': len(compressed),
                'ratio': ratio
            }
            
        # Retourner la méthode avec le meilleur ratio
        return min(results.items(), key=lambda x: x[1]['ratio'])[0]

    def compress_file(self, input_path: str, output_path: str, method: Optional[str] = None) -> None:
        """Compresse un fichier"""
        method = method or self.compression_config['default_method']
        
        with open(input_path, 'rb') as f_in:
            with open(output_path, 'wb') as f_out:
                while True:
                    chunk = f_in.read(self.compression_config['chunk_size'])
                    if not chunk:
                        break
                        
                    compressed = self.compress_data(chunk, method)
                    f_out.write(compressed)

    def decompress_file(self, input_path: str, output_path: str, method: Optional[str] = None) -> None:
        """Décompresse un fichier"""
        method = method or self.compression_config['default_method']
        
        with open(input_path, 'rb') as f_in:
            with open(output_path, 'wb') as f_out:
                while True:
                    chunk = f_in.read(self.compression_config['chunk_size'])
                    if not chunk:
                        break
                        
                    decompressed = self.decompress_data(chunk, method)
                    f_out.write(decompressed)
