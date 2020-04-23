.PHONY: devserve
devserve:
	./manage runserver


.PHONY: devserve_heroku
devserve_heroku:
	heroku local


.PHONY: deploy_staging
deploy_staging:
	git push se-staging master


.PHONY: deploy_usa
deploy_usa:
	git push se-usa master


.PHONY: deploy_india
deploy_india:
	git push se-india master


.PHONY: deploy_africa
deploy_africa:
	git push se-africa master


.PHONY: deploy_staging_current_branch
deploy_staging_current_branch:
	git push se-staging `git rev-parse --abbrev-ref HEAD`:master


.PHONY: deploy_usa_current_branch
deploy_usa_current_branch:
	git push se-usa `git rev-parse --abbrev-ref HEAD`:master


.PHONY: deploy_india_current_branch
deploy_india_current_branch:
	git push se-india `git rev-parse --abbrev-ref HEAD`:master


.PHONY: deploy_africa_current_branch
deploy_africa_current_branch:
	git push se-africa `git rev-parse --abbrev-ref HEAD`:master
