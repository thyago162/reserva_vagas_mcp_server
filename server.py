from mcp.server import MCPServer

mcp = MCPServer("ReservaVagasMcp")
import httpx

@mcp.tool()
def listar_escolas() -> object:
    """
    Busca na api a lista de escolas.

    ATENÇÃO/REGRA DE NEGÓCIO: Antes de chamar esta ferramenta para um candidato, você DEVIDAMENTE DEVE:
    1. Pedir os dados do candidato: (cpf, nome, data de nascimento)
    2. Chamar a ferramenta 'verificar_reserva_existe', informando o CPF do candidato.
    Só prossiga para a listar as escolas se o candidato não possuir uma reserva ativa (PENDENTE OU RECUSADO)

    O retorno traz as escolas com as seguintes informações:
    Dados da escola.
    Endereço da escola
    Escolaridades que a escola atende.
    Turnos que a escola atende.
    As vagas dispoíveis na escola.
    Caso a api retorne erro acima de 300, informar ao usuário que o sistema está fora do ar
    """
    try:
        response = httpx.get("http://localhost:3000/escolas")
        if response.status_code >= 300:
            return {
                "erro": True,
                "mensagem": "O sistema está fora do ar no momento. Tente novamente mais tarde."
            }

        return response.json()
    except httpx.RequestError:
        return {
            "erro": True,
            "mensagem": "O sistema está fora do ar no momento. (Falha de conexão)"
        }
   

@mcp.tool()
def verificar_reserva_existe(cpf_candidato: str) -> object:
    """
    Verifica na api se o candidato já possui uma reserva ativa.
    A reserva é considerada ativa se for PENDENTE OU APROVADO.
    Retorna para o usuário as informações da reserva.
    Caso a reserva seja ativa (PENDENTE OU APROVADO) adicione a resposta:
    1. informar que não é possível realizar uma nova reserva, pois a mesma encontra-se ativa
    2. Se estiver cancelada, informar que uma nova reserva poderá ser feita.
    Caso a api retorne erro acima de 300, informar ao usuário que o sistema está fora do ar
    """
    try:
        url = f"http://localhost:3000/candidato/candidato-possui-reserva/${cpf_candidato}"
        response = httpx.get(url)
        
        if response.status_code >= 300:
            return {
                "erro": True,
                "mensagem": response.json()
            }

        return response.json()

    except httpx.RequestError:
        return {
            "erro": True,
            "mensagem": "O sistema está fora do ar no momento (falha de conexão)."
        }
 


if __name__ == "__main__":
    mcp.run(transport="stdio")
