install:
	@pip install git+https://github.com/openfisca/openfisca-france-local.git@strasbourg#egg=openfisca-France-Local
	@pip install "openfisca_core[web-api]"
	@pip install grist_api openfisca_survey_manager openpyxl python-dotenv
build:
	@cd front && npm run build
