import asyncio # Biblioteca para lidar com operações simultâneas (permite atender vários clientes ao mesmo tempo sem travar)
import websockets # Biblioteca fundamental que cria e gerencia o servidor e as conexões WebSocket
import json # Biblioteca para codificar e decodificar os pacotes de dados (transforma texto em Dicionário e vice-versa)
import random # Biblioteca para trabalhar com valores randomicos

# O dicionário agora vai guardar uma "ficha" de cada dispositivo, funcionará como nossa "agenda" principal de conexões ativas na memória
clientes_conectados = {}

def gerar_mac_aleatorio():
    # Gera 6 números aleatórios entre 0 e 255 formatados em hexadecimal com 2 dígitos
    mac_bytes = [random.randint(0, 255) for _ in range(6)]
    return ":".join([f"{b:02x}" for b in mac_bytes])

async def manipulador_conexao(websocket): # Função principal que é executada individualmente para CADA cliente que se conecta
    # ==========================================
    # 1. Fase de Autenticação / Login
    # ==========================================
    try: # Inicia um bloco de tentativa: se algo der errado (ex: cliente desconectar do nada), o código pula para o 'except'
        primeira_mensagem = await websocket.recv() # Pausa a execução APENAS para este cliente e aguarda ele enviar a 1ª mensagem
        dados = json.loads(primeira_mensagem) # Converte o pacote recebido (que é um texto puro) em um Dicionário Python
        
        if dados.get("Token", {}) == "GHXXc7VvzJkapZ5x7p6eeEDUoPvOrwY62xX5wKbEq5Oy7i1LxICucyUFqQ93YVHh": # Verifica de forma segura se o Token enviado pelo cliente é válido
            if dados.get("Sistema", {}) == "LightFy": # Verifica de forma segura se o cliente é realmente do sistema LightFy
                if dados.get("Comando", {}) == "Conexao": # Verifica de forma segura se a intenção do cliente é fazer login/registrar
                    id_cliente_Nome = dados.get("ID",{}).get("Nome", "Sem nome definido") # Extrai o nome; se falhar ou não existir, usa o valor padrão
                    id_cliente_Identificador = dados.get("ID",{}).get("Identificador", gerar_mac_aleatorio()) # Extrai o MAC/UUID único, se falhar ou não existir, gera um valor MAC aleatório válido
                    
                    # UPGRADE AQUI: Em vez de salvar só o websocket, salvamos um sub-dicionário
                    clientes_conectados[id_cliente_Identificador] = { # Cria uma nova "gaveta" na agenda usando o Identificador/MAC/UUID único como chave
                        "ws": websocket, # Salva o "cabo" da conexão física para podermos repassar mensagens para ele depois
                        "nome": id_cliente_Nome # Salva o nome amigável para exibirmos em logs e relatórios
                    }
                    
                    if id_cliente_Nome != "Sem nome definido": # Checa se o dispositivo enviou um nome válido
                        print(f"[{id_cliente_Nome}] conectado com sucesso na central!") # Imprime o nome de quem entrou
                    else:
                        print(f"[{id_cliente_Identificador}] conectado com sucesso na central!") # Se não tem nome, imprime o UUID bruto
                else:
                    print("Dispositivo não se identificou. Fechando conexão...") # Se a 1ª mensagem não for de Conexão, é uma anomalia
                    return # O 'return' mata a função imediatamente, forçando a conexão deste cliente intruso/com erro a ser fechada
            else:
                print("Sistema inválido. Fechando conexão...") # Se o sistema não bater, é uma tentativa de invasão
                return # O 'return' mata a função imediatamente, forçando a conexão deste cliente intruso/com erro a ser fechada
        else:
            print("Token inválido. Fechando conexão...") # Se o Token não bater, é uma tentativa de invasão
            return # O 'return' mata a função imediatamente, forçando a conexão deste cliente intruso/com erro a ser fechada

    except Exception as e: # Captura qualquer erro que tenha ocorrido no bloco 'try' acima (ex: JSON mal formado)
        print(f"Erro durante o handshake de identificação.\nErro: {e}") # Registra no log <=== Aqui futuramente posso guardar esses erros em um banco de dados
        return # Interrompe a função e derruba a conexão

    # ==========================================
    # 2. Fase de Roteamento (A Mesa Telefônica)
    # ==========================================
    try: # Inicia o bloco responsável por manter a conexão viva e rotear as conversas
        async for mensagem in websocket: # Loop infinito: o Python fica escutando TUDO o que chegar por este cabo de conexão
            dados_msg = json.loads(mensagem) # Transforma a nova mensagem recebida em Dicionário
            
            destino = dados_msg.get("Destino") # Lê a "etiqueta" Destino para saber a quem a mensagem pertence (procura pelo Identificador/UUID)
            comando = dados_msg.get("Comando") # Capturamos qual é a intenção do JSON (ex: "Acionar", "Status")
            
            # =======================================================
            # INTERCEPTAÇÃO DE DADOS (Preparação para o Banco de Dados)
            # =======================================================
            if comando == "Status": # Verifica se a mensagem é um relatório de métricas vindo do ESP
                # Entramos no bloco "Dados" de forma segura
                bloco_dados = dados_msg.get("Dados", {}) # Extrai as informações de hardware do JSON
                
                # Pegamos o valor exato do atuador
                status_atuador = bloco_dados.get("Atuador", "Desconhecido") # Lê especificamente o estado da lâmpada/relé
                
                # FUTURO: É exatamente aqui que você vai colocar a sua query SQL 
                # (ex: cursor.execute("INSERT INTO historico ..."))
                # print(f" >>> [MEMÓRIA INTERNA] Salvando status: O {id_cliente_Nome} relatou que está [{status_atuador}]") # Log provisório
            # =======================================================

            if destino in clientes_conectados: # Verifica se o UUID de destino existe dentro da nossa "agenda"(websocket) 
                ws_destino = clientes_conectados[destino]["ws"] # Resgata o "cabo" físico do destinatário salvo na Fase 1
                nome_destino = clientes_conectados[destino]["nome"] # Resgata o nome amigável do destinatário
                
                await ws_destino.send(mensagem) # Despacha o pacote JSON original intocado diretamente para o destinatário
                print(f"Comando roteado: de [{id_cliente_Nome}] para [{nome_destino}]") # Registra no log que a entrega foi um sucesso
            else: # Caso o destinatário não seja encontrado na agenda...
                print(f"Falha no roteamento: o destino [{destino}] está offline.") # Avisa que a mensagem foi descartada

    except Exception as e: # Se houver perda de conexão (Wi-Fi caiu, fechou a aba do navegador) durante o loop
        print(f"Erro de comunicação em [{id_cliente_Nome}]:\nErro: {e}") # Loga qual foi o dispositivo que sofreu a queda
    finally: # Bloco crucial: o código AQUI sempre será executado ao final, tenha dado erro ou não
        if id_cliente_Identificador in clientes_conectados: # Verifica se a ficha do cliente ainda existe na agenda
            del clientes_conectados[id_cliente_Identificador] # Deleta a "gaveta" do cliente, liberando espaço na memória RAM
            print(f"[{id_cliente_Nome}] removido da central.") # Registra oficialmente a desconexão

async def main(): # Função que empacota o servidor e gerencia o ciclo de vida do programa principal
    print("Servidor WebSocket Python iniciado na porta 8765...") # Aviso visual de partida
    
    # Cria o servidor na interface global (0.0.0.0 = aceita de qualquer IP da rede) apontando para a porta 8765
    async with websockets.serve(manipulador_conexao, "0.0.0.0", 8765):
        await asyncio.Future() # Essa linha cria uma promessa infinita, travando o código para que o script nunca termine de rodar

if __name__ == "__main__": # Segurança extra: garante que o servidor só suba se o arquivo for executado diretamente
    asyncio.run(main()) # Dá a "ignição" no motor assíncrono do Python para iniciar a função main()
    
# Em todas as vez que o Servidor for ligado/reiniciado, execute esse comando no terminal no caminho da pasta do projeto antes de inicar o script: 
# source venv/bin/activate