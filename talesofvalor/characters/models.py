"""
Describes the character models.

These models describe a character and its relationship
to players.
"""
from django.contrib.auth.models import User
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ObjectDoesNotExist
from django.db import models
from django.urls import reverse
from django.utils.translation import ugettext as _

from filer.fields.image import FilerImageField

from talesofvalor.players.models import Player
from talesofvalor.rules.models import Prerequisite
from talesofvalor.skills.models import Header, Skill
from talesofvalor.origins.models import Origin


class Character(models.Model):
    """
    Character a player can play.

    Players can have more than one character, but only one can be active at a
    time.
    Staff can have multiple characters who are active at the same time.
    """

    ALIVE = 'alive'
    DEAD = 'dead'
    RETIRED = 'retired'
    STATUS_CHOICES = (
        (ALIVE, 'Alive'),
        (DEAD, 'Dead'),
        (RETIRED, 'Retired'),
    )

    player = models.ForeignKey(Player, on_delete=models.CASCADE)
    status = models.CharField(
        max_length=50,
        choices=STATUS_CHOICES,
        default='alive'
    )
    name = models.CharField(_("Character Name"), max_length=255)
    description = models.TextField(blank=True)
    history = models.TextField(blank=True)
    picture = FilerImageField(blank=True, null=True, on_delete=models.CASCADE)
    player_notes = models.TextField(blank=True)
    staff_notes_visible = models.TextField(blank=True)
    staff_notes_hidden = models.TextField(blank=True)
    staff_attention_flag = models.BooleanField(default=False)
    npc_flag = models.BooleanField(default=False)
    active_flag = models.BooleanField(default=False)
    cp_spent = models.PositiveIntegerField(default=0)
    cp_available = models.PositiveIntegerField(default=0)
    cp_transferred = models.PositiveIntegerField(default=0)
    # The headers and skills that a character has.
    headers = models.ManyToManyField(Header)
    skills = models.ManyToManyField(Skill, through='CharacterSkills')
    # origins.  Should only be as many as there are types.
    origins = models.ManyToManyField(Origin)

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
    created_by = models.ForeignKey(
        User,
        editable=False,
        related_name='%(app_label)s_%(class)s_author',
        null=True,
        on_delete=models.SET_NULL
    )
    modified_by = models.ForeignKey(
        User,
        editable=False,
        related_name='%(app_label)s_%(class)s_updater',
        null=True,
        on_delete=models.SET_NULL
    )

    def get_absolute_url(self):
        return reverse('characters:character_detail', kwargs={'pk': self.pk})

    def __str__(self):
        try:
            return "{}::{}".format(
                self.name, self.player)
        except ObjectDoesNotExist:
            return "{}".format(self.name)

    @property
    def background(self):
        return self.origins.get(type=Origin.BACKGROUND)

    @property
    def race(self):
        return self.origins.get(type=Origin.RACE)

    @property
    def skillhash(self):
        """
        Get the base skill cost hash and update it based on the character
        """
        skillhash = Skill.skillhash()
        # update skillhash with skills the character has.
        print("HEADERS:")
        print(self.headers.all())
        # go throught the hash and figure out what headers have had the
        # prerequisites met . . .
        
        return skillhash

    def grants(self):
        """
        skills granted by a specific character grant or as a result of
        of character backgrounds or headers granting skills without the need
        for the player to spend points.
        """

    def check_header_prerequisites(self, header):
        """
        Does the sent header meet the prerequisites for that header.
        If there are no prerequisites, it meets them.
        """
        try: 
            header_type = ContentType.objects.get_for_model(Header)
            header_prerequisites = Prerequisite.objects.filter(
                content_type__pk=header_type.id,
                object_id=header.id
            )
            # check for origin requirements
            for prereq in header_prerequisites:
                if prereq.origin: 
                    if prereq.origin not in self.origins:
                        return False
                # check for header/skill requirements
                if prereq.header:
                    if prereq.header not in self.headers:
                        return False
                    # check for the number of different skills in the header.
                    purchased_skills = self.skills.filter(headerskill__header_id=prereq.header.id)
                    print(purchased_skills)
                    if prereq.number_of_different_skills > self.skills.filter(headerskill__header_id=prereq.header.id).count(): 
                        return False
                    # figure out the total skill points
                    total = 0
                    for skill in purchased_skills:
                        total += skill.headerskill.cost * skill

                # check for skill requirements
            # if we made it this far, we can assume all prerequisites
            # have been met.
            return True
        except Prerequisite.DoesNotExist:
            return True
        return True

    def check_skill_prerequisites(self, skill, header):
        """
        Does the sent skill meet the prerequisites for that header.
        If there are no prerequisites, it meets them.
        """
        try: 
            skill_type = ContentType.objects.get_for_model(Skill)
            skill_prerequisites = Prerequisite.objects.filter(
                content_type__pk=skill_type.id,
                object_id=skill.id
            )
        except Prerequisite.DoesNotExist:
            return True
        return True

    class Meta:
        ordering = ["name"]


class CharacterSkills(models.Model):
    """
    Links chracters with their skills.

    Indicates what skills a character has and how many of them exist.
    """

    character = models.ForeignKey(Character, on_delete=models.CASCADE)
    skill = models.ForeignKey(Skill, on_delete=models.CASCADE)
    count = models.PositiveIntegerField(null=False, default=1)


class CharacterLog(models.Model):
    """
    Log of changes to character.

    Whenever anyone makes a change to a character, an entry to
    this log should be added so any problems or bad actions can be traced.
    """

    character = models.ForeignKey(Character, on_delete=models.CASCADE)
    message = models.TextField(_("Log Message"))
    created = models.DateTimeField(
        _('date created'),
        auto_now_add=True,
        editable=False
    )
    created_by = models.ForeignKey(
        User,
        editable=False,
        related_name='%(app_label)s_%(class)s_author',
        null=True,
        on_delete=models.SET_NULL
    )


class CharacterGrant(models.Model):
    """
    Tracks special skills and headers granted to a character.

    Some origins or events trigger the granting of headers or skills.
    These do not count against spent character points.

    TODO: I feel like there is a way to do this without grants since the
    system will know what rules have been or should run.

    Grants would then turn into a "special" that could be granted by a
    staff member.
    """

    SKILL_GRANT = 'SkillGrant'
    HEADER_GRANT = 'HeaderGrant'
    TYPE_CHOICES = (
        (SKILL_GRANT, 'Skill Grant'),
        (HEADER_GRANT, 'Header Grant')
    )
    type = models.CharField(
        max_length=20,
        choices=TYPE_CHOICES,
        default='SkillGrant'
    )
    character = models.ForeignKey(Character, on_delete=models.CASCADE)
    correlated_id = models.PositiveIntegerField()
    reason = models.TextField()
    free = models.BooleanField(default=False)
    picks_remaining = models.PositiveIntegerField(default=10000)

