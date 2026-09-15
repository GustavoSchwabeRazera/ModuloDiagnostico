from diagnostico.handoff_service import ServicoHandoff
from diagnostico.jornada_repository import RepositorioJornadas
if __name__ == "__main__":
    print({"handoffs_removidos": ServicoHandoff().limpar(), "jornadas_removidas": RepositorioJornadas().limpar_expiradas()})
