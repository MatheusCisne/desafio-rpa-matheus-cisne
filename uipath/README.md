# RPA Challenge — Solução UiPath

Automação 100% em UiPath do [RPA Challenge](https://rpachallenge.com/): baixa o Excel do
próprio site, preenche as 10 rodadas do formulário e captura o resultado final. Não depende
da solução em Python — nenhum arquivo `.py`, script ou componente Python é chamado em nenhum
ponto.

## Problema resolvido

O RPA Challenge exibe um formulário de 7 campos que trocam de posição na tela a cada uma das
10 rodadas. A automação precisa: baixar o Excel de entrada, ler e validar os dados, clicar
Start, e preencher cada rodada localizando cada campo pelo **significado** (nunca pela posição
na tela), até a tela de conclusão aparecer.

## Programas e versões utilizados

- UiPath Studio **2026.0.180 STS** (Community Edition, licença ativada via Automation Cloud)
- Pacotes de atividades: `UiPath.Excel.Activities 3.6.1`, `UiPath.System.Activities 25.10.3`,
  `UiPath.UIAutomation.Activities 26.10.3`
- Compatibility: Windows · Language: VB (não Windows-Legacy)
- Microsoft Edge (navegador alvo da automação, via `channel msedge` equivalente do
  `NApplicationCard`)

## Decisões técnicas

### Por que um único card de navegador para tudo (decisão mais importante do projeto)

A primeira versão deste projeto seguia o roteiro mais óbvio: um arquivo `.xaml` por
responsabilidade (`OpenChallenge.xaml` abria o navegador e clicava Start, `FillRound.xaml` era
invocado 10 vezes — uma por rodada —, `CaptureResult.xaml` validava a tela final). Cada um
desses arquivos abria seu próprio `Use Application/Browser` (`NApplicationCard`), reaproveitando
a mesma janela do navegador (mesmo título, sem navegação visível, sem popup de "traduzir
página").

Isso **parecia** funcionar — os campos eram preenchidos corretamente, rodada após rodada — mas
a tela de conclusão (`.congratulations`) nunca aparecia. Investigando a fundo (ver seção
"Dificuldades" abaixo), descobri que o botão inferior esquerdo do site, que deveria mudar de
"START" para "Round 1", "Round 2"... conforme as rodadas oficiais avançam, **nunca saía de
"START"**. Ou seja: mesmo com os campos sendo preenchidos e enviados com sucesso, todas as
"10 rodadas" estavam acontecendo no **modo de teste livre** que o site permite antes do Start
(“you may submit the form as many times as you wish without receiving penalties”) — nunca no
desafio cronometrado de verdade. Reabrir o card do navegador entre arquivos `.xaml`, mesmo sem
nenhuma navegação visível, estava resetando o estado interno do componente Angular da SPA.

A correção foi consolidar **todo** o fluxo — abrir o navegador, clicar Start, preencher as
10 rodadas, validar a tela final e capturar a evidência — dentro de um **único**
`NApplicationCard`, nunca fechado/reaberto no meio (`RunChallenge.xaml`). Depois dessa mudança,
o botão passou a mostrar corretamente "Round 2", "Round 3"... confirmando que o desafio real
estava progredindo, e a tela de conclusão passou a aparecer normalmente.

### Por que `WebClient.DownloadFile` em vez de clicar no link "Download Excel"

O link "Download Excel" do site aponta para uma URL pública e fixa
(`https://rpachallenge.com/assets/downloadFiles/challenge.xlsx`). Clicar nesse link no
Microsoft Edge não dispara um download de arquivo: o Edge intercepta a navegação para `.xlsx` e
abre uma prévia "Excel Online" (`view.officeapps.live.com`) em outra aba, sem nunca salvar o
arquivo em disco — comportamento nativo do Edge, confirmado durante a depuração. Por isso o
arquivo é obtido com uma chamada HTTP direta (`System.Net.WebClient`, atividade `Invoke Method`)
para essa mesma URL pública — que nem precisa de navegador aberto, já que é só uma requisição
HTTP simples.

### Por que `UiPath.System.Activities`/`UiPath.UIAutomation.Activities` (sem `.Runtime`)

O projeto originalmente referenciava `UiPath.System.Activities.Runtime` e
`UiPath.UIAutomation.Activities.Runtime` como dependências diretas — pacotes que normalmente são
dependência **transitiva** interna (puxados automaticamente pelos pacotes de design), não uma
referência direta de projeto. Descartei essa hipótese como causa de um travamento de
empacotamento (não era — ver "Dificuldades"), mas mantive a correção por ser tecnicamente mais
correta: o projeto de teste vazio criado durante a depuração usava `UiPath.System.Activities`
(sem `.Runtime`), então padronizei por aqui.

## Como os campos dinâmicos foram identificados

Igual à solução Python: o site roda Angular em modo desenvolvimento, o que expõe o atributo
`ng-reflect-name` em cada `<input>` do formulário — esse valor não muda entre rodadas, mesmo com
o layout embaralhando a posição dos campos. No UiPath, isso vira um seletor de atributo dentro
do `FullSelectorArgument`:

```
<html title='*RPA Challenge*' /><webctrl tag='INPUT' ng-reflect-name='labelFirstName' />
```

O botão Submit (`<input type="submit">`) fica fora do componente que se repete — nunca muda de
posição nem de atributos — por isso usa um seletor simples por tag/tipo, sem precisar de
`ng-reflect-name`. A tela final é detectada via `Check App State` esperando aparecer um
`<div>` cuja classe **contém** `congratulations` (`class='*congratulations*'`, com wildcard —
a classe real do elemento é `"congratulations col s8 m8 l8"`, não só `"congratulations"`).

## Instalação

1. Crie uma conta gratuita em [Automation Cloud](https://cloud.uipath.com/) (se ainda não tiver).
2. Baixe e instale o **UiPath Studio Community** pelo Resource Center da sua conta.
3. Abra o Studio e faça login com a mesma conta — uma licença Community é ativada
   automaticamente.
4. Abra o projeto: **Abrir → Abrir um Projeto Local** → selecione a pasta `uipath/` (o arquivo
   `project.json`).

## Como executar

**Pelo Studio (recomendado para ver rodando ao vivo):** com o projeto aberto, clique no botão
de **Executar** (▶) na barra de ferramentas, ou pressione `F5`.

**Por linha de comando (após publicar um pacote):** dentro do Studio, **Publicar → Personalizado**
e escolha uma pasta local (ex.: `uipath/.output`) como destino — **não publique direto no
Orchestrator/nuvem** (ver "Dificuldades" abaixo sobre por que isso é instável). Depois, rode o
pacote gerado:

```bash
UiRobot.exe execute --file "caminho\para\RPAChallengeUiPath.X.Y.Z.nupkg"
```

Não é necessário informar caminho algum do Excel: o robô baixa o arquivo sozinho, direto do
site, e salva em `uipath/data/challenge.xlsx` (caminho relativo ao projeto).

## O que o robô faz

1. Baixa `challenge.xlsx` direto da URL pública do desafio.
2. Invoca `ReadExcelData.xaml`: lê a planilha, remove espaços dos cabeçalhos, valida que as 7
   colunas obrigatórias existem (encerra com erro claro se faltar alguma) e descarta linhas
   totalmente vazias.
3. Invoca `RunChallenge.xaml`: abre o navegador, clica Start, e — dentro do mesmo card — percorre
   as 10 linhas do Excel preenchendo os 7 campos de cada rodada pelo `ng-reflect-name` e enviando
   o formulário.
4. Na última rodada, espera a tela `.congratulations` aparecer e salva um screenshot em
   `evidencias/resultado-uipath.png` (na raiz do repositório).

## Erros e logs

Cada rodada é envolvida num `Try Catch`: se uma rodada falhar, o erro é logado com o número
exato da rodada (`Falha na rodada N/10: <mensagem>`) antes de ser repropagado — comportamento
fail-fast, sem retry automático, igual à solução Python. Erros de validação do Excel (colunas
ausentes) e erros de download levantam exceções com mensagem clara antes de qualquer tentativa
de abrir o navegador. O log de execução do Robot fica em
`%LOCALAPPDATA%\UiPath\Logs\<data>_Execution.log` — uma limitação conhecida é que esse log **não**
fica em um caminho relativo ao projeto (diferente da solução Python, que grava seu próprio
arquivo de log dentro do projeto); é o comportamento padrão da plataforma UiPath, que centraliza
logs de execução por usuário/máquina.

## Dificuldades encontradas e como foram resolvidas

- **Publicar travava por vários minutos, sem erro.** Descartei sistematicamente: concorrência
  com o Studio aberto (fechei o Studio, mesmo travamento), Windows Defender bloqueando (adicionei
  exclusões, mesmo travamento), dependências erradas no `project.json` (corrigi, mesmo
  travamento), e só depois de deixar rodar por tempo suficiente descobri que "Publicar" também
  tenta **enviar o pacote para o Orchestrator/nuvem** — e esse envio falhava com
  `SocketException (10054): conexão resetada pelo host remoto` (muito provavelmente relacionado
  à tela do computador bloquear/suspender a rede no meio do envio). A correção: publicar sempre
  com destino **Personalizado** (pasta local), evitando esse envio de rede por completo.
- **Pacote publicado crescendo exponencialmente (chegou a ~57 GB numa das tentativas).**
  Publicar dentro da própria pasta do projeto (`uipath/.output`) faz o publicador incluir o
  `.nupkg` da versão anterior dentro do novo pacote, que inclui o da versão anterior a essa, e
  assim por diante — crescimento exponencial a cada republicação. Tentei configurar
  `ignoredFiles` no `project.json` para excluir a pasta `.output`, mas o Studio reverte essa
  configuração sozinho ao salvar. Mitigação: sempre limpar `uipath/.output` antes de uma leva de
  testes, e nunca deixar acumular várias versões publicadas.
- **A tela de conclusão nunca aparecia, mesmo com todos os campos preenchidos corretamente.**
  Essa foi a investigação mais longa do projeto (ver "Por que um único card" acima) — a causa
  raiz era a SPA perdendo o estado de "desafio iniciado" toda vez que um novo `.xaml` reabria o
  card do navegador, mesmo sem navegação visível. Resolvido consolidando todo o fluxo em um
  único card contínuo.
- **`WebClient.DownloadFile` com erro de sintaxe de caminho.** Uma versão intermediária montava
  o caminho de destino incorretamente (misturando a pasta do pacote instalado com a URL de
  download, que ainda vinha com aspas literais coladas). Corrigido reescrevendo a chamada com
  variáveis separadas e limpas para URL de origem e caminho de destino.
- **Elemento "fora dos limites da tela" ao clicar Start.** A janela do navegador controlado pelo
  UiPath abria não-maximizada, às vezes com posição salva de uma sessão anterior que não cabia
  mais na tela. Corrigido configurando a propriedade **"Redimensionar janela" = Maximized** no
  card do navegador.

## Limitações conhecidas

- Depende do site continuar expondo `ng-reflect-name` (modo desenvolvimento do Angular) — mesma
  limitação documentada na solução Python.
- O log de execução do Robot fica no diretório padrão do UiPath (por usuário/máquina), não dentro
  da pasta do projeto.
- Publicar direto no Orchestrator/nuvem se mostrou instável neste ambiente (falha de rede durante
  o upload); o fluxo documentado aqui usa publicação local, que é confiável e não depende de
  conexão de rede sustentada por vários minutos.
