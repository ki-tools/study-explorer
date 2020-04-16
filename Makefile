.PHONY: devserve
devserve:
	./manage runserver


.PHONY: deploy_usa_production
deploy_usa_production:
	git push dokku-se-usa master


.PHONY: deploy_usa_production_current_branch
deploy_usa_production_current_branch:
	git push dokku-se-usa `git rev-parse --abbrev-ref HEAD`:master
