"""
Describes the player models.

These models describe the player and its relationship to the
django authentication user models.
"""
from django.contrib.auth.models import User
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils.translation import ugettext as _

from djangocms_text_ckeditor.fields import HTMLField

from talesofvalor.events.models import Event


class Player(models.Model):
    """
    Player of a game.

    An individual who is playing a game.  All users are players
    of some sort.
    """

    user = models.OneToOneField(User, on_delete=models.CASCADE)
    game_started = models.ForeignKey(Event, blank=True, null=True)
    cp_available = models.PositiveIntegerField(default=0)

    def __unicode__(self):
        """General display of model."""
        return "{} {}".format(
            self.user.first_name,
            self.user.last_name
        )

    @property
    def active_character(self):
        """
        The active character of the Player.

        Gets the active character from the list of characters associated with 
        this player.

        TODO:
        if there is more than one character returned here, it should error out (try/except)
        The error should set the player to "needs attention flag"
        There should be a message added to the message queue explaining what happened.
        """
        return self.character_set.get(active_flag=True)

    class Meta:
        """Add permissions."""

        permissions = (
            ("change_any_player", "Can change any player"),
            ("view_any_player", "Can view any player"),
        )



@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    """
    A User has been created.

    When a user is created, we also have to create a profile object and attach
    it to the user.  This uses the 'post_save' signal.
    """
    if created:
        Player.objects.create(user=instance)


@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    """
    A User has been updated.

    When a user has been updated, we have to make sure that the profile
    attached to it has as well.  This uses the 'post_save' signal.
    """
    instance.player.save()


class Registration(models.Model):
    """
    Registration for events.

    Holds the registration for players for a specific event.
    """

    player = models.ForeignKey(Player)
    event = models.ForeignKey(Event)
    cabin = models.CharField(
        max_length=100,
        blank=True,
        default='',
        help_text=_("What cabin is the player staying in?")
    )
    mealplan_flag = models.BooleanField(
        default=False,
        help_text=_("Has the player signed up for a meal plan?")
    )
    notes = models.TextField(blank=True, default='')


class PEL(models.Model):
    """
    (P)ost (E)vent (L)etter.

    Letter and information describing a player's experience at an event.
    """

    RATINGS_CHOICES = (
        (5, 'Amazing'),
        (4, 'Good'),
        (3, 'Average'),
        (2, 'Fair'),
        (1, 'Poor'),
    )

    player = models.ForeignKey(Player)
    event = models.ForeignKey(Event)
    created = models.DateTimeField(
        _('date created'),
        null=True,
        auto_now_add=True,
        editable=False
    )
    modified = models.DateTimeField(
        _('last updated'),
        null=True,
        auto_now=True,
        editable=False
    )
    likes = models.TextField(blank=True, default='')
    dislikes = models.TextField(blank=True, default='')
    best_moments = models.TextField(blank=True, default='')
    worst_moments = models.TextField(blank=True, default='')
    learned = models.TextField(blank=True, default='')
    data = HTMLField(blank=True, default='')
    rating = models.PositiveIntegerField(choices=RATINGS_CHOICES)
