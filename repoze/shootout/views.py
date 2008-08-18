import sha

import webob
import formencode
from webob.exc import HTTPFound

from repoze.bfg.template import render_template_to_response, render_template
from repoze.bfg.security import authenticated_userid

from repoze.shootout.models import DBSession
from repoze.shootout.models import User, Idea, Tag

COOKIE_VOTED = 'repoze.shootout.voted'

def main_view(context, request):
    params = request.params
    message = params.get('message','')
    hitpct = DBSession.query(Idea).join('users').filter(Idea.target==None).order_by(Idea.hit_percentage.desc()).all()[:10]
    top = DBSession.query(Idea).join('users').filter(Idea.target==None).order_by(Idea.hits.desc()).all()[:10]
    bottom = DBSession.query(Idea).join('users').filter(Idea.target==None).order_by(Idea.misses.desc()).all()[:10]
    last10 = DBSession.query(Idea).join('users').filter(Idea.target==None).order_by(Idea.idea_id.desc()).all()[:10]
    toplists=[
              {'title':'Latest shots','items':last10},
              {'title':'Most hits','items':top},
              {'title':'Most misses','items':bottom},
              {'title':'Best performance','items':hitpct},
             ]
    return render_template_to_response('templates/main.pt',
                                       app_url=request.application_url,
                                       message=message,
                                       toolbar=toolbar_view(context,request),
                                       toplists=toplists)

def idea_vote(context, request):
    app_url = request.application_url
    response = webob.Response()
    params = request.params
    target = params.get('target')
    idea = DBSession.query(Idea).filter(Idea.idea_id==target).one()
    voter_username = authenticated_userid(request)
    voter = DBSession.query(User).filter(User.username==voter_username).one()
    poster = DBSession.query(User).filter(User.user_id==idea.author).one()
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
    response.set_cookie("%s.%s.%s" % (COOKIE_VOTED,idea.idea_id,voter_username), vote)
    DBSession.flush()
    DBSession.commit()
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
            author = DBSession.query(User).filter(User.username==author_id).one().user_id
            idea = Idea(target=target, author=author, title=title, text=text)
            tags = tags.replace(';',' ').replace(',',' ')
            tags = [tag.lower() for tag in tags.split()]
            tags = set(tags)
            if '' in tags:
                tags.remove('')
            for tagname in tags:
                existent = DBSession.query(Tag).filter(Tag.name==tagname).all()
                if not existent:
                    tag = Tag(name=tagname)
                    idea.tags.append(tag)
                else:
                    idea.tags.append(existent[0])
            DBSession.commit()
            url = "%s/ideas/%s" % (app_url,idea.idea_id)
        return HTTPFound(location=url)
    target = params.get('target', None)
    kind = 'idea'
    if target is not None:
        target = DBSession.query(Idea).join('users').filter(Idea.idea_id==target).one()
        kind = 'comment'
    return render_template_to_response('templates/idea_add.pt',
                                       app_url=app_url,
                                       message=message,
                                       toolbar=toolbar_view(context,request),
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
        username = params.get('username', None)
        password = params.get('password', None)
        name = params.get('name', None)
        email = params.get('email', None)
        schema = Registration()
        try:
            form = schema.to_python(params)
        except formencode.validators.Invalid, why:
            message=str(why)
            url = "%s/register?message=%s" % (app_url,message)
        else:
            password='{SHA}%s' % sha.new(password).hexdigest()
            user = User(username=username, password=password, name=name, email=email)
            DBSession.save(user)
            DBSession.commit()
            url = "%s?message=%s" % (app_url,message)
        return HTTPFound(location=url)
    return render_template_to_response('templates/user_add.pt',
                                       message=message,
                                       toolbar=toolbar_view(context,request),
                                       app_url=app_url)

def user_view(context, request):
    app_url = request.application_url
    user = DBSession.query(User).filter(User.username==context.user).one()
    return render_template_to_response('templates/user.pt',
                                       user=user,
                                       toolbar=toolbar_view(context,request),
                                       app_url=app_url)

def idea_view(context, request):
    idea = DBSession.query(Idea).filter(Idea.idea_id==context.idea).one()
    poster = DBSession.query(User).filter(User.user_id==idea.author).one()
    viewer_username = authenticated_userid(request)
    idea_cookie = '%s.%s.%s' % (COOKIE_VOTED,idea.idea_id,viewer_username)
    voted = request.cookies.get(idea_cookie, None)
    comments = DBSession.query(Idea).filter(Idea.target==context.idea).all()
    return render_template_to_response('templates/idea.pt',
                                       app_url=request.application_url,
                                       toolbar=toolbar_view(context,request),
                                       poster=poster,
                                       voted=voted,
                                       comments=comments,
                                       viewer_username=viewer_username,
                                       idea=idea)

def tag_view(context, request):
    ideas = DBSession.query(Idea).filter(Idea.tags.any(name=context.tag)).all()
    return render_template_to_response('templates/tag.pt',
                                       tag=context.tag,
                                       app_url=request.application_url,
                                       toolbar=toolbar_view(context,request),
                                       ideas=ideas)

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

