from django.contrib.auth.decorators import login_required
from django.shortcuts import render

# Create your views here.
from authapp.models import Users


@login_required
def all_users(request):
    all_users = Users.objects.all()

    context = {
        'user': request.user,
        'list': all_users,
    }
    return render(request, 'reports/all_users.html', context)
