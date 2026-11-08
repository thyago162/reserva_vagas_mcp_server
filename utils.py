import re


def validar_formato_cpf(cpf: str) -> bool:
    """Verifica se o CPF possui exatamente 11 dígitos numéricos."""
    cpf_limpo = limpar_cpf(cpf)
    return len(cpf_limpo) == 11 and not cpf_limpo == cpf_limpo[0] * 11

def limpar_cpf(cpf):
    return re.sub(r'\D', '', cpf)