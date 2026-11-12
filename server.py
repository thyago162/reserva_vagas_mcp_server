import os
from typing import Any, Dict, List
from mcp.server import MCPServer
from dotenv import load_dotenv
import httpx
from utils import validar_formato_cpf, limpar_cpf
from mcp.types import ToolAnnotations


load_dotenv()
_token_cache = None

mcp = MCPServer("ReservaVagasMcp")

def _auth_headers(force=False):
       global _token_cache
       if force:
           _token_cache = None
       return {"Authorization": f"Bearer {obter_token_mcp()}"}

def obter_token_mcp() -> str:
    global _token_cache
    if _token_cache:
        return _token_cache
    
    # Faz o login com o usuário MCP criado no Go
    response = httpx.post(os.getenv("BACKEND_API") + "login", json={
        "email": os.getenv("MCP_EMAIL"),
        "senha": os.getenv("MCP_PWD")
    }, timeout=10.0)

    if response.status_code == 401:
        _auth_headers
    
    if response.status_code == 200:
        data = response.json()
        print(data)
        _token_cache = data.get("access_token") # Ou o formato que seu backend retorna o JWT
        return _token_cache
    
    raise Exception("Falha ao autenticar o usuário MCP no backend Go.")

@mcp.tool(annotations=ToolAnnotations(
    readOnlyHint=True, destructiveHint=False,
    idempotentHint=True, openWorldHint=True))

def listar_escolas(data_nascimento: str, latitude: str, longitude: str) -> List[Dict[str, Any]]:
    """
    Busca e retorna uma LISTA (array) de escolas disponíveis que possuem vagas ativas 
    próximas à localização informada.
    IMPORTANTE: Analise TODOS os itens da lista retornada. Cada item representa uma escola 
    com suas respetivas 'VagasEscolares'. Verifique todas as opções antes de responder ao usuário.

    ATENÇÃO/REGRA DE NEGÓCIO: Antes de chamar esta ferramenta para um candidato, você DEVIDAMENTE DEVE:
    1. Pedir os dados do candidato: (cpf, nome, data de nascimento, logradouro)
    2. Chamar a ferramenta 'verificar_reserva_existe', informando o CPF do candidato.
    3. Chamar a ferramenta 'obter_lat_long' para pegar a latitude e longitude do endereço, infomração nescessária para calculo de distância.
    Só prossiga para a listar as escolas se o candidato não possuir uma reserva ativa (PENDENTE OU APROVADO)

    O retorno traz as escolas com as seguintes informações:
    Dados da escola.
    Endereço da escola
    Escolaridades que a escola atende.
    Turnos que a escola atende.
    As vagas dispoíveis na escola.
    Caso a api retorne erro acima de 300, informar ao usuário que o sistema está fora do ar
    Caso a api retorne as escolas com as vagas escolares vazias, informar que não encontrou nenhuma escola com vagas disponíveis.
    """
    try:
        token = obter_token_mcp()
        headers = {"Authorization": f"Bearer {token}"}

        params = {
            "data_nascimento": data_nascimento.replace("/", "-"),
            "latitude": latitude,
            "longitude": longitude
        }
        
        response = httpx.get(os.getenv("BACKEND_API") + "escolas/get-escolas-dt-nascimento", params=params, headers=headers)
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
   

@mcp.tool(annotations=ToolAnnotations(
    readOnlyHint=True, destructiveHint=False,
    idempotentHint=True, openWorldHint=True))
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
        cpf = validar_formato_cpf(cpf_candidato)
        url = os.getenv("BACKEND_API") + f"candidato/candidato-possui-reserva/{cpf}"
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
 

@mcp.tool(annotations=ToolAnnotations(
    readOnlyHint=False, destructiveHint=False,
    idempotentHint=True, openWorldHint=True))
def realizar_reserva(
    nome_candidato: str,
    cpf_candidato: str,
    dt_nascimento_candidato: str,
    nome_responsavel: str,
    cpf_responsavel: str,
    dt_nascimento_responsavel: str,
    email_responsavel: str,
    telefone: str,
    tipo_logradouro: str,
    logradouro: str,
    numero: str,
    complemento: str,
    bairro: str,
    cidade: str,
    uf: str,
    cep: str,
    latitude: float,
    longitude: float,
    escolaridade_id: str,
    turno_id: str,
    vaga_id: str,
    escola_id: str
) -> object:
    """
    Envia as informações do candidato e responsável para realizar a reserva/matrícula na API.
    
    Todos os campos acima são OBRIGATÓRIOS. Se qualquer um dos dados estiver faltando, 
    o sistema deverá pedir novamente ao usuário antes de chamar esta ferramenta.
    
    Se o status for 201 a API retornará as informações sobre o candidato e a reserva realizada.
    Se o status for maior que 300, a API retornará o erro adequado.
    """
    try:
        token = obter_token_mcp()
        headers = {"Authorization": f"Bearer {token}"}
        cpf_cand = limpar_cpf(cpf_candidato)
        cpf_res = limpar_cpf(cpf_responsavel)
        
        # 2. Monta o payload de reserva com todos os dados recebidos
        payload = {
            "nome_candidato": nome_candidato,
            "cpf_candidato": cpf_cand,
            "dt_nascimento_candidato": dt_nascimento_candidato,
            "nome_responsavel": nome_responsavel,
            "cpf_responsavel": cpf_res,
            "dt_nascimento_responsavel": dt_nascimento_responsavel,
            "email_responsavel": email_responsavel,
            "telefone": telefone,
            "tipo_logradouro": tipo_logradouro,
            "logradouro": logradouro,
            "numero": numero,
            "complemento": complemento,
            "bairro": bairro,
            "cidade": cidade,
            "uf": uf,
            "cep": cep,
            "latitude": latitude,
            "longitude": longitude,
            "escolaridade_id": escolaridade_id,
            "turno_id": turno_id,
            "vaga_id": vaga_id,
            "escola_id": escola_id
        }

        # 3. Realiza a requisição de reserva enviando o JSON e os Headers
        response = httpx.post(
            os.getenv("BACKEND_API") + "reserva-vagas/realizar-reserva",
            json=payload,
            headers=headers
        )

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

@mcp.tool(annotations=ToolAnnotations(
    readOnlyHint=True, destructiveHint=False,
    idempotentHint=True, openWorldHint=True))
def obter_lat_long(logradouro: str, numero: str, bairro: str, cidade: str) -> dict:
    """
    Envia as informações do endereço para obter a latitude e longitude.
    Retorna um dicionário com 'latitude' e 'longitude'.
    
    Caso o endereço não seja encontrado:
    1. Informar que não pode prosseguir com a reserva com este endereço e peça outro endereço.
    2. Caso não seja passado um novo endereço, diga que não é possível continuar com a reserva.
    """
    # 1. Correção da concatenação de strings usando f-string
    endereco = f"{logradouro}, {numero}, {bairro}, {cidade}"
    
    params = {
        "address": endereco,
        "key": os.getenv("GOOGLE_MAPS_API_KEY"),
        "region": "br",
    }

    headers = {
        "User-Agent": "MeuAppDeEscolas/1.0"
    }
    
    try:
        response = httpx.get(os.getenv("GOOGLE_MAPS_API_URL"), params=params, headers=headers)
        
        if response.status_code >= 300:
            return {
                "erro": True,
                "mensagem": "Erro ao consultar o serviço de geolocalização."
            }
        
        data = response.json()
        
        # 2. Correção da validação de endereço não encontrado no formato do Google
        if data.get("status") == "ZERO_RESULTS" or not data.get("results"):
            return {
                "erro": True,
                "status_api": data.get("status"),
                "mensagem": "Endereço não encontrado. Solicite ao usuário um endereço válido com logradouro e CEP."
            }

        # Se o status da API for qualquer coisa diferente de "OK" (ex: REQUEST_DENIED por causa do faturamento)
        if data.get("status") != "OK":
            return {
                "erro": True,
                "mensagem": f"Erro na API do Google: {data.get('status')}"
            }

        # 3. Correção do mapeamento das chaves de latitude e longitude ('geometry')
        location = data['results'][0]['geometry']['location']
        return {
            "latitude": location['lat'],
            "longitude": location['lng']
        }
        
    except httpx.RequestError:
        return {
            "erro": True,
            "mensagem": "O sistema está fora do ar no momento (falha de conexão)."
        }


async def processar_resposta_reserva(status_code: int, dados_resposta: dict):
    """
    Processa o retorno da API de reserva conforme as regras de negócio especificadas:
    - Status > 300: Sistema fora do ar.
    - Status 201 (ou sucesso com reserva ativa): Verificar status (PENDENTE ou APROVADO) ou cancelada.
    """
    # 1. Tratamento de Erro da API (Status acima de 300)
    if status_code > 300:
        return "O sistema está fora do ar no momento. Por favor, tente novamente mais tarde."

    # 2. Tratamento de Sucesso / Informações da Reserva
    # Supondo que 'dados_resposta' contenha os dados do candidato e o 'status' da reserva
    status_reserva = dados_resposta.get("status", "").upper()
    nome_candidato = dados_resposta.get("nome_candidato", "Candidato")

    mensagem_base = f"Informações da reserva para {nome_candidato}:\n- Status atual: {status_reserva}"

    # 3. Validação de Reserva Ativa vs Cancelada
    if status_reserva in ["PENDENTE", "APROVADO"]:
        mensagem_adicional = (
            "\n\n⚠️ Não é possível realizar uma nova reserva, "
            "pois a mesma encontra-se ativa."
        )
    elif status_reserva == "CANCELADA":
        mensagem_adicional = (
            "\n\nℹ️ A reserva anterior está cancelada. "
            "Uma nova reserva poderá ser feita."
        )
    else:
        mensagem_adicional = f"\n\nStatus da reserva: {status_reserva}"

    return mensagem_base + mensagem_adicional

if __name__ == "__main__":
    mcp.run(transport="stdio")
