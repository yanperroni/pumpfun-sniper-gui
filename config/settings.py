"""
Gerenciador de configuracoes - salva/carrega em JSON
"""
import json
import os
import sys
from dataclasses import dataclass, asdict
from typing import Optional


# Caminho do arquivo de config (na mesma pasta do exe)
def get_config_path():
    """Retorna caminho do config.json"""
    if getattr(sys, 'frozen', False):
        # Rodando como exe
        base = os.path.dirname(sys.executable)
    else:
        # Rodando como script
        base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base, 'config.json')


@dataclass
class Settings:
    # API
    api_key: str = ""

    # Buy settings
    buy_amount: float = 5.0  # SOL
    slippage: int = 49  # %
    priority_fee: float = 0.12  # SOL
    num_attempts: int = 5
    delay_between: float = 0.5  # segundos

    # Coordenadas
    view_coin_x: int = 764
    view_coin_y: int = 344
    ca_area_x: int = 440
    ca_area_y: int = 198

    # Tesseract
    tesseract_path: str = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

    # Avancado
    scan_interval: float = 0.15
    chart_load_time: float = 2.5

    def to_dict(self) -> dict:
        """Converte para dicionario"""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> 'Settings':
        """Cria Settings a partir de dicionario"""
        # Filtrar apenas campos validos
        valid_fields = {k: v for k, v in data.items() if k in cls.__dataclass_fields__}
        return cls(**valid_fields)

    def save(self, path: Optional[str] = None):
        """Salva configuracoes em JSON"""
        if path is None:
            path = get_config_path()

        with open(path, 'w', encoding='utf-8') as f:
            json.dump(self.to_dict(), f, indent=2, ensure_ascii=False)

    @classmethod
    def load(cls, path: Optional[str] = None) -> 'Settings':
        """Carrega configuracoes de JSON"""
        if path is None:
            path = get_config_path()

        if not os.path.exists(path):
            # Retorna config padrao
            return cls()

        try:
            with open(path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            return cls.from_dict(data)
        except Exception as e:
            print(f"Erro ao carregar config: {e}")
            return cls()


# Instancia global
_settings: Optional[Settings] = None

def get_settings() -> Settings:
    """Retorna instancia global das settings"""
    global _settings
    if _settings is None:
        _settings = Settings.load()
    return _settings

def save_settings():
    """Salva instancia global"""
    global _settings
    if _settings is not None:
        _settings.save()
