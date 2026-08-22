# Compila o artigo. Requer TeX Live (pdflatex + bibtex) ou latexmk.
# Sem TeX instalado localmente: subir para Overleaf funciona como está.

.PHONY: main clean

main: main.pdf

main.pdf: main.tex sections/*.tex references.bib
	latexmk -pdf -interaction=nonstopmode main.tex

clean:
	latexmk -C
	rm -rf build
