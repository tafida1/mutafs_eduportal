from django.db import models
from django.utils import timezone
from django.utils.text import slugify
from django.conf import settings




class School(models.Model):
    class SubscriptionStatus(models.TextChoices):
        TRIAL = "TRIAL", "Trial"
        ACTIVE = "ACTIVE", "Active"
        EXPIRED = "EXPIRED", "Expired"
        SUSPENDED = "SUSPENDED", "Suspended"

    name = models.CharField(max_length=255)
    slug = models.SlugField(max_length=255, unique=True, db_index=True)

    portal_subpath = models.SlugField(
        max_length=255,
        unique=True,
        help_text="Public portal path, e.g. berachah-school",
    )

    code = models.CharField(max_length=50, unique=True, db_index=True)

    email = models.EmailField(blank=True)
    phone = models.CharField(max_length=30, blank=True)
    address = models.TextField(blank=True)

    logo = models.ImageField(upload_to="school_logos/", blank=True, null=True)

    result_stamp = models.ImageField(
        upload_to="school_stamps/",
        blank=True,
        null=True,
    )

    is_active = models.BooleanField(default=True)
    is_verified = models.BooleanField(default=False)

    subscription_status = models.CharField(
        max_length=20,
        choices=SubscriptionStatus.choices,
        default=SubscriptionStatus.TRIAL,
        db_index=True,
    )
    subscription_start_date = models.DateField(null=True, blank=True)
    subscription_end_date = models.DateField(null=True, blank=True)

    result_checker_enabled = models.BooleanField(default=True)
    cbt_enabled = models.BooleanField(default=True)
    finance_enabled = models.BooleanField(default=True)
    parent_portal_enabled = models.BooleanField(default=True)

    custom_domain = models.CharField(
        max_length=255,
        blank=True,
        db_index=True,
        help_text="Example: schoolname.com",
    )

    subdomain = models.SlugField(
        max_length=100,
        blank=True,
        db_index=True,
        help_text="Example: brightstar",
    )

    primary_color = models.CharField(
        max_length=20,
        default="#2563eb",
    )

    secondary_color = models.CharField(
        max_length=20,
        default="#0f172a",
    )

    accent_color = models.CharField(
        max_length=20,
        default="#22c55e",
    )

    maintenance_mode = models.BooleanField(default=False)

    maintenance_message = models.TextField(
        blank=True,
        default="This school portal is temporarily under maintenance.",
    )

    storage_limit_mb = models.PositiveIntegerField(default=500)

    allow_custom_branding = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["name"]
        indexes = [
            models.Index(fields=["slug"]),
            models.Index(fields=["portal_subpath"]),
            models.Index(fields=["subscription_status"]),
            models.Index(fields=["is_active"]),
        ]

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)

        if not self.portal_subpath:
            self.portal_subpath = self.slug

        if not self.code:
            base_code = slugify(self.name).replace("-", "").upper()[:8]
            self.code = base_code or "SCHOOL"

        super().save(*args, **kwargs)

    @property
    def is_subscription_expired(self):
        if not self.subscription_end_date:
            return False
        return timezone.localdate() > self.subscription_end_date

    @property
    def days_remaining(self):
        if not self.subscription_end_date:
            return None
        delta = self.subscription_end_date - timezone.localdate()
        return max(delta.days, 0)

    def can_use_premium_features(self):
        return (
            self.is_active
            and self.subscription_status in [
                self.SubscriptionStatus.TRIAL,
                self.SubscriptionStatus.ACTIVE,
            ]
            and not self.is_subscription_expired
        )





class SubscriptionPlan(models.Model):
    class BillingCycle(models.TextChoices):
        MONTHLY = "MONTHLY", "Monthly"
        TERMLY = "TERMLY", "Termly"
        YEARLY = "YEARLY", "Yearly"

    name = models.CharField(max_length=120, unique=True)
    description = models.TextField(blank=True)

    billing_cycle = models.CharField(
        max_length=20,
        choices=BillingCycle.choices,
        default=BillingCycle.MONTHLY,
    )

    price = models.DecimalField(max_digits=12, decimal_places=2)

    max_students = models.PositiveIntegerField(default=500)
    max_staff = models.PositiveIntegerField(default=100)

    cbt_enabled = models.BooleanField(default=True)
    finance_enabled = models.BooleanField(default=True)
    parent_portal_enabled = models.BooleanField(default=True)
    result_checker_enabled = models.BooleanField(default=True)

    is_active = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["price", "name"]

    def __str__(self):
        return self.name


class SchoolSubscription(models.Model):
    class Status(models.TextChoices):
        TRIAL = "TRIAL", "Trial"
        ACTIVE = "ACTIVE", "Active"
        EXPIRED = "EXPIRED", "Expired"
        SUSPENDED = "SUSPENDED", "Suspended"
        CANCELLED = "CANCELLED", "Cancelled"

    school = models.OneToOneField(
        School,
        on_delete=models.CASCADE,
        related_name="subscription",
    )

    plan = models.ForeignKey(
        SubscriptionPlan,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="school_subscriptions",
    )

    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.TRIAL,
    )

    start_date = models.DateField(default=timezone.localdate)
    end_date = models.DateField(null=True, blank=True)

    auto_disable_on_expiry = models.BooleanField(default=True)

    notes = models.TextField(blank=True)

    updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="updated_school_subscriptions",
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["end_date", "school__name"]

    def __str__(self):
        return f"{self.school.name} - {self.get_status_display()}"

    @property
    def is_expired(self):
        if self.end_date:
            return timezone.localdate() > self.end_date
        return False

    @property
    def days_remaining(self):
        if not self.end_date:
            return None
        return (self.end_date - timezone.localdate()).days

    def sync_school_status(self):
        if self.is_expired:
            self.status = self.Status.EXPIRED

            if self.auto_disable_on_expiry:
                self.school.subscription_status = School.SubscriptionStatus.EXPIRED
                self.school.is_active = False
                self.school.save(update_fields=["subscription_status", "is_active", "updated_at"])

            self.save(update_fields=["status", "updated_at"])

        else:
            self.school.subscription_status = self.status
            self.school.save(update_fields=["subscription_status", "updated_at"])


class SubscriptionPayment(models.Model):
    class Method(models.TextChoices):
        CASH = "CASH", "Cash"
        TRANSFER = "TRANSFER", "Bank Transfer"
        POS = "POS", "POS"
        ONLINE = "ONLINE", "Online"

    subscription = models.ForeignKey(
        SchoolSubscription,
        on_delete=models.CASCADE,
        related_name="payments",
    )

    amount = models.DecimalField(max_digits=12, decimal_places=2)
    payment_method = models.CharField(max_length=20, choices=Method.choices)
    reference = models.CharField(max_length=255, blank=True)

    payment_date = models.DateTimeField(default=timezone.now)
    received_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )

    note = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-payment_date"]

    def __str__(self):
        return f"{self.subscription.school.name} - {self.amount}"