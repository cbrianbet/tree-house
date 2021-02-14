from django.conf.urls import url
from django.contrib import admin
from django.urls import path
from . import  views

urlpatterns = [
    path('property/list', views.properties_list, name='prop-list'),
    path('property/add', views.properties_add, name='add-list'),
    path('property/delete/<int:pid>', views.delete_property, name='delete-prop'),
    path('property/payment/<uuid:u_id>', views.properties_payment, name='payment-list'),
    path('property/units/list/<uuid:u_uid>', views.list_units, name='unit-list'),
    path('property/units/view/<uuid:pid>', views.view_unit, name='unit-view'),
    path('property/units/add/<int:floor>/<uuid:u_uid>', views.add_units, name='unit-add'),
    path('property/units/edit/<uuid:u_uid>', views.edit_units, name='unit-edit'),
    path('property/units/tenant/add/<uuid:u_uid>', views.add_tenant, name='tenant-add'),
    path('property/units/tenant/<uuid:u_uid>', views.view_tenant, name='view-tenant'),
    path('property/view/<uuid:p_id>', views.view_prop, name='view-prop'),
    path('property/edit/<uuid:p_id>', views.properties_edit, name='edit-prop'),
    path('property/units/tenant/swap/<uuid:u_uid>', views.swap_tenant, name='swap-tenant'),
    path('property/file/upload', views.prop_file_upload, name='file-prop'),
    path('property/file/template', views.prop_template, name='file-template'),
    path('unit/file/template', views.unit_template, name='unit-template'),
    path('unit/file/upload/<uuid:uid>', views.unit_file_upload, name='unit-file-upload'),
    path('property/tenant/file/upload', views.tenant_file_upload, name='file-tenant'),
    path('staff/', views.staff, name='company_staff'),
    path('staff/edit/<int:uid>', views.edit_staff, name='edit-staff'),
    path('profile/company', views.staff, name='company_profile'),
    path('attach_people/', views.attach_people, name='attach_people'),
    path('vacate/request', views.vacate_tenant_request, name='vacate_request'),
    path('vacate/letter', views.generate_vacate_notice, name='generate-vacate-request'),
    path('vacate/list', views.vacate_list, name='vacate-list'),
    path('inspection/report/<int:id>', views.inspection_report, name='ins-report'),
    path('documnets', views.document, name='documents'),
    path('documnet/lease', views.document_lease, name='document-lease'),
    path('documnet/vacate', views.document_vacate, name='document-vacate'),
    path('documnet/non-comp', views.document_non_comp, name='document-non-comp'),
]
