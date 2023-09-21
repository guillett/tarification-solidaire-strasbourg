install:
	@pip install git+https://github.com/openfisca/openfisca-france-local.git@strasbourg#egg=openfisca-France-Local
	@pip install "openfisca_core[web-api]"
	@pip install grist_api openfisca_survey_manager openpyxl odfpy python-dotenv pyjwt ezodf lxml

build:
	@cd front && npm ci && npm run build

run:
	@gunicorn run

dev:
	FLASK_DEBUG=1 FLASK_RUN_PORT=8000 FLASK_APP=run.py flask run

restart:
	@systemctl restart plugin_python

status:
	@systemctl status plugin_python

cd:
	su main -c "make install && make build" && sudo make restart && sudo make status
