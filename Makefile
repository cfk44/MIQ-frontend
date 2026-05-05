#======================#
# Install, clean, test #
#======================#

install_requirements:
	@pip install -r requirements.txt

install:
	@pip install . -U

clean:
	@rm -f */version.txt
	@rm -f .coverage
	@rm -fr */__pycache__ */*.pyc __pycache__
	@rm -fr build dist
	@rm -fr proj-*.dist-info
	@rm -fr proj.egg-info

test_structure:
	@bash tests/test_structure.sh

#======================#
#       Streamlit      #
#======================#

streamlit: streamlit_local

streamlit_local:
	-@BASE_URI=http://127.0.0.1:8000 streamlit run app.py
# CHANGED FROM API_URI
streamlit_local_docker:
	-@API_URI=local_docker_uri streamlit run app.py

streamlit_cloud:
	-@API_URI=cloud_api_uri streamlit run app.py
