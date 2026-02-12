AUTOREAP v2 (VERSÃO APAPS OFFLINE LINUX)
========================================

Esta é uma versão dedicada e offline do AutoREAP configurada especificamente para o perfil APAPS.
Não requer ativação online nem verificação de licença.

1. BUILD (GERAR O EXECUTÁVEL)
-----------------------------
Abra o terminal na pasta do projeto e execute:
   bash build_linux.sh

Isso criará uma pasta chamada "dist/AutoREAPv2_Linux" contendo o executável.

2. PREPARAR O PACOTE PARA O CLIENTE
-----------------------------------
Dentro da pasta "dist/AutoREAPv2_Linux" (onde está o executável), você deve copiar os seguintes arquivos que estão na raiz do projeto:

   - install.sh
   - AutoREAP.desktop

3. DISTRIBUIÇÃO
---------------
Compacte a pasta "AutoREAPv2_Linux" (agora contendo o executável + install.sh + .desktop) em um arquivo .zip ou .tar.gz e envie para o cliente.

4. INSTRUÇÕES PARA O CLIENTE (USUÁRIO FINAL)
--------------------------------------------
Diga ao cliente para:
   1. Baixar e extrair a pasta.
   2. Abrir a pasta extraída.
   3. Clicar com o botão direito no arquivo "install.sh" -> Propriedades -> Permissões -> Permitir executar como programa (se necessário).
   4. Executar o arquivo "install.sh" (ou abrir terminal na pasta e rodar `./install.sh`).

   O programa será instalado e aparecerá no Menu de Aplicativos dele.
