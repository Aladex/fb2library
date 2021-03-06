from django.conf.urls import patterns,  url
from views import *

urlpatterns = patterns(
    '/book',
    # url(r'^$', 'book.views.library', name='recent'),
    url(r'letters/', letters, name="letters"),
    url(r'genres/', genres, name="genres"),
    url(r'sequences/', sequences, name="sequences"),
    url(r'authors/(?P<letter>\w)$', author_letter, name='author_letter'),
    url(r'author/(?P<author_id>\d+)/$', author_books, name='author_books'),
    url(r'genre/(?P<genre_id>\d+)/$', genre_books, name='genre_books'),
    url(r'(?P<book_id>\d+)/$', book_details, name='book_details'),
)
