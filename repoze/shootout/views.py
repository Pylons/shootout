import sha
import os
import math

import webob
import formencode
from webob.exc import HTTPFound

from paste import urlparser

from sqlalchemy.sql import func

from repoze.bfg.wsgi import wsgiapp
from repoze.bfg.template import render_template_to_response, render_template
from repoze.bfg.security import authenticated_userid

from repoze.shootout.models import DBSession
from repoze.shootout.models import User, Idea, Tag, IdeaTag

here = os.path.abspath(os.path.dirname(__file__))
static = urlparser.StaticURLParser(os.path.join(here, 'resources', '..'))

COOKIE_VOTED = 'repoze.shootout.voted'

def main_view(context, request):
    params = request.params
    message = params.get('message','')
    session = DBSession()
    hitpct = session.query(Idea).join('users').filter(Idea.target==None).order_by(Idea.hit_percentage.desc()).all()[:10]
    top = session.query(Idea).join('users').filter(Idea.target==None).order_by(Idea.hits.desc()).all()[:10]
    bottom = session.query(Idea).join('users').filter(Idea.target==None).order_by(Idea.misses.desc()).all()[:10]
    last10 = session.query(Idea).join('users').filter(Idea.target==None).order_by(Idea.idea_id.desc()).all()[:10]
    toplists=[
              {'title':'Latest shots','items':last10},
              {'title':'Most hits','items':top},
              {'title':'Most misses','items':bottom},
              {'title':'Best performance','items':hitpct},
             ]
    return render_template_to_response('templates/main.pt',
                                       username = authenticated_userid(request),
                                       app_url=request.application_url,
                                       message=message,
                                       toolbar=toolbar_view(context,request),
                                       cloud=cloud_view(context,request),
                                       latest=latest_view(context,request),
                                       login_form=login_form_view(context,request),
                                       toplists=toplists)

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
            form = schema.to_python(params)
        except formencode.validators.Invalid, why:
            message=str(why)
            url = "%s/idea_add?message=%s" % (app_url,message)
        else:
            author_id = authenticated_userid(request)
            author = session.query(User).filter(User.username==author_id).one().user_id
            idea = Idea(target=target, author=author, title=title, text=text)
            session.save(idea)
            tags = tags.replace(';',' ').replace(',',' ')
            tags = [tag.lower() for tag in tags.split()]
            tags = set(tags)
            if '' in tags:
                tags.remove('')
            for tagname in tags:
                existent = session.query(Tag).filter(Tag.name==tagname).all()
                if not existent:
                    tag = Tag(name=tagname)
                    session.save(tag)
                    idea.tags.append(tag)
                else:
                    idea.tags.append(existent[0])
            url = "%s/ideas/%s" % (app_url,idea.idea_id)
        return HTTPFound(location=url)
    target = params.get('target', None)
    kind = 'idea'
    if target is not None:
        session = DBSession()
        target = session.query(Idea).join('users').filter(Idea.idea_id==target).one()
        kind = 'comment'
    return render_template_to_response('templates/idea_add.pt',
                                       app_url=app_url,
                                       message=message,
                                       toolbar=toolbar_view(context,request),
                                       cloud=cloud_view(context,request),
                                       latest=latest_view(context,request),
                                       login_form=login_form_view(context,request),
                                       target=target,
                                       kind=kind,
                                       request=request)

class Registration(formencode.Schema):
    allow_extra_fields = True
    username = formencode.validators.PlainText(not_empty=True)
    password = formencode.validators.PlainText(not_empty=True)
    email = formencode.validators.Email(resolve_domain=False)
    name = formencode.validators.String(not_empty=True)
    password = formencode.validators.String(not_empty=True)
    confirm_password = formencode.validators.String(not_empty=True)
    chained_validators = [formencode.validators.FieldsMatch('password','confirm_password')]

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
            form = schema.to_python(params)
        except formencode.validators.Invalid, why:
            message=str(why)
            url = "%s/register?message=%s" % (app_url,message)
        else:
            password='{SHA}%s' % sha.new(password).hexdigest()
            user = User(username=username, password=password, name=name, email=email)
            session.save(user)
            # try to autolog the user in
            plugins = request.environ.get('repoze.who.plugins', {})
            identifier = plugins.get('auth_tkt')
            if identifier:
                identity = {'repoze.who.userid': username}
                headers = identifier.remember(request.environ, identity)
            request.environ['repoze.who.userid'] = username
            url = "%s?message=%s" % (app_url,message)
        return HTTPFound(location=url, headers=headers)

    return render_template_to_response('templates/user_add.pt',
                                       message=message,
                                       toolbar=toolbar_view(context,request),
                                       cloud=cloud_view(context,request),
                                       latest=latest_view(context,request),
                                       login_form=login_form_view(context,request),
                                       app_url=app_url)

def user_view(context, request):
    app_url = request.application_url
    session = DBSession()
    user = session.query(User).filter(User.username==context.user).one()
    return render_template_to_response('templates/user.pt',
                                       user=user,
                                       toolbar=toolbar_view(context,request),
                                       cloud=cloud_view(context,request),
                                       latest=latest_view(context,request),
                                       login_form=login_form_view(context,request),
                                       app_url=app_url)

def idea_view(context, request):
    session = DBSession()
    idea = session.query(Idea).filter(Idea.idea_id==context.idea).one()
    poster = session.query(User).filter(User.user_id==idea.author).one()
    viewer_username = authenticated_userid(request)
    idea_cookie = '%s.%s.%s' % (COOKIE_VOTED,idea.idea_id,viewer_username)
    voted = request.cookies.get(idea_cookie, None)
    comments = session.query(Idea).filter(Idea.target==context.idea).all()
    return render_template_to_response('templates/idea.pt',
                                       app_url=request.application_url,
                                       toolbar=toolbar_view(context,request),
                                       cloud=cloud_view(context,request),
                                       latest=latest_view(context,request),
                                       login_form=login_form_view(context,request),
                                       poster=poster,
                                       voted=voted,
                                       comments=comments,
                                       viewer_username=viewer_username,
                                       idea=idea)

def tag_view(context, request):
    session = DBSession()
    ideas = session.query(Idea).filter(Idea.tags.any(name=context.tag)).all()
    return render_template_to_response('templates/tag.pt',
                                       tag=context.tag,
                                       app_url=request.application_url,
                                       toolbar=toolbar_view(context,request),
                                       cloud=cloud_view(context,request),
                                       latest=latest_view(context,request),
                                       login_form=login_form_view(context,request),
                                       ideas=ideas)

def about_view(context, request):
    return render_template_to_response('templates/about.pt',
                                       app_url=request.application_url,
                                       toolbar=toolbar_view(context,request),
                                       cloud=cloud_view(context,request),
                                       latest=latest_view(context,request),
                                       login_form=login_form_view(context,request))

def logout_view(context, request):
    response = webob.Response()
    response.status = '401 Unauthorized'
    return response

def login_view(context, request):
    return main_view(context, request)

def toolbar_view(context, request):
    viewer_username = authenticated_userid(request)
    return render_template('templates/toolbar.pt',
                           app_url=request.application_url,
                           viewer_username=viewer_username)

def login_form_view(context, request):
    loggedin = authenticated_userid(request)
    return render_template('templates/login.pt',
                           app_url=request.application_url,
                           loggedin=loggedin)

def latest_view(context, request):
    session = DBSession()
    latest = session.query(Idea).join('users').filter(Idea.target==None).order_by(Idea.idea_id.desc()).all()[:10]
    return render_template('templates/latest.pt',
                           app_url=request.application_url,
                           latest=latest)

def cloud_view(context, request):
    session = DBSession()
    tag_counts = session.query(Tag.name, func.count('*')).join(IdeaTag).group_by(Tag.name).all()
    total = sum([tag[1] for tag in tag_counts])
    totalcounts = []
    for tag in tag_counts:
        weight = int((math.log(tag[1] or 1) * 4) + 10)
        totalcounts.append((tag[0], tag[1],weight))
    cloud = sorted(totalcounts, cmp=lambda x,y: cmp(x[0], y[0]))
    return render_template('templates/cloud.pt',
                           app_url=request.application_url,
                           cloud=cloud)

@wsgiapp
def static_view(environ, start_response):
    return static(environ, start_response)

