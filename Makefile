
ifeq (deploy,$(firstword $(MAKECMDGOALS)))
  DEPLOY_ARGS := $(wordlist 2,$(words $(MAKECMDGOALS)),$(MAKECMDGOALS))
  $(eval $(DEPLOY_ARGS):;@:)
endif

ifeq (deploy_current_branch,$(firstword $(MAKECMDGOALS)))
  DEPLOY_ARGS := $(wordlist 2,$(words $(MAKECMDGOALS)),$(MAKECMDGOALS))
  $(eval $(DEPLOY_ARGS):;@:)
endif

.PHONY: devserve
devserve:
	./manage.py runserver


.PHONY: test
test:
	./manage.py test --driver Firefox -v


.PHONY: devserve_heroku
devserve_heroku:
	heroku local


.PHONY: deploy
deploy:
	$(foreach var,$(DEPLOY_ARGS), git push -f se-$(var) master;)


.PHONY: deploy_current_branch
deploy_current_branch:
	$(foreach var,$(DEPLOY_ARGS), git push -f se-$(var) `git rev-parse --abbrev-ref HEAD`:master;)
