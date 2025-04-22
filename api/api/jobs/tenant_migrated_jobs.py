from datetime import timedelta

from api.jobs.common import CustomerServiceDep
from core.domain.events import TenantMigratedEvent, WithDelay

from ..broker import broker


@broker.task(retry_on_error=True)
async def handle_tenant_migrated(event: TenantMigratedEvent, customer_service: CustomerServiceDep):
    await customer_service.handle_customer_migrated(
        from_user_id=event.from_user_id,
        from_anon_id=event.from_anon_id,
    )


@broker.task(retry_on_error=True)
async def send_daily_digest(event: TenantMigratedEvent, customer_service: CustomerServiceDep):
    await customer_service.send_daily_user_digest()


JOBS = [handle_tenant_migrated, WithDelay(send_daily_digest, timedelta(hours=2))]
