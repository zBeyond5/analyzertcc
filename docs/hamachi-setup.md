# Hospedagem privada no Windows 11

O aplicativo executa no computador anfitrião. Clientes autorizados enviam e recebem arquivos pela rede Hamachi. A aplicação não tem contas próprias: quem ingressar na rede autorizada poderá abrir a interface. O administrador deve admitir e remover os membros da rede e avaliar a autorização ética antes de usar dados reais.

## Teste local

Na raiz do projeto, com o ambiente instalado conforme o README:

```powershell
.\scripts\start_local.ps1
```

Abrir `http://127.0.0.1:8501`. Este início escuta exclusivamente no computador local e não disponibiliza o serviço na LAN. Encerrar com Ctrl+C no PowerShell.

## Preparação Hamachi

1. Instalar e conectar o Hamachi no servidor e em cada cliente autorizado. O software e a administração da rede são externos a este aplicativo.
2. Conferir o IPv4 e o nome exato da interface do anfitrião com `Get-NetIPAddress -AddressFamily IPv4`. Os scripts aceitam IPv4 Hamachi na faixa 25.0.0.0/8; não usar IP físico, público, `Any` ou uma faixa ampla de peers.
3. Substituir os IPs dos exemplos pelos endereços reais. No **PowerShell como administrador**, criar a regra exclusiva do aplicativo:

```powershell
.\scripts\configure_firewall.ps1 -HamachiAddress '25.1.2.3' -AllowedPeerAddresses @('25.1.2.4','25.1.2.5') -HamachiInterfaceAlias 'Hamachi'
```

A regra `TCC Analyzer Hamachi 8501` permite somente TCP/8501, endereço/interface Hamachi e a lista explícita dos clientes. O configurador altera apenas a regra com esse nome e recusa duplicatas. Para examinar a proposta sem gravar regras, usar `-CheckOnly`; esse modo **não comprova** que a interface ou a política do computador já estão configuradas. `-WhatIf` também não aplica alterações.

4. Em PowerShell normal, iniciar:

```powershell
.\scripts\start_hamachi.ps1 -HamachiAddress '25.1.2.3' -AllowedPeerAddresses @('25.1.2.4','25.1.2.5') -HamachiInterfaceAlias 'Hamachi'
```

O início verifica o endereço atribuído, a regra restritiva e outras regras de entrada que possam liberar a porta/processo de forma ampla. Falhas interrompem o início; nenhuma regra alheia é removida automaticamente. `-CheckOnly` neste launcher realiza as verificações e não inicia o servidor.

5. Nos clientes autorizados, abrir `http://25.1.2.3:8501`. Encerrar o serviço no servidor com Ctrl+C.

O parâmetro `-AllowAnyBind` é uma alternativa explícita para um ambiente que exija `0.0.0.0`. Ele mantém todas as verificações restritivas e só deve ser utilizado após testar a limitação efetiva da rede. Preferir sempre o bind ao IP Hamachi. Não configurar port forwarding, túnel público ou publicação em nuvem. Manter Firewall do Windows, CORS e proteção XSRF habilitados.

## Conferência obrigatória antes de dados reais

- Com um cliente Windows Hamachi autorizado, testar upload, análise e download ZIP. Dois navegadores com bases diferentes devem receber somente seus próprios arquivos.
- Conferir o listener no anfitrião: `Get-NetTCPConnection -LocalPort 8501 -State Listen`.
- Conferir a regra e seus filtros com `Get-NetFirewallRule -DisplayName 'TCC Analyzer Hamachi 8501'` e `Get-NetFirewallAddressFilter`, `Get-NetFirewallPortFilter`, `Get-NetFirewallInterfaceFilter`.
- De outro computador fora da VPN, testar a porta 8501 nos endereços LAN e público do anfitrião; o acesso deve falhar. Um teste negativo feito somente no servidor não prova essa restrição.
- Avaliar as propriedades de transporte e a configuração do Hamachi com o administrador. Não atribuir garantia de confidencialidade apenas à instalação da VPN.

**Estado deste aceite:** scripts e verificações locais automatizadas disponíveis; o teste remoto Hamachi, a política efetiva do Firewall e o acesso negativo externo precisam de evidência no ambiente de implantação. Nenhuma regra do sistema foi alterada durante a autoria dos scripts.

## Operação e diagnóstico

Estado de sessão é temporário. Recarregar a página, perder o WebSocket ou reiniciar o servidor pode exigir novo envio e análise. Não desabilitar CORS/XSRF para resolver reconexão; conferir conexão Hamachi, endereço, firewall e logs técnicos sem dados da pesquisa.

Trabalhos e uploads ficam em `runtime/`, fora de diretórios públicos; a retenção é configurada no aplicativo e o descarte não depende apenas de fechar a aba. Backups, antivírus, memória do processo e logs do Windows têm gestão separada. Downloads já salvos no cliente são cópias locais e não podem ser revogados pelo servidor.

Para operação sem internet, preparar previamente as dependências fixadas e os wheels Python correspondentes ao Windows/Python 3.12. A aplicação não precisa de serviços de IA remotos, Epi Info instalado ou conexão pública durante o processamento.
