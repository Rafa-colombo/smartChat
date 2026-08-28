import requests

def consultar_pokemon(nome_ou_id: str) -> dict:
    """
    Consulta dados de um Pokémon utilizando a PokéAPI pública.
    """
    # Padronizar o nome para letras minúsculas 
    identificador = str(nome_ou_id).strip().lower()
    
    url = f"https://pokeapi.co/api/v2/pokemon/{identificador}"
    
    try:
        response = requests.get(url)
        if response.status_code == 200:
            dados = response.json()
            # Retornamos apenas os dados mais relevantes para economizar contexto
            return {
                "nome": dados.get("name"),
                "id": dados.get("id"),
                "altura": dados.get("height"),
                "peso": dados.get("weight"),
                "tipos": [t["type"]["name"] for t in dados.get("types", [])],
                "habilidades": [h["ability"]["name"] for h in dados.get("abilities", [])]
            }
        elif response.status_code == 404:
            return {"erro": f"Pokémon '{nome_ou_id}' não encontrado."}
        else:
            return {"erro": f"Erro ao consultar a PokéAPI. Status: {response.status_code}"}
    except Exception as e:
        return {"erro": f"Falha de conexão com a PokéAPI: {str(e)}"}