import math
from operator import itemgetter

import formencode

from pyramid.view import view_config
from pyramid.renderers import render_to_response, render
from pyramid.httpexceptions import HTTPMovedPermanently, HTTPFound, HTTPNotFound
from pyramid.security import authenticated_userid, remember, forget

from shootout.models import DBSession
from shootout.models import User, Idea, Tag


@view_config(permission='view', route_name='main',
             renderer='templates/main.pt')
def main_view(request):
    hitpct = Idea.ideas_bunch(Idea.hit_percentage.desc())
    top = Idea.ideas_bunch(Idea.hits.desc())
    bottom = Idea.ideas_bunch(Idea.misses.desc())
    last10 = Idea.ideas_bunch(Idea.idea_id.desc())
    
    toplists = [
        {'title': 'Latest shots', 'items': last10},
        {'title': 'Most hits', 'items': top},
        {'title': 'Most misses', 'items': bottom},
        {'title': 'Best performance', 'items': hitpct},
    ]

    login_form = login_form_view(request)
    
    return {
        'username': authenticated_userid(request),
        'toolbar': toolbar_view(request),
        'cloud': cloud_view(request),
        'latest': latest_view(request),
        'login_form': login_form,
        'toplists': toplists,
    }


@view_config(permission='post', route_name='idea_vote')
def idea_vote(request):
    params = request.params
    target = params.get('target')
    session = DBSession()

    idea = Idea.get_by_id(target)
    voter_username = authenticated_userid(request)
    voter = User.get_by_username(voter_username)

    if params.get('form.vote_hit'):
        vote = 'hit'
        idea.hits += 1
        idea.author.hits += 1
        voter.delivered_hits += 1

    elif params.get('form.vote_miss'):
        vote = 'miss'
        idea.misses += 1
        idea.author.misses += 1
        voter.delivered_misses += 1

    idea.voted_users.append(voter)

    session.flush()

    redirect_url = request.route_url('idea', idea_id=idea.idea_id)
    response = HTTPMovedPermanently(location=redirect_url)

    return response


class Registration(formencode.Schema):
    allow_extra_fields = True
    username = formencode.validators.PlainText(not_empty=True)
    password = formencode.validators.PlainText(not_empty=True)
    email = formencode.validators.Email(resolve_domain=False)
    name = formencode.validators.String(not_empty=True)
    password = formencode.validators.String(not_empty=True)
    confirm_password = formencode.validators.String(not_empty=True)
    chained_validators = [
        formencode.validators.FieldsMatch('password','confirm_password')
    ]


@view_config(permission='view', route_name='register',
             renderer='templates/user_add.pt')
def user_add(request):
    params = request.params
    if 'form.submitted' in params:
        headers = []
        username = params.get('username', None)
        password = params.get('password', None)
        name = params.get('name', None)
        email = params.get('email', None)

        schema = Registration()
        try:
            schema.to_python(params)
        except formencode.validators.Invalid, why:
            why = str(why).splitlines()
            for i in why:
                request.session.flash(i)
            url = request.route_url('register')
        else:
            session = DBSession()
            user = User(username=username, password=password, name=name,
                        email=email)
            session.add(user)
            headers = remember(request, username)
            url = request.route_url('main')
        return HTTPFound(location=url, headers=headers)

    login_form = login_form_view(request)

    return {
        'toolbar': toolbar_view(request),
        'cloud': cloud_view(request),
        'latest': latest_view(request),
        'login_form': login_form,
    }


class AddIdea(formencode.Schema):
    allow_extra_fields = True
    title = formencode.validators.String(not_empty=True)
    text = formencode.validators.String(not_empty=True)
    tags = formencode.validators.String(not_empty=True)


@view_config(permission='post', route_name='idea_add',
             renderer='templates/idea_add.pt')
def idea_add(request):
    params = request.params
    target = params.get('target')
    session = DBSession()

    if target:
        target = Idea.get_by_id(target)
        if not target:
            return HTTPNotFound()
        kind = 'comment'
    else:
        kind = 'idea'

    if params.get('form.submitted'):
        title = params.get('title')
        text = params.get('text')
        tags_string = params.get('tags')
        schema = AddIdea()
        try:
            schema.to_python(params)
        except formencode.validators.Invalid, why:
            request.session.flash(message)
        else:
            author_username = authenticated_userid(request)
            author = User.get_by_username(author_username)
            idea = Idea(target=target, author=author, title=title, text=text)
            tags = Tag.create_tags(tags_string)
            if tags:
                idea.tags = tags
            session.add(idea)            
            redirect_url = request.route_url('idea', idea_id=idea.idea_id)

        return HTTPFound(location=redirect_url)

    login_form = login_form_view(request)

    return {
        'toolbar': toolbar_view(request),
        'cloud': cloud_view(request),
        'latest': latest_view(request),
        'login_form': login_form,
        'target': target,
        'kind': kind,
    }

@view_config(permission='view', route_name='user',
             renderer='templates/user.pt')
def user_view(request):
    username = request.matchdict['username']
    user = User.get_by_username(username)
    login_form = login_form_view(request)
    return {
        'user': user,
        'toolbar': toolbar_view(request),
        'cloud': cloud_view(request),
        'latest': latest_view(request),
        'login_form' :login_form,
    }


@view_config(permission='view', route_name='idea',
             renderer='templates/idea.pt')
def idea_view(request):
    idea_id = request.matchdict['idea_id']
    idea = Idea.get_by_id(idea_id)

    viewer_username = authenticated_userid(request)
    voted = idea.user_voted(viewer_username)
    login_form = login_form_view(request)

    return {
        'toolbar': toolbar_view(request),
        'cloud': cloud_view(request),
        'latest': latest_view(request),
        'login_form': login_form,
        'voted': voted,
        'viewer_username': viewer_username,
        'idea': idea,
    }


@view_config(permission='view', route_name='tag',
             renderer='templates/tag.pt')
def tag_view(request):
    tagname = request.matchdict['tag_name']
    ideas = Idea.get_by_tagname(tagname)
    login_form = login_form_view(request)
    return {
        'tag': tagname,
        'app_url': request.application_url,
        'toolbar': toolbar_view(request),
        'cloud': cloud_view(request),
        'latest': latest_view(request),
        'login_form': login_form,
        'ideas': ideas,
    }


@view_config(permission='view', route_name='about',
             renderer='templates/about.pt')
def about_view(context, request):
    return {
        'toolbar': toolbar_view(request),
        'cloud': cloud_view(request),
        'latest': latest_view(request),
        'login_form': login_form_view(request),
    }


@view_config(permission='view', route_name='login')
def login_view(request):
    main_view = request.route_url('main')
    came_from = request.params.get('came_from', main_view)

    params = request.params
    if 'submit' in params:
        login = params['login']
        password = params['password']

        if User.check_password(login, password):
            headers = remember(request, login)
            request.session.flash('Logged in successfully.')
            return HTTPFound(location=came_from, headers=headers)
    
    request.session.flash('Failed to login.')
    return HTTPFound(location=came_from)


@view_config(permission='post', route_name='logout')
def logout_view(request):
    request.session.invalidate()
    request.session.flash('Logged out successfully.')
    headers = forget(request)
    return HTTPFound(location=request.route_url('main'),
                     headers=headers)


def toolbar_view(request):
    viewer_username = authenticated_userid(request)
    return render(
        'templates/toolbar.pt',
        {'viewer_username': viewer_username}, 
        request
    )


def login_form_view(request):
    logged_in = authenticated_userid(request)
    return render('templates/login.pt', {'loggedin': logged_in}, request)


def latest_view(request):
    latest = Idea.ideas_bunch(Idea.idea_id.desc())
    return render('templates/latest.pt', {'latest': latest}, request)

def cloud_view(request):
    totalcounts = []
    for tag in Tag.tag_counts():
        weight = int((math.log(tag[1] or 1) * 4) + 10)
        totalcounts.append((tag[0], tag[1], weight))
    cloud = sorted(totalcounts, key=itemgetter(0))

    return render('templates/cloud.pt', {'cloud': cloud}, request)

