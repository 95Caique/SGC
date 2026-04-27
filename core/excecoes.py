class ExcecaoContraflow(Exception):
    """Excecao base para erros de dominio do ContraFlow."""


class ErroValidacao(ExcecaoContraflow):
    pass


class ErroPermissao(ExcecaoContraflow):
    pass


class ErroAcessoEmpresaNegado(ErroPermissao):
    pass


class ErroEmpresa(ExcecaoContraflow):
    pass


class ErroCliente(ExcecaoContraflow):
    pass


class ErroContrato(ExcecaoContraflow):
    pass


class ErroProposta(ExcecaoContraflow):
    pass


class ErroPropostaNaoEncontrada(ErroProposta):
    pass


class ErroPropostaStatusInvalido(ErroProposta):
    pass
