import uuid as u_id

from django.db import models

from authapp.models import Users, Profile, Subscriptions


class Companies(models.Model):
    uuid = models.UUIDField(default=u_id.uuid4, editable=False, unique=True)
    name = models.CharField(max_length=50, null=True, blank=True)
    no_of_emp = models.PositiveIntegerField(default=1)
    location = models.CharField(max_length=40, blank=True, null=True)
    logo = models.ImageField(upload_to='logo/%Y/%m/', null=True, blank=True)

    class Meta:
        db_table = "Companies"


class CompanyProfile(models.Model):
    uuid = models.UUIDField(default=u_id.uuid4, editable=False, unique=True)
    company = models.ForeignKey(Companies, on_delete=models.CASCADE)
    user = models.ForeignKey(Users, on_delete=models.CASCADE)

    class Meta:
        db_table = "Company_Profile"


class Properties(models.Model):
    uuid = models.UUIDField(default=u_id.uuid4, editable=False, unique=True)
    property_name = models.CharField(max_length=50)
    owner = models.CharField(max_length=50, null=True, blank=True)
    property_type = models.CharField(max_length=50)
    building_type = models.CharField(max_length=50, null=True, blank=True)
    property_value = models.CharField(max_length=20, null=True, blank=True)
    mngmt_start = models.DateField(blank=True, null=True)
    no_of_units = models.PositiveIntegerField(default=1)
    no_of_floors = models.PositiveIntegerField(default=1)
    parking = models.PositiveIntegerField(default=0)
    electricity = models.CharField(max_length=20)
    water = models.CharField(max_length=20)
    pics = models.ImageField(upload_to='propPic/%Y/%m/', null=True, blank=True)
    long = models.DecimalField(max_digits=19, decimal_places=6, null=True)
    lat = models.DecimalField(max_digits=19, decimal_places=6, null=True)
    rent_collection = models.CharField(max_length=50, default="Spec_date")
    specific_day = models.CharField(max_length=5, blank=True, null=True)
    penalty_type = models.CharField(max_length=50, default="percent")
    penalty_value = models.CharField(max_length=50, default="20")
    location_desc = models.CharField(max_length=50, null=True)
    company = models.ForeignKey(Companies, on_delete=models.CASCADE)
    created_by = models.ForeignKey(Users, on_delete=models.CASCADE, related_name="p_created_by")
    updated_by = models.ForeignKey(Users, on_delete=models.CASCADE, related_name="p_updated_by", null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "Properties"

    def delete(self, *args, **kwargs):
        self.pics.delete()
        super().delete(*args, **kwargs)


class PaymentAccount(models.Model):
    uuid = models.UUIDField(default=u_id.uuid4, editable=False, unique=True)
    payment_mode = models.CharField(max_length=30)
    prop = models.ForeignKey(Properties, on_delete=models.CASCADE)
    created_by = models.ForeignKey(Users, on_delete=models.CASCADE, related_name="p_m_created_by")
    updated_by = models.ForeignKey(Users, on_delete=models.CASCADE, related_name="p_m_updated_by", null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "Payment Account"


class PaymentPaybill(models.Model):
    uuid = models.UUIDField(default=u_id.uuid4, editable=False, unique=True)
    acc = models.CharField(max_length=30)
    paybill = models.CharField(max_length=30)
    prop = models.ForeignKey(PaymentAccount, on_delete=models.CASCADE)

    class Meta:
        db_table = "Payment Paybill"


class PaymentTill(models.Model):
    uuid = models.UUIDField(default=u_id.uuid4, editable=False, unique=True)
    till = models.CharField(max_length=30)
    prop = models.ForeignKey(PaymentAccount, on_delete=models.CASCADE)

    class Meta:
        db_table = "Payment Till"


class Banks(models.Model):
    bank = models.CharField(max_length=60)

    class Meta:
        db_table = "Banks"


class BankAcc(models.Model):
    uuid = models.UUIDField(default=u_id.uuid4, editable=False, unique=True)
    acc = models.CharField(max_length=130)
    bank = models.ForeignKey(Banks, on_delete=models.CASCADE)
    prop = models.ForeignKey(PaymentAccount, on_delete=models.CASCADE)

    class Meta:
        db_table = "Bank Account"


class Unit(models.Model):
    uuid = models.UUIDField(default=u_id.uuid4, editable=False, unique=True)
    unit_name = models.CharField(max_length=40)
    type_of_unit = models.CharField(max_length=40, null=True, blank=True)
    value = models.CharField(max_length=40)
    unit_status = models.CharField(max_length=40, default='Vacant')
    area = models.CharField(max_length=40, null=True, blank=True)
    service_charge = models.CharField(max_length=40, default="0")
    parking_assigned = models.PositiveIntegerField(default=0)
    property = models.ForeignKey(Properties, on_delete=models.CASCADE)
    floor = models.PositiveIntegerField()
    other_specify = models.CharField(max_length=30, null=True, blank=True)
    size = models.CharField(max_length=30, null=True, blank=True)
    security_deposit = models.CharField(max_length=20, default=0)
    discount_type = models.CharField(max_length=20, null=True, blank=True)
    amount = models.DecimalField(max_digits=6, decimal_places=2, default=0.00)
    created_by = models.ForeignKey(Users, on_delete=models.CASCADE, related_name="u_created_by")
    updated_by = models.ForeignKey(Users, on_delete=models.CASCADE, related_name="u_updated_by", null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "Units"


class Tenant(models.Model):
    uuid = models.UUIDField(default=u_id.uuid4, editable=False, unique=True)
    profile = models.ForeignKey(Profile, on_delete=models.CASCADE)
    secondary_msisdn = models.CharField(max_length=40)
    date_occupied = models.DateTimeField()
    unit = models.ForeignKey(Unit, on_delete=models.CASCADE, null=True)
    discount = models.DecimalField(max_digits=19, decimal_places=2, null=True)
    discount_type = models.CharField(max_length=40, default="None")
    id_card = models.FileField(upload_to='ID/%Y/%m/')
    created_by = models.ForeignKey(Users, on_delete=models.CASCADE, related_name="t_created_by")
    updated_by = models.ForeignKey(Users, on_delete=models.CASCADE, related_name="t_updated_by", null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    accept_terms = models.BooleanField(default=False)

    class Meta:
        db_table = "Tenant"


class PropertyStaff(models.Model):
    user = models.ForeignKey(Users, on_delete=models.CASCADE)
    property = models.ForeignKey(Properties, on_delete=models.CASCADE)
    created_by = models.ForeignKey(Users, on_delete=models.CASCADE, related_name="ps_created_by")
    updated_by = models.ForeignKey(Users, on_delete=models.CASCADE, related_name="ps_updated_by", null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


class SubscriptionsCompanies(models.Model):
    company = models.ForeignKey(Companies, on_delete=models.CASCADE)
    subs = models.ForeignKey(Subscriptions, on_delete=models.CASCADE, null=True)
    date_started = models.DateField(null=True)
    date_end = models.DateField(null=True)

    class Meta:
        db_table = "Subscription_Company"


class TransactionCodes(models.Model):
    trx = models.CharField(max_length=20)
    created_by = models.ForeignKey(Users, on_delete=models.CASCADE, related_name="trx_created_by", null=True)
    updated_by = models.ForeignKey(Users, on_delete=models.CASCADE, related_name="trx_updated_by", null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "Trans codes"


class PeopleAttached(models.Model):
    uuid = models.UUIDField(default=u_id.uuid4, editable=False, unique=True)
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE)
    f_name = models.CharField(max_length=140)
    l_name = models.CharField(max_length=40, null=True, blank=True)
    relationship = models.CharField(max_length=140)
    mobile_number = models.CharField(max_length=40, null=True, blank=True)
    created_by = models.ForeignKey(Users, on_delete=models.CASCADE, related_name="pa_created_by")
    updated_by = models.ForeignKey(Users, on_delete=models.CASCADE, related_name="pa_updated_by", null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "People Attached"


class VacateNotice(models.Model):
    notice_from = models.ForeignKey(Tenant, on_delete=models.CASCADE)
    vacate_date = models.DateField()
    unit = models.ForeignKey(Unit, on_delete=models.CASCADE)
    reason = models.CharField(null=True, max_length=90)
    new_contacts = models.CharField(max_length=15, blank=True)
    days_notice = models.PositiveIntegerField(default=20)
    created_by = models.ForeignKey(Users, on_delete=models.CASCADE, related_name="vn_created_by")
    updated_by = models.ForeignKey(Users, on_delete=models.CASCADE, related_name="vn_updated_by", null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    status = models.BooleanField(default=False)

    class Meta:
        db_table = "Vacate Notice"


class InspectionReport(models.Model):
    faults = models.CharField(max_length=500)
    charges = models.CharField(max_length=16)
    notice = models.ForeignKey(VacateNotice, on_delete=models.CASCADE)
    created_by = models.ForeignKey(Users, on_delete=models.CASCADE, related_name="ir_created_by")
    updated_by = models.ForeignKey(Users, on_delete=models.CASCADE, related_name="ir_updated_by", null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "Inspection Report"


class NonCompliance(models.Model):
    violation = models.CharField(max_length=500)
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE)
    unit = models.ForeignKey(Unit, on_delete=models.CASCADE)
    created_by = models.ForeignKey(Users, on_delete=models.CASCADE, related_name="comp_created_by")
    updated_by = models.ForeignKey(Users, on_delete=models.CASCADE, related_name="comp_updated_by", null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "Non Compliance"


class TenantHistory(models.Model):
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE)
    curr_unit = models.ForeignKey(Unit, on_delete=models.CASCADE)
    start_date = models.DateField()
    end_date = models.DateField(null=True, blank=True)

    class Meta:
        db_table = "Tenant History"
