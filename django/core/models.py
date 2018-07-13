from uuid import uuid4

from django.conf import settings
from django.db import models
from django.db.models.aggregates import Sum


def movie_directory_path_with_uuid(instance, filename):
    # used to generate the uploaded file's name
    return '{}/{}'.format(instance.movie_id, uuid4())


class MovieManager(models.Manager):
    '''
    MovieManager for a movie model.
    '''
    def all_with_related_persons(self):
        '''
        This method prefetches all related objects of Person model.
        (extracts list of directors, writers, actors) 
        Uses select_related() method for director field because this
        field has a one to many relation.
        '''
        qs = self.get_queryset()
        qs = qs.select_related('director')
        qs = qs.prefetch_related('writers', 'actors')
        return qs

    def all_with_related_persons_and_score(self):
        qs = self.all_with_related_persons()
        qs = qs.annotate(score=Sum('vote__value'))
        return qs

    def top_movies(self, limit=10):
        qs = self.get_queryset()
        qs = qs.annotate(vote_sum=Sum('vote__value'))
        qs = qs.exclude(vote_sum=None)
        qs = qs.order_by('-vote_sum')
        qs = qs[:limit]
        return qs


class Movie(models.Model):
    '''
    Model.Movie
    '''
    NOT_RATED = 0
    RATED_G = 1
    RATED_PG = 2
    RATED_R = 3
    RATINGS = (
        (NOT_RATED, 'NR - Not Rated'),
        (RATED_G, 'G - General Audiences'),
        (RATED_PG, 'PG - Parental Guidance Suggested'),
        (RATED_R, 'R - Restricted'),
    )

    title = models.CharField(max_length=140)
    plot = models.TextField()
    year = models.PositiveIntegerField()
    rating = models.IntegerField(choices=RATINGS, default=NOT_RATED)
    runtime = models.PositiveIntegerField()
    website = models.URLField(blank=True)
    director = models.ForeignKey(
        to='Person',
        on_delete=models.SET_NULL,
        related_name='directed',
        null=True,
        blank=True
    )
    writers = models.ManyToManyField(
        to='Person',
        related_name='writing_credits',
        blank=True
    )
    actors = models.ManyToManyField(
        to='Person',
        through='Role',
        related_name='acting_credits',
        blank=True
    )
    objects = MovieManager()

    class Meta:
        ordering = ('-year', 'title')

    def __str__(self):
        return '{} ({})'.format(self.title, self.year)


class MovieImage(models.Model):
    '''
    Model.MovieImage
    '''
    image = models.ImageField(upload_to=movie_directory_path_with_uuid)
    uploaded = models.DateTimeField(auto_now_add=True)
    movie = models.ForeignKey('Movie', on_delete=models.CASCADE)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE
    )


class PersonManager(models.Manager):
    '''
    PersonManager for Person model. Added new method which is uses
        get_queryset() to get a QuerySet and tells it to prefetch the related
        objects of Movie model.
    '''
    def all_with_prefetch_movies(self):
        qs = self.get_queryset()
        return qs.prefetch_related(
            'directed',
            'writing_credits',
            'acting_credits'
        )


class Person(models.Model):

    first_name = models.CharField(max_length=140)
    last_name = models.CharField(max_length=140)
    born = models.DateField()
    died = models.DateField(blank=True, null=True)
    objects = PersonManager()

    class Meta:
        ordering = ('first_name', 'last_name')

    def __str__(self):
        if self.died:
            return '{}, {} ({}-{})'.format(
                self.last_name,
                self.first_name,
                self.born,
                self.died
            )

        return '{}, {} ({})'.format(
            self.last_name,
            self.first_name,
            self.born
        )


class Role(models.Model):
    '''
    Intermediary table for many-to-many relationship between Movie and Person
        models(Movie.actors and Person.acting_credits fields). Requires all
        field to be unique together.
    '''
    movie = models.ForeignKey(Movie, on_delete=models.DO_NOTHING)
    person = models.ForeignKey(Person, on_delete=models.DO_NOTHING)
    name = models.CharField(max_length=140)

    class Meta:
        unique_together = ('movie', 'person', 'name')

    def __str__(self):
        return '{} {} {}'.format(self.movie_id, self.person_id, self.name)


class VoteManager(models.Manager):
    '''
    This manager checks whether a given user has a related Vote model instance
        for a given Movie instance.
    Args:
        movie - int (id for the instance of Movie model)
    '''
    def get_vote_or_unsaved_blank_vote(self, movie, user):
        try:
            return Vote.objects.get(movie=movie, user=user)
        except Vote.DoesNotExist:
            # This model instance won't be saved in DB until create() method
            # is used in a view!
            return Vote(movie=movie, user=user)


class Vote(models.Model):

    UP = 1
    DOWN = -1
    VALUE_CHOICES = (
        (UP, "👍",),
        (DOWN, "👎",),
    )

    value = models.SmallIntegerField(
        choices=VALUE_CHOICES,
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE
    )
    movie = models.ForeignKey(
        Movie,
        on_delete=models.CASCADE
    )
    voted_on = models.DateTimeField(
        auto_now=True
    )
    objects = VoteManager()

    class Meta:
        unique_together = ('user', 'movie')
