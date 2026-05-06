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

# Run frontend against local backend (uvicorn on port 8000)
streamlit_local:
	-@export API_URI=local_api_uri && streamlit run app.py

streamlit_cloud:
	-@export API_URI=cloud_api_uri && streamlit run app.py
