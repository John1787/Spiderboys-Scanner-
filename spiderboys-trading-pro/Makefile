.PHONY: install run test check clean

install:
	python -m pip install -r requirements.txt

run:
	streamlit run app.py

test:
	python -m pytest

check:
	python scripts/check_project.py
	python -m pytest

clean:
	find . -type d -name __pycache__ -prune -exec rm -rf {} +
	find . -type f -name '*.pyc' -delete
