# Assessment in application security development

## Version Python
3.12.10

## Dependencies to install
flask
flask-cors
PyJWT
python-dotenv
requirements.txt
environment virtual

### Steps for create project

#### Create environment virtual
python -m venv "environment name"

#### Install dependecies
pip install flask
pip install flask-cors
pip install PyJWT
pip install python-dotenv

#### Generate file "requirements.txt"
pip freeze > requirements.txt

#### Activate environment
Windows PowerShell: .\"environment name"\Scripts\Activate
Bash Terminal: source "environment name"\Scripts\Activate

#### Deactivate environment
deactivate