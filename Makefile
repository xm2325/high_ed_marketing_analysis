.PHONY: demo test run

demo:
	python src/generate_demo_data.py

test:
	pytest -q

run:
	streamlit run dashboard/streamlit_app.py
