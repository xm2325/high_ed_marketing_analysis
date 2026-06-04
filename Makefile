.PHONY: test run data check

data:
	python src/generate_demo_data.py

check:
	python -m py_compile dashboard/streamlit_app.py src/*.py

test: check
	pytest -q

run:
	streamlit run dashboard/streamlit_app.py
