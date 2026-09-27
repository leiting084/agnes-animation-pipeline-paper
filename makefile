# 论文编译
#   Windows 若无 make，直接跑下面两条命令之一：
#     pdflatex -synctex=1 -output-directory=build main.tex
#     pdflatex -synctex=1 -output-directory=build main_mtap.tex

TEX ?= pdflatex
BIB  ?= bibtex

.PHONY: all icme mtap clean watch

all: icme

# 会议版（两遍编译：第一遍记引用，第二遍填）
icme:
	mkdir -p bib figures build
	$(TEX) -synctex=1 -output-directory=build main.tex
	$(BIB) build/main.aux
	$(TEX) -synctex=1 -output-directory=build main.tex

# 期刊版 / 当前主攻
mtap:
	mkdir -p bib figures build
	$(TEX) -synctex=1 -output-directory=build main_mtap.tex
	$(BIB) build/main_mtap.aux
	$(TEX) -synctex=1 -output-directory=build main_mtap.tex

# 只导 PDF（用于快速预览，会跳过 bibliographystyle 差异）
quick:
	$(TEX) -synctex=1 -output-directory=build main_mtap.tex

watch:
	fswatch -o sections/*.tex main_mtap.tex preamble.tex | xargs -n1 -I{} $(MAKE) quick

clean:
	rm -rf build/*
