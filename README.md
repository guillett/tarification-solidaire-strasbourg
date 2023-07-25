

```bash
pyenv virtualenv 3.9.16 stras
pyenv activate stras
pip install jupyter pandas

pip install git+https://github.com/openfisca/openfisca-france-local.git@strasbourg#egg=openfisca-France-Local
pip install "openfisca_core[web-api]"
pip install grist_api openfisca_survey_manager openpyxl python-dotenv
```

