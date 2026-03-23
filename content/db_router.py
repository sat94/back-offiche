class ArticleRouter:
    route_models = {'pgarticle', 'articleview'}

    def db_for_read(self, model, **hints):
        if model._meta.model_name in self.route_models:
            return 'articles'
        return None

    def db_for_write(self, model, **hints):
        if model._meta.model_name in self.route_models:
            return 'articles'
        return None

    def allow_relation(self, obj1, obj2, **hints):
        return None

    def allow_migrate(self, db, app_label, model_name=None, **hints):
        if model_name in self.route_models:
            return False
        return None
