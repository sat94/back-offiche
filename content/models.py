from django.db import models
from back_office.mongodb import get_mongo_database
from datetime import datetime
from bson import ObjectId


class PgArticle(models.Model):
    titre = models.CharField(max_length=255)
    sous_titre = models.CharField(max_length=500, null=True, blank=True)
    petit_description = models.TextField(null=True, blank=True)
    contenu = models.TextField(null=True, blank=True)
    photo = models.CharField(max_length=500, null=True, blank=True)
    theme = models.CharField(max_length=100, null=True, blank=True)
    date_publication = models.DateTimeField(null=True, blank=True)
    access_count = models.IntegerField(null=True, blank=True)
    reading_time = models.IntegerField(null=True, blank=True)
    mis_en_avant = models.BooleanField(null=True, blank=True)
    auteur_full_name = models.CharField(max_length=255, null=True, blank=True)
    slug = models.CharField(max_length=255)
    created_at = models.DateTimeField(null=True, blank=True)
    updated_at = models.DateTimeField(null=True, blank=True)
    word_count = models.IntegerField(null=True, blank=True)
    meta_description = models.CharField(max_length=160, null=True, blank=True)
    canonical_url = models.CharField(max_length=500, null=True, blank=True)
    content_type = models.CharField(max_length=50, null=True, blank=True)
    schema_markup = models.JSONField(null=True, blank=True)
    og_title = models.CharField(max_length=95, null=True, blank=True)
    og_description = models.CharField(max_length=160, null=True, blank=True)
    focus_keyword = models.CharField(max_length=100, null=True, blank=True)
    last_updated_for_seo = models.DateTimeField(null=True, blank=True)
    faq_suggestions = models.JSONField(null=True, blank=True)
    photo_description = models.TextField(null=True, blank=True)
    photo_highlight = models.CharField(max_length=500, null=True, blank=True)
    vignette = models.CharField(max_length=500, null=True, blank=True)
    youtube_video_id = models.CharField(max_length=255, null=True, blank=True)
    youtube_video_title = models.CharField(max_length=500, null=True, blank=True)
    trending_keywords = models.JSONField(null=True, blank=True)
    related_questions = models.JSONField(null=True, blank=True)
    youtube_video_url = models.CharField(max_length=500, null=True, blank=True)
    youtube_video_embed = models.CharField(max_length=500, null=True, blank=True)
    youtube_video_thumbnail = models.CharField(max_length=500, null=True, blank=True)
    photos = models.JSONField(null=True, blank=True)
    tags_list = models.JSONField(null=True, blank=True)
    keywords = models.JSONField(null=True, blank=True)

    class Meta:
        db_table = 'articles'
        managed = False

    def __str__(self):
        return self.titre


class ArticleView(models.Model):
    article = models.ForeignKey(PgArticle, on_delete=models.CASCADE, db_column='article_id')
    ip_address = models.CharField(max_length=45)
    viewed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'article_views'
        managed = False


class MongoBaseModel:
    collection_name = None
    db_key = 'api'

    @classmethod
    def get_collection(cls):
        db = get_mongo_database(cls.db_key)
        return db[cls.collection_name]

    @classmethod
    def create(cls, data):
        data['created_at'] = datetime.now()
        data['updated_at'] = datetime.now()
        return cls.get_collection().insert_one(data).inserted_id

    @classmethod
    def find_all(cls, filter_dict=None, limit=100):
        if filter_dict is None:
            filter_dict = {}
        return list(cls.get_collection().find(filter_dict).limit(limit))

    @classmethod
    def find_by_id(cls, doc_id):
        if isinstance(doc_id, str):
            doc_id = ObjectId(doc_id)
        return cls.get_collection().find_one({'_id': doc_id})

    @classmethod
    def update(cls, doc_id, data):
        if isinstance(doc_id, str):
            doc_id = ObjectId(doc_id)
        data['updated_at'] = datetime.now()
        return cls.get_collection().update_one({'_id': doc_id}, {'$set': data}).modified_count

    @classmethod
    def delete(cls, doc_id):
        if isinstance(doc_id, str):
            doc_id = ObjectId(doc_id)
        return cls.get_collection().delete_one({'_id': doc_id}).deleted_count

    @classmethod
    def count(cls, filter_dict=None):
        if filter_dict is None:
            filter_dict = {}
        return cls.get_collection().count_documents(filter_dict)


class Article(MongoBaseModel):
    collection_name = 'articles'
    db_key = 'api'


class Contact(MongoBaseModel):
    collection_name = 'contacts'
    db_key = 'api'


class ReseauSocial(MongoBaseModel):
    collection_name = 'reseaux_sociaux'
    db_key = 'social'


class Facture(MongoBaseModel):
    collection_name = 'factures'
    db_key = 'api'


class Message(MongoBaseModel):
    collection_name = 'messages'
    db_key = 'gateway'
