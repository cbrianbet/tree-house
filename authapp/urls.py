from django.conf.urls import url
from django.contrib import admin
from django.urls import path
from . import  views

urlpatterns = [
    path('', views.about, name='about'),
    path('wallet', views.wall_bal, name='hapo_wallet'),
    path('wallet/r_trans', views.hapokash_wallet_transfer, name='hapo_wallet_trans'),
    path('wallet/trans_inv', views.hapokash_wallet_transfer_Inv, name='hapo_wallet_transinv'),
    path('wallet/confirm/trans', views.confirm_payment, name='confirm-trans'),
    path('login/', views.login, name='web-login'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('profile/', views.profile, name='profile'),
    path('checkusername/', views.check_username, name='check-username'),
    path('change_password/', views.change_password, name='change_password'),
    path('signup/', views.signup, name='register'),
    path('suspend/<int:uid>', views.suspend_user, name='suspend_user'),
    path('delete/<int:uid>', views.delete_user, name='delete_user'),
    path('suspend/comp/<int:uid>', views.suspend_company, name='suspend_comp'),
    path('delete/comp/<int:uid>', views.delete_company, name='delete_comp'),
    path('logout/', views.logout_request, name='logout'),

]
