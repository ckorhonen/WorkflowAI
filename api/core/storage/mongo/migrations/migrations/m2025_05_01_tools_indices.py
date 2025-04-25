from core.storage.mongo.migrations.base import AbstractMigration


class AddToolsIndicesMigration(AbstractMigration):
    """Add necessary indices to the tools collection"""

    @property
    def _tools_collection(self):
        return self.storage._tools_collection  # pyright: ignore [reportPrivateUsage]

    async def apply(self):
        # Unique composite index on tenant and name fields
        await self._tools_collection.create_index(
            [
                ("tenant", 1),
                ("name", 1),
            ],
            name="tools_tenant_name_unique",
            unique=True,
            background=True,
        )

    async def rollback(self):
        await self._drop_index_if_exists(self._tools_collection, "tools_tenant_name_unique")
