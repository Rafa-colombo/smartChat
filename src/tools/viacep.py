import requests

def consultar_cep(cep: str) -> dict:
    """
    Consulta dados de um CEP utilizando a API pública do ViaCEP.
    """
    # Remover qualquer caractere que não seja número (ex: hífens ou pontos)
    cep_limpo = "".join(filter(str.isdigit, cep))
    
    if len(cep_limpo) != 8:
        return {"erro": "CEP inválido. Deve conter exatamente 8 dígitos."}
    
    url = f"https://viacep.com.br/ws/{cep_limpo}/json/"
    
    try:
        response = requests.get(url)
        if response.status_code == 200:
            dados = response.json()
            if "erro" in dados:
                return {"erro": "CEP não encontrado na base de dados."}
            return dados
        else:
            return {"erro": f"Erro ao consultar o ViaCEP. Status: {response.status_code}"}
    except Exception as e:
        return {"erro": f"Falha de conexão com o ViaCEP: {str(e)}"}