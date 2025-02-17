"""These are views that are used for viewing and editing characters."""

from django.contrib import messages
from django.contrib.auth.mixins import UserPassesTestMixin,\
    LoginRequiredMixin, PermissionRequiredMixin
from django.http import HttpResponseRedirect
from django.urls import reverse, reverse_lazy
from django.views import View
from django.views.generic.edit import FormMixin, CreateView, UpdateView
from django.views.generic import DetailView, ListView, DeleteView

from rest_framework.authentication import SessionAuthentication
from rest_framework.permissions import BasePermission
from rest_framework.response import Response
from rest_framework.views import APIView

from talesofvalor.skills.models import Header, Skill

from .models import Character
from .forms import CharacterForm, CharacterSkillForm


class OwnsCharacter(BasePermission):
    """
    The current user is staff or owns the that is being manipulated.
    """
    message = "You don't own this character"

    def has_object_permission(self, request, view, obj):
        if self.request.user.has_perm('players.view_any_player'):
            return True
        try:
            player = Character.objects.get(pk=self.kwargs['pk']).player
            return (player.user == self.request.user)
        except Character.DoesNotExist:
            return False
        return False


class CharacterCreateView(LoginRequiredMixin, CreateView):
    model = Character
    form_class = CharacterForm

    def get_initial(self):
        # Get the initial dictionary from the superclass method
        initial = super(CharacterCreateView, self).get_initial()
        # Copy the dictionary so we don't accidentally change a mutable dict
        initial = initial.copy()
        # default to getting the player from the query String.
        try:
            initial['player'] = self.request.GET['player']
        except KeyError:
            initial['player'] = self.request.user.player
        # etc...
        return initial

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user  # pass the 'user' in kwargs
        return kwargs

    def get_success_url(self):
        return reverse(
            'characters:character_detail',
            kwargs={'pk': self.object.pk}
        )

    def form_valid(self, form):
        """
        If this form is valid, then add the current player to the character
        if the current user is not an admin
        """
        if not self.request.user.has_perm('players.view_any_player'):
            form.instance.player = self.request.user.player
        return super().form_valid(form)


class CharacterUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = Character
    form_class = CharacterForm

    def test_func(self):
        if self.request.user.has_perm('players.view_any_player'):
            return True
        try:
            player = Character.objects.get(pk=self.kwargs['pk']).player
            return (player.user == self.request.user)
        except Character.DoesNotExist:
            return False
        return False

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user  # pass the 'user' in kwargs
        return kwargs

    def get_success_url(self):
        return reverse(
            'characters:character_detail',
            kwargs={'pk': self.object.pk}
        )


class CharacterDeleteView(
        PermissionRequiredMixin,
        UserPassesTestMixin,
        DeleteView
        ):
    """
    Removes a character permanantly.

    Removing a character may have strange effects on other views.
    """

    model = Character
    permission_required = ('character.can_edit', )
    success_url = reverse_lazy('characters:character_list')

    def test_func(self):
        if self.request.user.has_perm('players.view_any_player'):
            return True
        try:
            player = Character.objects.get(pk=self.kwargs['pk']).player
            return (player.user == self.request.user)
        except Character.DoesNotExist:
            return False
        return False


class CharacterSetActiveView(
        LoginRequiredMixin,
        UserPassesTestMixin,
        View
        ):
    """
    Set the active character for the characters player to the sent id.
    """

    model = Character
    fields = '__all__'

    def test_func(self):
        if self.request.user.has_perm('players.view_any_player'):
            return True
        try:
            player = Character.objects.get(pk=self.kwargs['pk']).player
            return (player.user == self.request.user)
        except Character.DoesNotExist:
            return False
        return False

    def get(self, request, *args, **kwargs):
        """
        Send the user back to the the originating page or back to the
        character they are setting active
        """

        character = self.model.objects.get(pk=self.kwargs['pk'])
        character.player.character_set.update(active_flag=False)
        character.active_flag = True
        character.save()
        messages.info(self.request, 'Active Character changed to {}.'.format(
            character.name
        ))
        return HttpResponseRedirect(
            self.request.META.get(
                'HTTP_REFERER',
                reverse(
                    'characters:character_detail',
                    kwargs={'pk': self.kwargs['pk']}
                )
            )
        )


class CharacterSkillUpdateView(
        LoginRequiredMixin,
        UserPassesTestMixin,
        FormMixin,
        DetailView):
    """
    Allow a user to update their chosen skills
    """

    template_name = 'characters/character_skill_form.html'
    form_class = CharacterSkillForm
    model = Character

    def test_func(self):
        if self.request.user.has_perm('players.view_any_player'):
            return True
        try:
            player = Character.objects.get(pk=self.kwargs['pk']).player
            return (player.user == self.request.user)
        except Character.DoesNotExist:
            return False
        return False

    def get_success_url(self):
        return reverse(
            'characters:character_detail',
            kwargs={'pk': self.object.pk}
        )

    def get_form_kwargs(self):
        kwargs = super(CharacterSkillUpdateView, self).get_form_kwargs()
        self.skills = Header.objects\
            .order_by('hidden_flag', 'category', 'name')\
            .all()
        kwargs.update({'skills': self.skills})
        return kwargs

    def get_context_data(self, **kwargs):
        context = super(CharacterSkillUpdateView, self)\
            .get_context_data(**self.kwargs)
        context['skills'] = self.skills
        """
        skills granted by a specific character grant or as a result of
        of character backgrounds or headers granting skills without the need
        for the player to spend points.
        """
        context['grants'] = self.object.grants
        context['skill_hash'] = self.object.skillhash
        return context

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        form = self.get_form()
        if form.is_valid():
            return self.form_valid(form)
        else:
            return self.form_invalid(form)

    def form_valid(self, form):
        """
        Form is valid.   Save the skills to that character and remove the
        appropriate number of characters points.
        """
        return super(CharacterSkillUpdateView, self).form_valid(form)


'''
Put the AJAX work for Characters here
'''


class CharacterAddHeaderView(APIView):
    '''
    Set of AJAX views for a Characters

    This handles different API calls for character actions.
    '''

    authentication_classes = [SessionAuthentication]
    permission_classes = [OwnsCharacter]

    def post(self, request, format=None):
        header_id = int(request.POST.get('header_id', 0))
        character_id = int(request.POST.get('character_id', 0))
        # get the character and then see if the header is allowed
        header = Header.objects.get(pk=header_id)
        character = Character.objects.get(pk=character_id)
        print("CHARACTER HEADERS:{}".format(character.headers.all()))
        # check that the header is allowed.
        print("HEADER CHECK:{}".format(character.check_header_prerequisites(header)))
        # if the prerequisites are met, add the header to the user and return
        # the list of skills
        if character.check_header_prerequisites(header):
            character.headers.add(header)
        # otherwise, return an error
        content = {
            'success': "testing right now"
        }

        return Response(content)


class CharacterAddSkillView(APIView):
    '''
    Set of AJAX views for a Characters

    This handles different API calls for character actions.
    '''

    authentication_classes = [SessionAuthentication]
    permission_classes = [OwnsCharacter]

    def post(self, request, format=None):
        skill_id = int(request.POST.get('skill_id', 0))
        header_id = int(request.POST.get('header_id', 0))
        character_id = int(request.POST.get('character_id', 0))
        # get the character and then see if the skill is allowed
        skill = Skill.objects.get(pk=skill_id)
        header = Header.objects.get(pk=header_id)
        character = Character.objects.get(pk=character_id)
        print("CHARACTER HEADERS:{}".format(character.headers.all()))
        # check that the skill is allowed.
        print("HEADER CHECK:{}".format(character.check_skill_prerequisites(header)))
        # if the prerequisites are met, add the header to the user and return
        # the list of skills
        # otherwise, return an error
        content = {
            'success': "testing right now"
        }

        return Response(content)

class CharacterDetailView(LoginRequiredMixin, UserPassesTestMixin, DetailView):
    """
    Show the details for a character.

    From here you can edit the details of a character or choose skills.
    """

    model = Character
    fields = '__all__'

    def test_func(self):
        if self.request.user.has_perm('players.view_any_player'):
            return True
        try:
            player = Character.objects.get(pk=self.kwargs['pk']).player
            return (player.user == self.request.user)
        except Character.DoesNotExist:
            return False
        return False


class CharacterListView(LoginRequiredMixin, ListView):
    """
    Show the list of characters.

    From here, you can view, edit, delete a character.
    """

    model = Character
    paginate_by = 25
