# ============================================================
#   Mapa do Trabalho Brasileiro — alvos de conveniência
#
#   Sem make? Use o fallback equivalente:
#     python3 scripts/run_all.py [pipeline|test]
# ============================================================
.PHONY: setup refresh test

# Interpretador Python: usa o venv do projeto quando existir
# (criado por `make setup`), senão o python3 do PATH.
# Sobrescreva quando precisar:  make PYTHON=/c/Python311/python.exe test
PYTHON ?= $(shell if [ -x .venv/bin/python ]; then echo .venv/bin/python; \
  elif [ -x .venv/Scripts/python.exe ]; then echo .venv/Scripts/python.exe; \
  else echo python3; fi)

ifeq ($(OS),Windows_NT)
  VENV_PY = .venv/Scripts/python.exe
else
  VENV_PY = .venv/bin/python
endif

setup:
	python3 -m venv .venv
	$(VENV_PY) -m pip install -r requirements.txt -r requirements-dev.txt

refresh:
	$(PYTHON) scripts/run_all.py pipeline

test:
	$(PYTHON) scripts/run_all.py test