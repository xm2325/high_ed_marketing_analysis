install:
	python -m pip install -r requirements.txt

test:
	pytest -q

run:
	streamlit run dashboard/streamlit_app.py
