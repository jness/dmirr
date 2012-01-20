
from django.shortcuts import redirect, render
from django.core.urlresolvers import reverse
from django.contrib.auth.decorators import login_required
from dmirr.hub.apps.accounts.forms import GroupForm, AddUserToGroupForm
from dmirr.hub import db
from dmirr.hub.utils import ok, session_is_owner, Http403

def index_view(request):
    if request.user.is_authenticated():
        return redirect('/account/%s/' % request.user.username)
    else:
        return redirect('/account/signin/')
    
def my_projects(request, user):
    data = {}
    print request.user.profile.my_projects
    data['projects'] = request.user.profile.my_projects
    return render(request, 'accounts/projects.html', data)
    
@login_required
def create_group(request):
    data = {}

    if request.method == 'POST':
        post = request.POST.copy()
        post['user'] = request.user
        form = GroupForm(post)
        if form.is_valid():
            group = form.save()
            
            return redirect(reverse('userena_profile_detail',
                                    kwargs=dict(username=request.user.username)))
    else:
        form = GroupForm()
        
    data['form'] = form
    return render(request, 'accounts/groups/create.html', data)
    
login_required
@ok('auth.change_group', (db.Group, 'name', 'group'))
def update_group(request, group):
    data = {}
    group = db.Group.objects.get(name=group)
    
    if request.method == 'POST':
        post = request.POST.copy()
        post['user'] = request.user
        form = GroupForm(post, instance=group)
        if form.is_valid():
            group = form.save()
            
            return redirect(reverse('userena_profile_detail',
                                    kwargs=dict(username=request.user.username)))
    else:
        form = GroupForm(instance=group)
        
    data['form'] = form   
    data['group'] = group 
    return render(request, 'accounts/groups/update.html', data)

login_required
@ok('auth.change_group', (db.Group, 'name', 'group'))
def update_group(request, group):
    data = {}
    group = db.Group.objects.get(name=group)

    if request.method == 'POST':
        post = request.POST.copy()
        post['user'] = request.user
        form = GroupForm(post, instance=group)
        if form.is_valid():
            group = form.save()
            
            return redirect(reverse('show_group', 
                                    kwargs=dict(group=group.name)))
    else:
        form = GroupForm(instance=group)
          
    data['form'] = form
    data['group'] = group 
    return render(request, 'accounts/groups/update.html', data)

@login_required
@ok('auth.change_group', (db.Group, 'name', 'group'))
def add_user_to_group(request, group):
    data = {}
    group = db.Group.objects.get(name=group)    
    
    if request.method == 'POST':
        user = db.User.objects.get(pk=request.POST['user'])
        group.user_set.add(user)
        group.save()
        return redirect(reverse('show_group', kwargs=dict(group=group.name)))
        
    else:
        form = AddUserToGroupForm()
        data['form'] = form
        data['group'] = group 
        return render(request, 'accounts/groups/add.html', data)

@login_required
@ok('auth.change_group', (db.Group, 'name', 'group'))
def remove_user_from_group(request, group):
    data = {}
    group = db.Group.objects.get(name=group)    
    user = db.User.objects.get(username=request.GET['user'])

    group.user_set.remove(user)
    group.save()
    return redirect(reverse('show_group', kwargs=dict(group=group.name)))

        
def show_group(request, group):
    data = {}
    data['group'] = db.Group.objects.get(name=group)
    return render(request, 'accounts/groups/show.html', data)

@login_required
@ok('auth.delete_group', (db.Group, 'name', 'group'))
def delete_group(request, group):
    data = {}
    group = db.Group.objects.get(name=group)
    group.delete()
    return redirect(reverse('userena_profile_detail',
                            kwargs=dict(username=request.user.username)))
    