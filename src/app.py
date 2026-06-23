from src.boot import executar as boot
from src.menu import rodar
from src.exceptions import Recarregar


def iniciar():
    while True:
        try:
            boot()
            rodar()
            break
        except Recarregar:
            pass
