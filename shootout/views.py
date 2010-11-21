try:
    import hashlib
    sha1 = hashlib.sha1
except ImportError:
    import sha
    sha1 = sha.new
import os
import math
import urllib

import webob
import formencode
from webob.exc import HTTPFound
from webob.exc import HTTPUnauthorized

from sqlalchemy.sql import func

from pyramid.renderers import render_to_response
from pyramid.renderers import render
from pyramid.security import authenticated_userid
from pyramid.view import static

from shootout.models import DBSession
from shootout.models import User
from shootout.models import Idea
from shootout.models import Tag
from shootout.models import IdeaTag

resources = os.path.join(
    os.path.abspath(os.path.dirname(__file__)), 'resources')
static_view = static(resources)

COOKIE_VOTED = 'shootout.voted'

def idea_bunch(order_by, how_many=10):
    session = DBSession()
    return session.query(Idea).join('users').filter(
        Idea.target==None).order_by(order_by).all()[:how_many]

def main_view(context, request):
    params = request.params
    message = params.get('message','')
    hitpct = idea_bunch(Idea.hit_percentage.desc(), 10)
    top = idea_bunch(Idea.hits.desc(), 10)
    bottom = idea_bunch(Idea.misses.desc(), 10)
    last10 = idea_bunch(Idea.idea_id.desc(), 10)
    toplists=[
        {'title':'Latest shots','items':last10},
        {'title':'Most hits','items':top},
        {'title':'Most misses','items':bottom},
        {'title':'Best performance','items':hitpct},
        ]
    login_form = login_form_view(context,request)
    return render_to_response(
        'templates/main.pt',
        dict(
            username = authenticated_userid(request),
            app_url=request.application_url,
            message=message,
            toolbar=toolbar_view(context,request),
            cloud=cloud_view(context,request),
            latest=latest_view(context,request),
            login_form=login_form,
            toplists=toplists
            ),
        request,
        )

def idea_vote(context, request):
    app_url = request.application_url
    response = webob.Response()
    params = request.params
    target = params.get('target')
    session = DBSession()
    idea = session.query(Idea).filter(Idea.idea_id==target).one()
    voter_username = authenticated_userid(request)
    voter = session.query(User).filter(User.username==voter_username).one()
    poster = session.query(User).filter(User.user_id==idea.author).one()
    if params.get('form.vote_hit'):
        vote='hit'
        idea.hits=idea.hits+1
        poster.hits=poster.hits+1
        voter.delivered_hits=voter.delivered_hits+1
    if params.get('form.vote_miss'):
        vote='miss'
        idea.misses=idea.misses+1
        poster.misses=poster.misses+1
        voter.delivered_misses=voter.delivered_misses+1
    cookie = "%s.%s.%s" % (COOKIE_VOTED,idea.idea_id,voter_username)
    response.set_cookie(cookie.encode('utf-8'), vote)
    session.flush()
    url = "%s/ideas/%s" % (app_url,idea.idea_id)
    response.status = '301 Moved Permanently'
    response.headers['Location'] = url
    return response

class AddIdea(formencode.Schema):
    allow_extra_fields = True
    title = formencode.validators.String(not_empty=True)
    text = formencode.validators.String(not_empty=True)
    tags = formencode.validators.String(not_empty=True)

def idea_add(context, request):
    app_url = request.application_url
    params = request.params
    message = params.get('message','')
    session = DBSession()
    if params.get('form.submitted'):
        target = params.get('target', None)
        title = params.get('title')
        text = params.get('text')
        tags = params.get('tags')
        schema = AddIdea()
        try:
            schema.to_python(params)
        except formencode.validators.Invalid, why:
            message=urllib.quote(str(why))
            url = "%s/idea_add?message=%s" % (app_url,message)
        else:
            author_id = authenticated_userid(request)
            author = session.query(User).filter(
                User.username==author_id).one().user_id
            idea = Idea(target=target, author=author, title=title, text=text)
            session.add(idea)
            tags = tags.replace(';',' ').replace(',',' ')
            tags = [tag.lower() for tag in tags.split()]
            tags = set(tags)
            if '' in tags:
                tags.remove('')
            for tagname in tags:
                existent = session.query(Tag).filter(Tag.name==tagname).all()
                if not existent:
                    tag = Tag(name=tagname)
                    session.add(tag)
                    idea.tags.append(tag)
                else:
                    idea.tags.append(existent[0])
            url = "%s/ideas/%s" % (app_url, idea.idea_id)
        return HTTPFound(location=url)
    target = params.get('target', None)
    kind = 'idea'
    if target is not None:
        target = session.query(Idea).join('users').filter(
            Idea.idea_id==target).one()
        kind = 'comment'
    login_form = login_form_view(context,request)
    return render_to_response(
        'templates/idea_add.pt',
        dict(
            app_url=app_url,
            message=message,
            toolbar=toolbar_view(context,request),
            cloud=cloud_view(context,request),
            latest=latest_view(context,request),
            login_form=login_form,
            target=target,
            kind=kind,
            request=request,
            ),
        request,
        )

class Registration(formencode.Schema):
    allow_extra_fields = True
    username = formencode.validators.PlainText(not_empty=True)
    password = formencode.validators.PlainText(not_empty=True)
    email = formencode.validators.Email(resolve_domain=False)
    name = formencode.validators.String(not_empty=True)
    password = formencode.validators.String(not_empty=True)
    confirm_password = formencode.validators.String(not_empty=True)
    chained_validators = [
        formencode.validators.FieldsMatch('password','confirm_password')]

def user_add(context, request):
    app_url = request.application_url
    params = request.params
    message = params.get('message','')
    if params.get('form.submitted'):
        headers = []
        username = params.get('username', None)
        password = params.get('password', None)
        name = params.get('name', None)
        email = params.get('email', None)
        schema = Registration()
        session = DBSession()
        try:
            schema.to_python(params)
        except formencode.validators.Invalid, why:
            message=urllib.quote(str(why))
            url = "%s/register?message=%s" % (app_url, message)
        else:
            password='{SHA}%s' % sha1(password).hexdigest()
            user = User(username=username, password=password, name=name,
                        email=email)
            session.add(user)
            # try to autolog the user in
            plugins = request.environ.get('repoze.who.plugins', {})
            identifier = plugins.get('auth_tkt')
            if identifier:
                identity = {'repoze.who.userid': username}
                headers = identifier.remember(request.environ, identity)
            request.environ['repoze.who.userid'] = username
            url = "%s?message=%s" % (app_url,message)
        return HTTPFound(location=url, headers=headers)

    login_form = login_form_view(context, request)

    return render_to_response(
        'templates/user_add.pt',
        dict(
            message=message,
            toolbar=toolbar_view(context,request),
            cloud=cloud_view(context,request),
            latest=latest_view(context,request),
            login_form=login_form,
            app_url=app_url,
            ),
        request,
        )

def user_view(context, request):
    app_url = request.application_url
    session = DBSession()
    user = session.query(User).filter(User.username==context.user).one()
    login_form = login_form_view(context, request)
    return render_to_response(
        'templates/user.pt',
        dict(
            user=user,
            toolbar=toolbar_view(context,request),
            cloud=cloud_view(context,request),
            latest=latest_view(context,request),
            login_form=login_form,
            app_url=app_url,
            ),
        request,
        )

def idea_view(context, request):
    session = DBSession()
    idea = session.query(Idea).filter(Idea.idea_id==context.idea).one()
    poster = session.query(User).filter(User.user_id==idea.author).one()
    viewer_username = authenticated_userid(request)
    idea_cookie = '%s.%s.%s' % (COOKIE_VOTED,idea.idea_id,viewer_username)
    voted = request.cookies.get(idea_cookie, None)
    comments = session.query(Idea).filter(Idea.target==context.idea).all()
    login_form = login_form_view(context, request)
    return render_to_response(
        'templates/idea.pt',
        dict(
            app_url=request.application_url,
            toolbar=toolbar_view(context,request),
            cloud=cloud_view(context,request),
            latest=latest_view(context,request),
            login_form=login_form,
            poster=poster,
            voted=voted,
            comments=comments,
            viewer_username=viewer_username,
            idea=idea,
            ),
        request,
        )

def tag_view(context, request):
    session = DBSession()
    ideas = session.query(Idea).filter(Idea.tags.any(name=context.tag)).all()
    login_form = login_form_view(context, request)
    return render_to_response(
        'templates/tag.pt',
        dict(
            tag=context.tag,
            app_url=request.application_url,
            toolbar=toolbar_view(context,request),
            cloud=cloud_view(context,request),
            latest=latest_view(context,request),
            login_form=login_form,
            ideas=ideas,
            ),
        request,
        )

def about_view(context, request):
    login_form = login_form_view(context, request)
    return render_to_response(
        'templates/about.pt',
        dict(
            app_url=request.application_url,
            toolbar=toolbar_view(context,request),
            cloud=cloud_view(context,request),
            latest=latest_view(context,request),
            login_form=login_form,
            ),
        request,
        )

def logout_view(context, request):
    # the Location in the headers tells the form challenger to redirect
    return HTTPUnauthorized(headers=[('Location', request.application_url)])

def login_view(context, request):
    return main_view(context, request)

def toolbar_view(context, request):
    viewer_username = authenticated_userid(request)
    return render(
        'templates/toolbar.pt',
        dict(
            app_url=request.application_url,
            viewer_username=viewer_username,
            ),
        request,
        )

def login_form_view(context, request):
    loggedin = authenticated_userid(request)
    return render(
        'templates/login.pt',
        dict(
            app_url=request.application_url,
            loggedin=loggedin,
            ),
        request,
        )

def latest_view(context, request):
    latest = idea_bunch(Idea.idea_id.desc(), 10)
    return render(
        'templates/latest.pt',
        dict(
            app_url=request.application_url,
            latest=latest,
            ),
        request,
        )

def cloud_view(context, request):
    session = DBSession()
    tag_counts = session.query(
        Tag.name, func.count('*')).join(IdeaTag).group_by(Tag.name).all()
    totalcounts = []
    for tag in tag_counts:
        weight = int((math.log(tag[1] or 1) * 4) + 10)
        totalcounts.append((tag[0], tag[1],weight))
    cloud = sorted(totalcounts, cmp=lambda x,y: cmp(x[0], y[0]))
    return render(
        'templates/cloud.pt',
        dict(
            app_url=request.application_url,
            cloud=cloud
            ),
        request,
        )

