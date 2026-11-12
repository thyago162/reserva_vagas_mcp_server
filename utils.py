import re

def limpar_cpf(cpf: str) -> str:
    return re.sub(r"\D", "", cpf or "")

def validar_cpf(cpf_limpo: str) -> bool:
    """Recebe o CPF só com dígitos. Valida o formato e os dois dígitos verificadores."""
    if len(cpf_limpo) != 11 or len(set(cpf_limpo)) == 1:
        return False

    for posicao in (9, 10):
        soma = sum(int(cpf_limpo[i]) * (posicao + 1 - i) for i in range(posicao))
        digito = (soma * 10 % 11) % 10
        if digito != int(cpf_limpo[posicao]):
            return False

    return True