# Uso de Inteligência Artificial

## Qual ferramenta de IA foi utilizada

Claude

<!-- Ex.: Claude Code (Anthropic), versão X, dentro do terminal/IDE. -->

## Em quais partes ela ajudou

Implementação do código, testes e revisão. Além de solucionar os bugs que ocorreram enquanto eu testava.

<!-- Ex.: estruturação inicial do projeto, revisão de código, escrita de testes, redação do
README, investigação de um erro específico de ambiente. Seja específico sobre o que foi
gerado com apoio da IA e o que foi decisão/verificação minha. -->

## De 3 a 5 prompts importantes que utilizei

<!-- Cole aqui os prompts (ou um resumo fiel deles) que mais moldaram o resultado — não
precisa ser a conversa inteira, só os pontos de decisão. -->

1.Utilize um agente para testar as validações do print acima(Print sobre o que foi pedido) ,um agente para revisar o código e outro agente para testes unitários.
2.O código em Python vai muito rápido e o do UiPath demora bem mais... Qual o porquê disso e dá pra otimizar?
3.E quando o Claude estava me ajudando para montar o código em Uipath ele estava testando uma solução e múltiplas janelas do Edge estavam sendo abertas e nenhuma chegava no Round 10. Pra ser sincero, nem o botão start estava sendo clicado. Percebi isso e notifiquei ao Claude que corrigiu rápido a causa com o prompt: Pelo que eu percebi aqui, você estava abrindo múltiplas páginas do Edge em vez de dar submit e ir pro próximo round. A partir disso fomos chegando ao erro do código e foi uma adaptação que eu explico a baixo.

## O que precisei corrigir, adaptar ou descartar

Correções: Bug de caminho no download do UiPath (aspas coladas, path errado) que foi pego por um log de execução real e depois corrigido.

fill_field preenchia células vazias com o texto literal "nan"/"None" em vez de vazio que foi pego por um teste automatizado e corrigido.

Adaptação: A arquitetura do UiPath precisou ser totalmente reestruturada (de vários arquivos com cards separados pra um único card contínuo) porque na solução UIpath é necessário um card continuo, pois cada vez que um card novo do navagador abria o estado interno do componente Angular da spa reiniciava e isso impedia de de mostrar os rounds posteriores. E com isso ficava preso na tela de START. Em resumo, os campos eram preenchidos mas apenas no modo de teste livre e nunca no desafio real do site.

Descarte: Hipóteses para um bug que estava acontecendo com o Chromium(Antivirus e driver corrompido) na minha máquina e que depois se corrigiu após alguns dias. 

<!-- Ex.: alguma sugestão que testei e não fazia sentido para o projeto, algo que precisei
ajustar depois de entender melhor, alguma decisão da IA que questionei. -->

## Principal aprendizado obtido com esse apoio

Uma poderosa ferramenta, mas que tem que saber ser usada. Como por exemplo escrever prompts específicos para o que está sendo necessitado e tirar um aprendizado disso utilizando-a para aprender também, não só copiar. No geral, é essencial na vida dos devs atuais e uma ferramenta que não pode se deixar de lado, pois otimiza projetos e acelera a escala.
