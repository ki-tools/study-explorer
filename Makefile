.PHONY: devserve
devserve:
	./manage runserver


.PHONY: deploy_usa_production
deploy_usa_production:
	git push dokku-se-usa master


.PHONY: deploy_india_production
deploy_india_production:
	git push dokku-se-india master


.PHONY: deploy_africa_production
deploy_africa_production:
	git push dokku-se-africa master


.PHONY: deploy_usa_production_current_branch
deploy_usa_production_current_branch:
	git push dokku-se-usa `git rev-parse --abbrev-ref HEAD`:master


.PHONY: deploy_india_production_current_branch
deploy_india_production_current_branch:
	git push dokku-se-india `git rev-parse --abbrev-ref HEAD`:master


.PHONY: deploy_africa_production_current_branch
deploy_africa_production_current_branch:
	git push dokku-se-africa `git rev-parse --abbrev-ref HEAD`:master
