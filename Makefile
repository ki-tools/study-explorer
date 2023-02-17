
ifeq (deploy,$(firstword $(MAKECMDGOALS)))
  DEPLOY_ARGS := $(wordlist 2,$(words $(MAKECMDGOALS)),$(MAKECMDGOALS))
  $(eval $(DEPLOY_ARGS):;@:)
endif

ifeq (deploy_current_branch,$(firstword $(MAKECMDGOALS)))
  DEPLOY_ARGS := $(wordlist 2,$(words $(MAKECMDGOALS)),$(MAKECMDGOALS))
  $(eval $(DEPLOY_ARGS):;@:)
endif

.PHONY: venv
venv:
	python3.7 -m venv .venv


.PHONY: pip_install
pip_install:
	pip install --upgrade pip
	pip install -r requirements.txt
	pip install -r requirements-dev.txt


.PHONY: createsuperuser
createsuperuser:
	./manage.py createsuperuser


.PHONY: devserve
devserve:
	./manage.py runserver


.PHONY: test
test:
	./manage.py test --driver Firefox -v


.PHONY: devserve_heroku
devserve_heroku:
	heroku local


.PHONY: docs
docs:
	./manage.py collectstatic && cd ./docs && make html && cd ..


.PHONY: deploy
deploy:
	$(foreach var,$(DEPLOY_ARGS), git push -f se-$(var) master;)


.PHONY: deploy_current_branch
deploy_current_branch:
	$(foreach var,$(DEPLOY_ARGS), git push -f se-$(var) `git rev-parse --abbrev-ref HEAD`:master;)


.PHONY: migrate
migrate:
	./manage.py migrate
