import pytest

from utils import validar_cpf

@pytest.mark.parametrize("cpf, esperado", [
    ("52998224725", True),
    ("52998224726", False),   # dígito verificador errado
    ("11111111111", False),   # todos iguais
    ("1234567890", False),    # 10 dígitos
    ("", False),
])

def test_validar_cpf(cpf, esperado):
    assert validar_cpf(cpf) is esperado