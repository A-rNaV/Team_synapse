.PHONY: setup run eval test

setup:
	uv python install 3.11
	uv venv --python 3.11 .venv
	uv pip install --python .venv -r requirements.txt

run:
	uv run --python .venv streamlit run app.py

eval:
	uv run --python .venv python eval.py $(if $(SUITE),--suite $(SUITE),)

test:
	uv run --python .venv pytest -q
