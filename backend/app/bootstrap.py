"""Punto de ensamblaje: conecta contratos con implementaciones externas."""
from application.services.gym_service import GymService
from application.services import membership_notifications, schedule_notifications
from infrastructure.authentication import PasswordService, GoogleIdentityProvider, SignedSessionProvider
from infrastructure.repositories.gym_repository import SupabaseGymRepository
from infrastructure.repositories.membership_notifications import NotificationRepository
from infrastructure.repositories.schedule_notifications import ScheduleNotificationRepository
from infrastructure.services.email_service import ResendEmailService
from infrastructure.services.stripe_service import StripeService
from application.services.identity_service import IdentityService
from application.services.store_images_service import StoreImagesService
from infrastructure.services.local_image_storage import LocalImageStorage
from infrastructure.services.supabase_storage_service import SupabaseStorageService


def create_gym_service(url, key):
    return GymService(
        SupabaseGymRepository(url, key), PasswordService(),
        identity=GoogleIdentityProvider(), sessions=SignedSessionProvider(),
        gateway_factory=StripeService,
    )


def create_identity_service():
    return IdentityService(GoogleIdentityProvider(), SignedSessionProvider())


def create_payment_gateway(settings):
    return StripeService(settings)


def create_store_images_service(settings):
    storage = (SupabaseStorageService(settings.supabase_url, settings.supabase_key, settings.store_images_bucket)
               if settings.has_supabase_credentials else LocalImageStorage(settings.store_images_dir))
    return StoreImagesService(storage)


def create_membership_notifications(settings):
    return membership_notifications.MembershipNotificationService(
        settings, repository=NotificationRepository(settings), sender=ResendEmailService(settings),
    )


def create_schedule_notifications(settings):
    return schedule_notifications.ScheduleNotificationService(
        settings, repository=ScheduleNotificationRepository(settings), sender=ResendEmailService(settings),
    )


def notify_membership(settings, clients_service, saved, event):
    if not getattr(settings, "has_email_credentials", False):
        return {"status": "not_configured", "message": "El servicio de correo todavía no está configurado."}
    return membership_notifications.notify_membership(
        create_membership_notifications(settings), clients_service, saved, event,
    )


def notify_schedule_enrollment(settings, enrollment_id):
    return schedule_notifications.notify_schedule_enrollment(create_schedule_notifications(settings), enrollment_id)


async def process_pending_emails(settings):
    await membership_notifications.process_pending_emails(create_membership_notifications(settings))
