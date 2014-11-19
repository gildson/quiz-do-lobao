from enum import Enum


class QuestaoStatus(Enum):
    nao_revisada = 0
    liberada = 1
    bloqueada = 2


# quando é feito o envio de uma resposta
class RetornoResposta(Enum):
    error = 0
    continua = 1
    fim_partida = 2


class QuestaoAlternativaCorreta(Enum):
    alternativa_a = 'a'
    alternativa_b = 'b'
    alternativa_c = 'c'
    alternativa_d = 'd'
    alternativa_e = 'e'


class PartidasRespostaResultado(Enum):
    errou = 0
    acertou = 1
    pulou = 2
